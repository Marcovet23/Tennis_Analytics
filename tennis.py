import pandas as pd
#import numpy as np
import zipfile
import requests
from io import BytesIO
from tqdm import tqdm

# Impostazioni di visualizzazione per DataFrame
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# Lista dei link ai file storici (alcuni .xls, alcuni .xlsx, uno .zip)
links = [
    'http://tennis-data.co.uk/2000/2000.xls', 'http://tennis-data.co.uk/2001/2001.xls',
    'http://tennis-data.co.uk/2002/2002.xls', 'http://tennis-data.co.uk/2003/2003.xls',
    'http://tennis-data.co.uk/2004/2004.xls', 'http://tennis-data.co.uk/2005/2005.xls',
    'http://tennis-data.co.uk/2006/2006.xls', 'http://tennis-data.co.uk/2007/2007.xls',
    'http://tennis-data.co.uk/2008/2008.zip', 'http://tennis-data.co.uk/2009/2009.xls',
    'http://tennis-data.co.uk/2010/2010.xls', 'http://tennis-data.co.uk/2011/2011.xls',
    'http://tennis-data.co.uk/2012/2012.xls', 'http://tennis-data.co.uk/2013/2013.xlsx',
    'http://tennis-data.co.uk/2014/2014.xlsx', 'http://tennis-data.co.uk/2015/2015.xlsx',
    'http://tennis-data.co.uk/2016/2016.xlsx', 'http://tennis-data.co.uk/2017/2017.xlsx',
    'http://tennis-data.co.uk/2018/2018.xlsx', 'http://tennis-data.co.uk/2019/2019.xlsx',
    'http://tennis-data.co.uk/2020/2020.xlsx', 'http://tennis-data.co.uk/2021/2021.xlsx',
    'http://tennis-data.co.uk/2022/2022.xlsx', 'http://tennis-data.co.uk/2023/2023.xlsx',
    'http://tennis-data.co.uk/2024/2024.xlsx', 'http://tennis-data.co.uk/2025/2025.xlsx'
]

# Scarico e concateno tutti i file in un unico DataFrame
df = pd.DataFrame()
for elem in tqdm(links, desc="Scaricamento files"):
    if elem.endswith('.zip'):
        # Se è un file zip, lo apro e prendo il primo file contenuto
        content = requests.get(elem)
        zf = zipfile.ZipFile(BytesIO(content.content))
        temp = pd.read_excel(zf.open(zf.namelist()[0]))
    else:
        # Altrimenti è un Excel normale
        temp = pd.read_excel(elem)
    df = pd.concat([df, temp], ignore_index=True)

# Riempio colonne vuote e filtro dataset
df['Best of'] = df['Best of'].fillna(3)
df = df[df['Comment'] == 'Completed'].reset_index(drop=True)
df = df[~df['WRank'].isnull()].reset_index(drop=True)
df = df[~df['LRank'].isnull()].reset_index(drop=True)
df = df[~df['W1'].isnull()].reset_index(drop=True)
df = df[~df['W2'].isnull()].reset_index(drop=True)
df = df[~df['L1'].isnull()].reset_index(drop=True)
df = df[~df['L2'].isnull()].reset_index(drop=True)
df[['W3', 'W4', 'W5', 'L3', 'L4', 'L5']] = df[['W3', 'W4', 'W5', 'L3', 'L4', 'L5']].fillna(0)

# 🔧 Correzione: conversione sicura delle quote a numerico
colsW = ['CBW', 'GBW', 'IWW', 'SBW', 'B&WW', 'EXW', 'PSW', 'UBW', 'LBW', 'SJW']
colsL = ['CBL', 'GBL', 'IWL', 'SBL', 'B&WL', 'EXL', 'PSL', 'UBL', 'LBL', 'SJL']

# Se alcune colonne mancano in certi anni, pandas non darà errore
df[colsW] = df[colsW].apply(pd.to_numeric, errors='coerce')
df[colsL] = df[colsL].apply(pd.to_numeric, errors='coerce')

# Calcolo media delle quote ignorando stringhe non numeriche
df['B365W'] = df['B365W'].fillna(df[colsW].mean(axis=1)).fillna(df['AvgW'])
df['B365L'] = df['B365L'].fillna(df[colsL].mean(axis=1)).fillna(df['AvgL'])

# Indice per distinguere i due giocatori
df['ind'] = [(lambda x: x % 2)(x) for x in range(len(df))]

# Funzione per sostituire celle vuote con 0
def checkempty(val):
    if val == ' ':
        return 0
    return val

df['W3'] = df['W3'].apply(checkempty)
df['L3'] = df['L3'].apply(checkempty)

# 🔧 Conversione robusta a numeri interi (se ci sono stringhe tipo "RET" le mette a 0)
cols_sets = ['W1','L1','W2','L2','W3','L3','W4','L4','W5','L5']
df[cols_sets] = df[cols_sets].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)

# Creo le colonne Player_1 / Player_2, Rank, Pts, Odds
df['Player_1'] = df.apply(lambda row: row['Winner'] if row['ind'] == 0 else row['Loser'], axis=1)
df['Player_2'] = df.apply(lambda row: row['Winner'] if row['ind'] == 1 else row['Loser'], axis=1)
df['Rank_1'] = df.apply(lambda row: row['WRank'] if row['ind'] == 0 else row['LRank'], axis=1)
df['Rank_2'] = df.apply(lambda row: row['WRank'] if row['ind'] == 1 else row['LRank'], axis=1)
df['Pts_1'] = df.apply(lambda row: row['WPts'] if row['ind'] == 0 else row['LPts'], axis=1)
df['Pts_2'] = df.apply(lambda row: row['WPts'] if row['ind'] == 1 else row['LPts'], axis=1)
df['Odd_1'] = df.apply(lambda row: row['B365W'] if row['ind'] == 0 else row['B365L'], axis=1)
df['Odd_2'] = df.apply(lambda row: row['B365W'] if row['ind'] == 1 else row['B365L'], axis=1)

# Funzione per costruire il punteggio in formato leggibile
def score(row):
    if row['ind'] == 0:
        return f"{row['W1']}-{row['L1']} {row['W2']}-{row['L2']} {row['W3']}-{row['L3']} {row['W4']}-{row['L4']} {row['W5']}-{row['L5']}"
    return f"{row['L1']}-{row['W1']} {row['L2']}-{row['W2']} {row['L3']}-{row['W3']} {row['L4']}-{row['W4']} {row['L5']}-{row['W5']}"

df['Score'] = df.apply(lambda row: score(row).replace('0-0', ''), axis=1)
df['Score'] = df['Score'].apply(lambda x: x.strip())

# Seleziono solo le colonne finali di interesse
new_df = df[['Tournament', 'Date', 'Series', 'Court', 'Surface', 'Round',
             'Best of', 'Player_1', 'Player_2','Winner',
             'Rank_1', 'Rank_2', 'Pts_1', 'Pts_2',
             'Odd_1', 'Odd_2', 'Score']]

# 🔧 Correzione formato data (%m per i mesi, non %M)
new_df['Date'] = pd.to_datetime(new_df['Date'], format='%Y-%m-%d', errors='coerce')

# Riempio valori mancanti con -1
new_df = new_df.fillna(-1)

# 🔧 Conversione robusta numerica delle colonne NR/valori anomali
def check(val):
    try:
        if str(val) == "NR":
            return -1
        return val
    except:
        return -1

cols = ['Best of', 'Rank_1', 'Rank_2', 'Pts_1', 'Pts_2']
new_df[cols] = new_df[cols].applymap(check).apply(pd.to_numeric, errors='coerce').fillna(-1).astype(int)

# Esporta in CSV
new_df.to_csv('atp_tennis.csv', index=False)

print("✅ File esportato correttamente: atp_tennis.csv")
