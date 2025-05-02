import streamlit as st
import pandas as pd
from timezonefinder import TimezoneFinder
from openpyxl import load_workbook
import pytz
import io
import os

st.set_page_config(page_title="Conversor WBGT", layout="centered")
st.title("☀️ Conversor de Dados INMET para Planilha WBGT")
st.markdown("Este aplicativo converte arquivos CSV do INMET para o modelo WBGT (.xlsx), entre 08h e 17h no horário local detectado automaticamente.")

modelo_uploaded = st.file_uploader("📄 Envie a planilha modelo WBGT (.xlsx):", type=["xlsx"], key="modelo")
csv_uploaded = st.file_uploader("📄 Envie os arquivos CSV do INMET:", type=["csv"], accept_multiple_files=True, key="csvs")


if modelo_uploaded and csv_uploaded:
    modelo_bytes = modelo_uploaded.read()
    for csv_file in csv_uploaded:
        st.write(f"🔄 Processando: {csv_file.name}")
        
        latitude = longitude = None
        for i in range(10):
            linha = csv_file.readline().decode('latin1')
            if 'LATITUDE' in linha.upper():
                latitude = float(linha.split(':')[-1].replace(';', '').replace(',', '.'))
            if 'LONGITUDE' in linha.upper():
                longitude = float(linha.split(':')[-1].replace(';', '').replace(',', '.'))
        csv_file.seek(0)

        if latitude is None or longitude is None:
            st.error(f"❌ Latitude ou longitude não encontrada no cabeçalho de {csv_file.name}")
            continue

        tf = TimezoneFinder()
        timezone = pytz.timezone(tf.timezone_at(lng=longitude, lat=latitude))

        df = pd.read_csv(csv_file, sep=';', skiprows=8, encoding='latin1')
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
        df_filtrado = df_filtrado.sort_values(by='data_hora_local').reset_index(drop=True)

        dados_final = pd.DataFrame({
            'DATA': df_filtrado['data_hora_local'].dt.date,
            'HORA': df_filtrado['data_hora_local'].dt.strftime('%H:%M'),
            'TAR': df_filtrado['TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)'],
            'TPO': df_filtrado['TEMPERATURA DO PONTO DE ORVALHO (°C)'],
            'UR': df_filtrado['UMIDADE RELATIVA DO AR, HORARIA (%)'],
            'VENTO': df_filtrado['VENTO, VELOCIDADE HORARIA (m/s)']
        })

        wb = load_workbook("Modelo.xlsx")
        ws = wb.active

        linha = 4
        for _, row in dados_final.iterrows():
            ws[f'D{linha}'] = row['DATA']
            ws[f'E{linha}'] = row['HORA']
            ws[f'G{linha}'] = row['TAR']
            ws[f'H{linha}'] = row['TPO']
            ws[f'I{linha}'] = row['UR']
            ws[f'J{linha}'] = row['VENTO']
            linha += 1

        nome_saida = f"WBGT_{csv_file.name.replace('.CSV', '').replace(' ', '_')}.xlsx"
        wb.save(nome_saida)
        with open(nome_saida, "rb") as f:
            st.download_button("📥 Baixar planilha gerada", f, file_name=nome_saida)
        os.remove(nome_saida)
