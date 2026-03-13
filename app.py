import requests
import pandas as pd
import plotly.express as px

CIK_list = ["0000080424","0001666700","0001751788","0000310158","0000034088",
            "0000078003","0000037996","0001467858","0000068505","0000037996",
            "0000018230","0000030625","0000104169","0001048911","0000200406",
            "0001637459","0000315189","0000040545","0000012927","0000051143"]

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

def download_companyfacts(CIK_list):

    headers = {"User-Agent": "henriquecuryboaro hcboaro@gmail.com"}
    company_data = {}

    for cik in CIK_list:
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        response = requests.get(url, headers=headers)
        company_data[cik] = response.json()

    return company_data

company_data = download_companyfacts(CIK_list)

for cik, data in company_data.items():

    entity_name = data['entityName']
    us_gaap = data['facts']['us-gaap']

def df_completo(demonstracao, metric_name, entity_name):

    if demonstracao is None or len(demonstracao) == 0:
        return None

    df = pd.DataFrame(demonstracao)

    # filtra apenas FY e 10-K
    df = df[(df["fp"] == "FY") & (df["form"] == "10-K")].copy()

    if df.empty:
        return None

    # converte datas uma única vez
    df["end"] = pd.to_datetime(df["end"])

    if "start" in df.columns:

        df["start"] = pd.to_datetime(df["start"])

        df["interval"] = (df["end"] - df["start"]).dt.days

        df = df[df["interval"] > 300].copy()

    df["entity"] = entity_name
    df["year"] = df["end"].dt.year

    df = (
        df.sort_values("filed")
        .drop_duplicates("year", keep="last")
    )

    df = df.rename(columns={"val": metric_name})

    return df[["entity", "year", metric_name]]

#Função generalizadora:
def data_consolidada(atributo,tag_list):
    dfs_organisations = []
    for cik,data in company_data.items():        
        entity_name = data['entityName']
        us_gaap = data['facts']['us-gaap']

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


#lista com todos atributos para junção em df unificado
dfs_atributos_consolidados = []

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
    'RnD': rd_tags
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

#criação de colunas com métricas calculadas indiretamente
df_atributo_unificado['CalcProfit'] = round((df_atributo_unificado['Revenue'].fillna(0) - df_atributo_unificado['COGS'].fillna(0)),2)
df_atributo_unificado['EBITDA'] = round((df_atributo_unificado['NetIncome'].fillna(0)+df_atributo_unificado['Interest'].fillna(0)+df_atributo_unificado['Taxes'].fillna(0)+df_atributo_unificado['DepreciationAmortization'].fillna(0)),2)

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

print(df_atributo_unificado)

