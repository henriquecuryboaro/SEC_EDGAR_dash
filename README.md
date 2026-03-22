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

* **Indicadores acumulados**: 
* **Margens**:

### Imagens

![Visualização de dados no painel](/tela_principal.png "Informaçõs do painel de natureza operacional")


## Conclusões

O objetivo do acesso *on-line* ao painel é permitir ao usuário navegar pelos dados de forma interativa, gerando seus próprios *insights*, mas algumas observações interessantes podem ser destacadas:

* Os dados tratam de operações envolvendo indústrias dos segmentos de polímeros, agroquímica e gases industriais
* A análise de valor de mercado foi realizada com o emprego do método dos múltiplios EV/EBITDA, considerando valores típicos para as estimativas de mercado (sete e dez múltiplos). A referência consultada pode ser encontrada [aqui](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html).
* Nota-se um valor maior do indicador de **produção por empregado** na planta que representa o setor de gases industriais, ilustrando um caso de operação pouco **trabalho-intensiva** em comparação com os demais ativos
* O ativo representativo do setor de gases industriais também apresenta um indicador de *performance*, dentro da avaliação de OEE, em patamar bastante elevado, o que é coerente com a observação de produtividade por empregado feita acima.
* Ainda, estes indicadores apresentados poderiam levar a considerações sobre implementações de mais metodologias de automação (especialmente em setores com indicadores relativamente mais baixos de produtividade)

## Projetos futuros

A conclusão deste painel oferece uma oportunidade para avaliação de indicadores operacionais de forma simples e intuitiva, destacando-se a possibilidade de comparações entre diferentes setores.

Como possibilidade de futuros desenvolvimentos, considera-se a possibilidade de aplicação de modelo preditivo para a obtenção de valores de EBITDA em função de indicadores como OEE ou outras variáveis, visto que este indicador financeiro é um dos mais relevantes para a avaliação da saúde financeira de um empreendimento.

