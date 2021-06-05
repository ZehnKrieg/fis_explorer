
import time
from datetime import datetime
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import plotly
import openpyxl
import streamlit as st
import plotly.express as px

### Definindo a barra superior da aplicação

# Título
st.write("*Análise de ativos*")
st.title("Fundos Imobiliários")

### Definindo Barra Lateral

# Cabeçalho lateral
st.sidebar.header("Parâmetros")
st.sidebar.markdown("Selecione as datas limites para realizar a análise")
start = st.sidebar.date_input('start date', datetime(2019,1,1))
end = st.sidebar.date_input('end date', datetime.today())

# Coletando dados do FundsExplorer
@st.cache
def coleta_fundos():
    url = "https://www.fundsexplorer.com.br/ranking"
    agent = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    table = soup.find_all('table')[0]
    df = pd.read_html(str(table), decimal=',',thousands='.')[0]
    return df

@st.cache
def call_pega_fundos(stock_dict):
    for symbol in symbols:
        # st.write('Buscando symbol:', symbol)
        try:
            stock_dict[symbol] = pega_fundos(symbol)
        except:
            st.write('Falha na captura do symbol', symbol)
    return stock_dict

def pega_fundos(name):
    stock = yf.download(name, start = start, end = end)
    return stock

def calcula_retorno(stock_dict):
    returns = pd.DataFrame()
    for key in stock_dict.keys():
        returns[key] = stock_dict[key]['Adj Close'].pct_change()
    return returns

def calcula_desconto(df):
    max_price = df['Adj Close'].describe()['75%']
    last_price = df['Adj Close'].iloc[-1]
    desconto = (last_price - max_price)/max_price
    return (desconto*-1)

def call_calcula_desconto(stock_dict):
    discont_dict = {}
    for tick in stock_dict.keys():
        try:
            discont_dict[tick] = calcula_desconto(stock_dict[tick])
        except:
            discont_dict[tick] = 0
    return discont_dict

def pega_setor(stock):
    return [x for x in df[symbols == stock]['Setor']]

def pega_dividendos(stock):
    return [x for x in df[symbols == stock]['DividendYield']]

def pega_pvpa(stock):
    return [x for x in df[symbols == stock]['P/VPA']]

def calcula_desvio(stock_info_df):
    std_list = []
    for tick in stock_info_df['ticker']:
        std_list.append(returns[tick].std())

    stock_info_df['volatilidade'] = std_list
    stock_info_df.sort_values(by = 'desconto').head(10)
    return stock_info_df

def transform_to_number(variable):
    variable = variable.str.replace('%','')
    variable = variable.str.replace(',','.')
    variable = variable.astype(float)
    return variable

# Programando o Botão de inicio
if(st.sidebar.button("Clique para iniciar a coleta e análise de fundos imobiliários")):

    # Barra de progressão
    my_bar = st.progress(0)
    # st.success('Colentando dados do FundsExplorer...')
    with st.spinner('Colentando dados do FundsExplorer...'):
        time.sleep(2)
    
    st.success("Dados coletados!")
    # Coletando dados via BeautifulSoup
    df = coleta_fundos()

    st.write("Tabela FundsExplorer:")
    st.write(df)

    symbols = df['Códigodo fundo'] + '.SA'

    st.write("Symbols:")
    st.write(symbols)

    st.write("Coletando Symbols no Yfinance...")
    stock_dict = {}

    stock_dict = call_pega_fundos(stock_dict)
    
    # Info de sucesso
    st.success("Symbols coletados!")

    with st.spinner('Calculando retorno...'):
        time.sleep(2)

    returns = calcula_retorno(stock_dict)

    st.success("Retorno calculado!")
    
    with st.spinner('Calculando desconto...'):
        time.sleep(2)
    
    discont_dict = {}
    discont_dict = call_calcula_desconto(stock_dict)

    st.success("Desconto calculado!")

    with st.spinner('Buscando setores...'):
        time.sleep(2)

    # Criação da tabela stock_info_df
    stock_info_df = pd.DataFrame.from_dict(discont_dict, orient='index').reset_index()
    stock_info_df.columns = ['ticker','desconto']
    stock_info_df['setor'] = [pega_setor(tick)[0] for tick in stock_info_df['ticker']]
    
    st.success("Setores encontrados!")

    with st.spinner('Buscando DividendYield...'):
        time.sleep(1)

    stock_info_df['dy'] = [pega_dividendos(tick)[0] for tick in stock_info_df['ticker']]

    st.success("DY encontrados!")

    with st.spinner('Buscando P/VPA...'):
        time.sleep(1)

    stock_info_df['p/vpa'] = [pega_pvpa(tick)[0] for tick in stock_info_df['ticker']]

    st.success("P/VPA encontrados!")


    with st.spinner('Calculando desvio padrão (std - volatilidade)...'):
        time.sleep(1)
    
    stock_info_df = calcula_desvio(stock_info_df)

    st.success("Volatilidade (std) calculada!")

    stock_info_df = stock_info_df.dropna()

    stock_info_df["dy"] = transform_to_number(stock_info_df["dy"])
    # stock_info_df["p/vpa"] = transform_to_number(stock_info_df["p/vpa"])

    st.success("Missings removidos!")

    st.write(stock_info_df)

    with st.spinner('Preparando exibição gráfica...'):
        time.sleep(2)
    
    fig1 = px.scatter(stock_info_df, x = 'volatilidade', y = 'desconto', color = 'setor', size = 'dy', hover_name= 'ticker', title= "Oportunidades (volatilidade x desconto x dy por setor):", log_x= True)

    # Para exibir offiline em outra aba:
    # plotly.offline.plot(fig, filename= 'Oportunidades Fundos Imobiliários.html')
    # fig.show()
    st.write(fig1)

    fig2 = px.scatter(stock_info_df, x = 'volatilidade', y = 'p/vpa', color = 'setor', size = 'dy', hover_name= 'ticker', title= "Oportunidades (std x p/vpa x dy por setor):", log_x= True, log_y= True)
    st.write(fig2)
    
    # Criando uma timeline:
#     numeric_df = df.select_dtypes(['float','int'])
    # numeric_cols = numeric_df.columns
    
    # st.write(numeric_df)
    # st.write(numeric_cols)

    # stock_column = df['Códigodo fundo']
    # st.write(stock_column)
    # unique_stocks = stock_column.uniq()
    
    # feature_selection = st.sidebar.multiselect(label="Variaveis numéricas disponívels", options=numeric_cols)
    # stock_dropdown = st.sidebar.selectbox(label="Stock Ticker", options=unique_stocks)
    #fundo = st.selectbox('Selecione um fundo para analisar', df['Códigodo fundo']) 
    # st.write(fundo)

#Fim






















