# 📄 Painel de informações financeiras de empresas listadas nos EUA


## Introdução

Este documento introduz  as funcionalidades encontradas no **Painel de informações financeiras de empresas listadas nos EUA**, desenvolvido como modelo a ser aplicado em cenários de avaliação da saúde financeira de empresas. Os dados reunidos e apresentados nesta aplicação são públicos, obtidos por consultas à API do sistema EDGAR da SEC (Securities and Exchange Commission), agência federal dos Estados Unidos que regula mercados financeiros.

## Metodologia

A manipulação dos dados é realizada integralmente por meio de um subrotinas escritas na linguagem Python, sendo destacado o uso da biblioteca Streamlit para elaboração do painel de visualização.

## Acesso ao painel e base de dados

O painel para visualização dos dados e aplicação pode ser acessado diretamente através [deste link](https://secedgardash.streamlit.app/).

Alternativamente, o repositório pode ser clonado para que as subrotinas sejam executadas localmente em um interpretador Python. Seguem as etapas:

```
git clone https://github.com/henriquecuryboaro/SEC_EDGAR_dash

```
Com o diretório clonado, instalam-se os pacotes necessários à execução do painel ao se executar o seguinte código no diretório em que os arquivos do projeto se encontram:

```
pip install -r requirements.txt
```

É recomendado o isolamento do ambiente em que o projeto será executado por meio da criação de ambiente virtual.

## Conteúdo do painel

O conteúdo do painel é exibido em uma página única, com a visualização dos dados ocorrendo em dois blocos:

* **Indicadores acumulados**: somatório de resultados financeiros disponíveis para a companhia selecionada dentro do período analisado
* **Margens**: valores médios de indicadores financeiros dentro do período analisado

Além disso, é possível visualizar a evolução temporal dos indicadores financeiros (tanto absolutos quanto margens) ao longo do período disponível para análise, em gráfico.

### Imagens

![Visualização de dados no painel](/tela_principal.png "Informaçõs do painel de natureza operacional")


