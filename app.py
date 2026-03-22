import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np

## Título da página,layout
st.set_page_config(page_title="Indicadores financeiros de empresas pela SEC",layout="wide")

CIK_list = ["0000080424","0001666700","0001751788","0000310158","0000034088",
            "0000078003","0000037996","0001467858","0000068505",
            "0000018230","0000030625","0000104169","0001048911","0000200406",
            "0001637459","0000315189","0000040545","0000012927","0000051143",
            "0001571996","0000789019","0001318605"]

#listas de nomes alternativos que alguns conceitos contábeis podem assumir
revenue_tags = [
'RevenueFromContractWithCustomerExcludingAssessedTax',
'SalesRevenueNet',
'Revenues'
]

net_income_tags = [
'NetIncomeLoss',
'ProfitLoss',
'NetIncomeLossAvailableToCommonStockholdersBasic',
'NetIncomeLossAttributableToParent'
]

inventory_tags = [
    'InventoryNet'
]

operating_tags = [
'OperatingIncomeLoss',
'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'
]

deprec_tags = [
'DepreciationDepletionAndAmortization',
'DepreciationAndAmortization',
'Depreciation',
'AmortizationOfIntangibleAssets',
'DepreciationAmortizationAndAccretionNet'
]

profit_tags = [
'GrossProfit',
'GrossProfitLoss'
]

cogs_tags = [
    'CostOfGoodsAndServicesSold',
    'CostOfGoodsSold',
    'CostOfServices',
    'CostOfRevenue'    
]

interest_tags = [
    'InterestExpense',
    'InterestExpenseDebt',
    'InterestIncomeExpenseNet'
]

tax_tags = [
    'IncomeTaxExpenseBenefit',
    'IncomeTaxExpenseBenefitContinuingOperations'
]

opex_tags = [ 'OperatingExpenses',
            ]

sga_tags = ['SellingGeneralAndAdministrativeExpenses']
rd_tags = ['ResearchAndDevelopmentExpense']
ooe_tags = ['OtherOperatingExpenses']
incometax_tags = ['IncomeTaxExpenseBenefit']
pretax_tags = [
    'IncomeLossFromContinuingOperationsBeforeIncomeTaxes',
    'IncomeBeforeIncomeTaxes',
    'PretaxIncome',
    'IncomeLossBeforeIncomeTaxes',
    'EarningsBeforeIncomeTaxes'
]
short_term_tags = ['ShortTermBorrowings']
long_term_tags = ['LongTermDebt']
equity_tags = ['StockholdersEquity']
cash_tags = [
    'CashAndCashEquivalentsAtCarryingValue',
    'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents',
    'Cash'
]

assets_tags = [
    'Assets'
]

current_liabilities_tags = [
    'LiabilitiesCurrent',
    'CurrentLiabilities'
]

def fetch_cik_data(cik, headers):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return cik, {"entityName": response.json().get("entityName"),
                    "facts": {
                        "us-gaap": response.json().get("facts", {}).get("us-gaap", {})
                    }
                    }
    except Exception as e:
        return cik, None

@st.cache_data(ttl=86400)
def download_companyfacts_parallel(CIK_list):
    headers = {"User-Agent": "henriquecuryboar hcboaro@gmail.com"}
    company_data = {}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(lambda cik: fetch_cik_data(cik, headers), CIK_list)
    
    for cik, data in results:
        company_data[cik] = data
    return company_data

company_data = download_companyfacts_parallel(CIK_list)

for cik, data in company_data.items():
    if data is None:
        continue

    entity_name = data['entityName']
    us_gaap = data['facts']['us-gaap']


@st.cache_data(ttl=3600, max_entries=10)
def df_completo(demonstracao, metric_name, entity_name):

    if demonstracao is None or len(demonstracao) == 0:
        return None

    cols_necessarias = ["end", "val", "fp", "form", "filed", "start"]
    df = pd.DataFrame(demonstracao)[[c for c in cols_necessarias if c in demonstracao[0]]]

    # filtra apenas FY e 10-K
    df = df[(df["fp"] == "FY") & (df["form"] == "10-K")]

    if df.empty:
        return None

    # converte datas uma única vez
    df["end"] = pd.to_datetime(df["end"])

    if "start" in df.columns:

        df["start"] = pd.to_datetime(df["start"])

        df["interval"] = (df["end"] - df["start"]).dt.days

        df = df[df["interval"] > 300]

    df["entity"] = entity_name
    df["year"] = df["end"].dt.year

    df = (
        df.sort_values("filed")
        .drop_duplicates("year", keep="last")
    )

    df = df.rename(columns={"val": metric_name})

    return df[["entity", "year", metric_name]]

#Função generalizadora:
@st.cache_data(ttl=3600, max_entries=10)
def data_consolidada(atributo,tag_list):
    dfs_organisations = []
    for cik,data in company_data.items():
        if data is None:
            continue
                
        entity_name = data['entityName']
        us_gaap = data['facts']['us-gaap']
        us_gaap = {
                    k: v for k, v in data['facts']['us-gaap'].items()
                    if k in tag_list
                }

        dfs = []
        for tag in tag_list:
            if tag in us_gaap:
                tag_data = us_gaap[tag]['units'].get('USD')
                if tag_data:
                    df_metric = df_completo(tag_data, tag, entity_name)
                    if df_metric is not None:
                        dfs.append(df_metric)

        if not dfs:
            continue

        if len(dfs) == 1:
            df_atributo = dfs[0]
        else:
            df_atributo = (
            pd.concat(
                [df.set_index(['entity','year']) for df in dfs],
                axis=1
            )
            .reset_index()
        )

        existing_cols = [c for c in tag_list if c in df_atributo.columns]

        df_atributo[atributo] = (
            df_atributo[existing_cols]
            .bfill(axis=1)
            .iloc[:, 0]
        )

        df_atributo['entity'] = entity_name
        df_atributo = df_atributo[['entity','year',atributo]]
        
        df_atributo = (
            df_atributo
            .groupby(['entity','year'], as_index=False)
            .agg({atributo: 'max'})
        )

        dfs_organisations.append(df_atributo)

        
    data_geral = pd.concat(dfs_organisations, ignore_index=True)

    return data_geral

@st.cache_data(ttl=3600, max_entries=10)
def variavel_agreg_periodo(empresa,variavel,inicio,fim):

    filtro_temporal = df_atributo_unificado[(df_atributo_unificado['entity'] == empresa) & (df_atributo_unificado['year'] >= inicio) & 
                                            (df_atributo_unificado['year'] <= fim)]
    filtro_temporal = filtro_temporal[variavel]

    return round(filtro_temporal.sum(skipna=True),2)

@st.cache_data(ttl=3600, max_entries=10)
def variavel_media(empresa,variavel,inicio,fim):

    filtro_temporal = df_atributo_unificado[(df_atributo_unificado['entity'] == empresa) & (df_atributo_unificado['year'] >= inicio) & 
                                            (df_atributo_unificado['year'] <= fim)]
    filtro_temporal = filtro_temporal[variavel]

    return round(filtro_temporal.mean(skipna=True),2)

@st.cache_data(ttl=3600, max_entries=10)
def atributo_anual_plotbar(empresa,atributo,texto_atributo):

    data_empresa = df_atributo_unificado[(df_atributo_unificado['entity'] == empresa) & (df_atributo_unificado['year'] >= 2008) & 
                                            (df_atributo_unificado['year'] <= 2026)]

    if data_empresa.empty:
        st.info("Selecione dados no menu de navegação ao lado para que indicadores sejam exibidos")
        return None

    # max_value = max(data_empresa[atributo])
    fig = px.line(data_empresa, x='year',y=atributo, labels={'year':'ano'})
    
    fig.update_layout(yaxis=dict(title=f'{texto_atributo} por ano fiscal', tickformat=",.2f"), title_text=f'Valores anuais de {texto_atributo}')

    return fig


#lista com todos atributos para junção em df unificado
dfs_atributos_consolidados = []

metricas_pt = {
    'Receita': 'Revenue',
    'Lucro operacional': 'OperatingIncome',
    'Lucro líquido': 'NetIncome',
    'Depreciação e amortização': 'DepreciationAmortization',
    'Lucro bruto': 'CalcProfit',
    'COGS': 'COGS',
    'Juros': 'Interest',
    'Impostos': 'Taxes',
    'Estoque': 'Inventory',
    'Despesas operacionais': 'Opex',
    'Investimento em P&D': 'RnD',
    'Margem EBITDA': 'EBITDAMargin',
    'Margem de lucro líquido': 'NetIncomeMargin',
    'Margem de lucro operacional': 'OperatingIncomeMargin',
    'Margem de lucro bruto': 'GrossMargin',
    'EBITDA':'EBITDA',
    'ROIC':'ROIC',
    'EVA':'EVA',
    'WACC':'WACC'
}


metricas = {
    'Revenue': revenue_tags,
    'OperatingIncome': operating_tags,
    'NetIncome': net_income_tags,
    'DepreciationAmortization': deprec_tags,
    'GrossProfit': profit_tags,
    'COGS': cogs_tags,
    'Interest': interest_tags,
    'Taxes': tax_tags,
    'Inventory': inventory_tags,
    'Opex': opex_tags,
    'RnD': rd_tags,
    'IncomeTax': incometax_tags,
    'ShortTermDebt': short_term_tags,
    'LongTermDebt': long_term_tags,
    'Equity': equity_tags,
    'Cash': cash_tags,
    'Assets': assets_tags,
    'CurrentLiabilities': current_liabilities_tags

}

for atributo,tags in metricas.items():
    df = data_consolidada(atributo,tags)
    dfs_atributos_consolidados.append(df)

df_atributo_unificado = (
    pd.concat(
        [df.set_index(['entity','year']) for df in dfs_atributos_consolidados],
        axis=1
    )
    .reset_index()
)

df_atributo_unificado = df_atributo_unificado.astype({
    col: 'float32'
    for col in df_atributo_unificado.select_dtypes('float').columns
})

#criação de colunas com métricas calculadas indiretamente
df_atributo_unificado['CalcProfit'] = round((df_atributo_unificado['Revenue'] - df_atributo_unificado['COGS']),2)
df_atributo_unificado['EBITDA'] = round((df_atributo_unificado['NetIncome'].fillna(0)+df_atributo_unificado['Interest'].fillna(0)+df_atributo_unificado['Taxes'].fillna(0)+df_atributo_unificado['DepreciationAmortization'].fillna(0)),2)
df_atributo_unificado['PreTax'] = df_atributo_unificado['NetIncome'] + abs(df_atributo_unificado['IncomeTax'])
df_atributo_unificado['TaxRate'] = (abs(df_atributo_unificado['IncomeTax']))/df_atributo_unificado['PreTax']
df_atributo_unificado['NOPAT'] = df_atributo_unificado['OperatingIncome']*(1 - df_atributo_unificado['TaxRate'])
df_atributo_unificado['ROIC'] = df_atributo_unificado['NOPAT']/(df_atributo_unificado['Assets'] - df_atributo_unificado['Cash'] - df_atributo_unificado['CurrentLiabilities'])

#Criação de atribuitos e tratativa de NaN para calcular WACC e EVA
df_atributo_unificado['E_D'] = (df_atributo_unificado['Equity']/(df_atributo_unificado['ShortTermDebt']+df_atributo_unificado['LongTermDebt']+df_atributo_unificado['Equity']))
weight_equity = df_atributo_unificado['E_D'].median()
df_atributo_unificado['E_D'] = df_atributo_unificado['E_D'].where(
    df_atributo_unificado['E_D'] > 0,
    weight_equity
)

df_atributo_unificado['Cost_of_Equity'] = 0.08
df_atributo_unificado['Rd'] = df_atributo_unificado['Interest']/(df_atributo_unificado['ShortTermDebt'] + df_atributo_unificado['LongTermDebt'])
df_atributo_unificado['Rd'] = df_atributo_unificado['Rd'].where(
    df_atributo_unificado['Rd'] > 0,
    0.05
)

df_atributo_unificado['TaxRate'] = df_atributo_unificado['TaxRate'].where(
    ((df_atributo_unificado['TaxRate'] >= 0) & (df_atributo_unificado['TaxRate'] < 1)),
    0.25
)

df_atributo_unificado['WACC'] = df_atributo_unificado['E_D']*df_atributo_unificado['Cost_of_Equity'] + df_atributo_unificado['E_D']*df_atributo_unificado['Rd']*(1 - df_atributo_unificado['TaxRate'])
df_atributo_unificado['EVA'] = (df_atributo_unificado['ROIC'] - df_atributo_unificado['WACC'])*(df_atributo_unificado['Assets'] - df_atributo_unificado['Cash'] - df_atributo_unificado['CurrentLiabilities'])

#Criação de colunas com margens
df_atributo_unificado['EBITDAMargin'] = round(100*(df_atributo_unificado['EBITDA']/df_atributo_unificado['Revenue']),2)

df_atributo_unificado['GrossMargin'] = round(100*(
    df_atributo_unificado['GrossProfit']
        .combine_first(df_atributo_unificado['CalcProfit'])
        .div(df_atributo_unificado['Revenue'])
),2)
df_atributo_unificado['NetIncomeMargin'] = round(100*(df_atributo_unificado['NetIncome']/df_atributo_unificado['Revenue']),2)
df_atributo_unificado['OperatingIncomeMargin'] = round(100*(df_atributo_unificado['OperatingIncome']/df_atributo_unificado['Revenue']),2)

#formatação dos dados e DataFrame
df_atributo_unificado = df_atributo_unificado.sort_values(by=['entity','year'])
df_atributo_unificado['entity'] = df_atributo_unificado['entity'].str.title()

num_cols = df_atributo_unificado.select_dtypes(include = ['number']).columns
numeric_features = num_cols.tolist()
df_atributo_unificado[numeric_features] = df_atributo_unificado[numeric_features].astype('float64')

#geração de lista de empresas
companies_list = df_atributo_unificado['entity'].unique().tolist()



def main():

    st.write('## Painel de informações financeiras de empresas listadas nos EUA')
    st.write('### Selecione dados no menu de navegação à esquerda. Caso nenhum valor seja exibido, isso significa que não há dados disponíveis para os filtros aplicados')
    st.write('#### Fonte dos dados: Securities and Exchange Commission - SEC') 
    empresa_escolhida = st.sidebar.selectbox('Escolha a empresa',sorted(companies_list), index=None, placeholder='Empresas', key=f'empresa')
    inicio = st.sidebar.selectbox('### Início da série', list(range(2008,2026)))
    fim = st.sidebar.selectbox('### Fim da série', list(range(2008,2026)))
    agg_revenue = round(variavel_agreg_periodo(empresa_escolhida,'Revenue',inicio,fim)/1E9,2)
    agg_GrossProfit = round(variavel_agreg_periodo(empresa_escolhida,'CalcProfit',inicio,fim)/1E9,2)
    agg_OpIncome = round(variavel_agreg_periodo(empresa_escolhida,'OperatingIncome',inicio,fim)/1E9,2)
    agg_EBITDA = round(variavel_agreg_periodo(empresa_escolhida,'EBITDA',inicio,fim)/1E9,2)
    agg_NetIncome = round(variavel_agreg_periodo(empresa_escolhida,'NetIncome',inicio,fim)/1E9,2)

    media_margem_lucrobruto = round(variavel_media(empresa_escolhida,'GrossMargin',inicio,fim),2)
    media_margem_operacional = round(variavel_media(empresa_escolhida,'OperatingIncomeMargin',inicio,fim),2)
    media_margem_ebitda = round(variavel_media(empresa_escolhida,'EBITDAMargin',inicio,fim),2)
    media_margem_lucroliquido = round(variavel_media(empresa_escolhida,'NetIncomeMargin',inicio,fim),2)

    col1,col2 = st.columns(2)
    with col1.container(border=True):

        st.markdown(
            """
            <style>
            .centered-text {
                text-align: center;
                font-size: 28px;
            }
            </style>
            <div class="centered-text">
                Indicadores acumulados<br>
            </div>
            """,
            unsafe_allow_html=True
        )


        a,b = st.columns(2)
        c,d = st.columns(2)
        if (pd.isna(agg_revenue) or agg_revenue == 0):
            a.metric(label=f'Receita (em bilhões)', value=f' - ', border=True)
        else:
            a.metric(label=f'Receita (em bilhões)', value=f'US${agg_revenue}', border=True)
        if (pd.isna(agg_GrossProfit) or agg_revenue == 0):
            b.metric(label=f'Lucro bruto (em bilhões)', value=f' - ', border=True)
        else:
            b.metric(label=f'Lucro bruto (em bilhões)', value=f'US${agg_GrossProfit}', border=True)
        if (pd.isna(agg_OpIncome) or agg_revenue == 0):
            c.metric(label=f'Lucro operacional (em bilhões)', value=f' - ', border=True)
        else:
            c.metric(label=f'Lucro operacional (em bilhões)', value=f'US${agg_OpIncome}', border=True)
        if (pd.isna(agg_EBITDA) or agg_revenue == 0):
            d.metric(label=f'EBITDA (em bilhões)', value=f' - ', border=True)
        else:
            d.metric(label=f'EBITDA (em bilhões)', value=f'US${agg_EBITDA}', border=True)
        if (pd.isna(agg_NetIncome) or agg_revenue == 0):
            st.metric(label=f'Lucro líquido (em bilhões)', value=f' - ', border=True)
        else:
            st.metric(label=f'Lucro líquido (em bilhões)', value=f'US${agg_NetIncome}', border=True)

        metric = st.selectbox('Métricas para séries temporais',sorted(metricas_pt.keys()), index=None, placeholder='Métricas', key=f'metrica')
        try:
            metrica_anual = metricas_pt[metric]
            fig_receita = atributo_anual_plotbar(empresa_escolhida,metrica_anual,metric)
            st.plotly_chart(fig_receita)
        except:
            pass

    with col2.container(border=True):
        st.markdown(
            """
            <style>
            .centered-text {
                text-align: center;
                font-size: 28px;
            }
            </style>
            <div class="centered-text">
                Margens (valores médios para o período)<br>
            </div>
            """,
            unsafe_allow_html=True
        )

        e,f = st.columns(2)
        g,h = st.columns(2)

        if pd.isna(media_margem_lucrobruto):
            e.metric(label=f'Margem de lucro bruto', value=f' - ', border=True)
        else:
            e.metric(label=f'Margem de lucro bruto', value=f'{media_margem_lucrobruto}%', border=True)
        if pd.isna(media_margem_operacional):
            f.metric(label=f'Margem de lucro operacional', value=f' - ', border=True)
        else:
            f.metric(label=f'Margem de lucro operacional', value=f'{media_margem_operacional}%', border=True)
        if pd.isna(media_margem_ebitda):
            g.metric(label=f'Margem EBITDA', value=f' - ', border=True)
        else:
            g.metric(label=f'Margem EBITDA', value=f'{media_margem_ebitda}%', border=True)
        if pd.isna(media_margem_ebitda):
            h.metric(label=f'Margem de lucro líquido', value=f' - ', border=True)
        else:
            h.metric(label=f'Margem de lucro líquido', value=f'{media_margem_lucroliquido}%', border=True)        

        roic_medio = round(100*variavel_media(empresa_escolhida,'ROIC',inicio,fim),2)
        eva_medio = round(variavel_media(empresa_escolhida,'EVA',inicio,fim)/1E9,2)
        fig_roic = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = roic_medio,
                        gauge = {"axis": {"range":[0,100]}},
                        title = {'text': "ROIC Médio (%)"}))
                
        fig_roic.update_layout(
                        autosize=False,
                        width=540, 
                        height=360, 
                        margin=dict(l=50, r=50, b=100, t=100, pad=4)
                    )
        

        st.plotly_chart(fig_roic)
        
        if (pd.isna(eva_medio) or agg_revenue == 0):
            st.metric(label=f'Valor econômico adicionado (EVA) - Em bilhões', value=f' - ', border=True)
        else:
            st.metric(label=f'Valor econômico adicionado (EVA) - Em bilhões', value=f'US${eva_medio}', border=True)   
        
if __name__ == "__main__":
    main()

