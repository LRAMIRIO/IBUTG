
import pandas as pd
import matplotlib.pyplot as plt
from timezonefinder import TimezoneFinder
from openpyxl import load_workbook
import pytz
from datetime import datetime
import streamlit as st
from io import BytesIO
import io
import os

# Etapa 1: Upload
print("📄 Envie a planilha modelo WBGT (.xlsx):")
modelo_uploaded = st.file_uploader('Envie os arquivos CSV do INMET', accept_multiple_files=True, type='csv')

print("📄 Envie os arquivos CSV do INMET:")
csv_uploaded = st.file_uploader('Envie os arquivos CSV do INMET', accept_multiple_files=True, type='csv')

# Etapa 2: Processamento
modelo_bytes = modelo_uploaded.read() if modelo_uploaded else None
os.makedirs("graficos", exist_ok=True)

for file_csv in csv_uploaded if csv_uploaded else []:
    nome_csv = file_csv.name
    # Etapa 3: Detectar coordenadas
    latitude = longitude = None
    file_csv.seek(0)
    content = file_csv.read().decode('latin1').splitlines()
    for linha in content[:10]:
        for _ in range(10):
            linha = f.readline().strip()
            if 'LATITUDE' in linha.upper():
                latitude = float(linha.split(':')[-1].replace(';', '').replace(',', '.'))
            if 'LONGITUDE' in linha.upper():
                longitude = float(linha.split(':')[-1].replace(';', '').replace(',', '.'))

    if latitude is None or longitude is None:
        raise ValueError("❌ Latitude ou longitude não encontrada no cabeçalho.")

    # Etapa 4: Fuso horário
    tf = TimezoneFinder()
    timezone = pytz.timezone(tf.timezone_at(lng=longitude, lat=latitude))

    # Etapa 5: Leitura
    file_csv.seek(0)
    df = pd.read_csv(file_csv, sep=';', skiprows=8, encoding='latin1')
    df = df[[
        'DATA (YYYY-MM-DD)', 'HORA (UTC)',
        'TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)',
        'TEMPERATURA DO PONTO DE ORVALHO (°C)',
        'UMIDADE RELATIVA DO AR, HORARIA (%)',
        'VENTO, VELOCIDADE HORARIA (m/s)'
    ]]
    for col in df.columns[2:]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

    df['data_hora_utc'] = pd.to_datetime(df['DATA (YYYY-MM-DD)'] + ' ' + df['HORA (UTC)'], format='%Y-%m-%d %H:%M', utc=True)
    df['data_hora_local'] = df['data_hora_utc'].dt.tz_convert(timezone)
    df['hora_local'] = df['data_hora_local'].dt.hour

    df_filtrado = df[(df['hora_local'] >= 8) & (df['hora_local'] <= 17)].copy()
    df_filtrado = df_filtrado.sort_values(by='data_hora_local')

    dados_final = pd.DataFrame({
        'DATA': df_filtrado['data_hora_local'].dt.date,
        'HORA': df_filtrado['data_hora_local'].dt.strftime('%H:%M'),
        'TAR': df_filtrado['TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)'],
        'TPO': df_filtrado['TEMPERATURA DO PONTO DE ORVALHO (°C)'],
        'UR': df_filtrado['UMIDADE RELATIVA DO AR, HORARIA (%)'],
        'VENTO': df_filtrado['VENTO, VELOCIDADE HORARIA (m/s)']
    })

    wb = load_workbook(io.BytesIO(modelo_bytes))
    ws = wb.active

    for i, row in dados_final.iterrows():
        linha = 4 + i
        ws[f'D{linha}'] = row['DATA']
        ws[f'E{linha}'] = row['HORA']
        ws[f'G{linha}'] = row['TAR']
        ws[f'H{linha}'] = row['TPO']
        ws[f'I{linha}'] = row['UR']
        ws[f'J{linha}'] = row['VENTO']

    nome_saida = f"{os.path.splitext(nome_csv)[0]}_WBGT_08h_17h.xlsx".replace(" ", "_")
    wb.save(nome_saida)
    st.download_button('📥 Baixar ' + nome_saida, open(nome_saida, 'rb').read(), file_name=nome_saida)
