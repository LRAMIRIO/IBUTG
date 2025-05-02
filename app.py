import streamlit as st
import pandas as pd
from timezonefinder import TimezoneFinder
from openpyxl import load_workbook
import pytz
from datetime import datetime
import io
import os

st.set_page_config(page_title="Conversor INMET → WBGT", layout="centered")
st.title("☀️ Conversor de Dados INMET para Planilha WBGT")

# Upload dos arquivos
modelo_uploaded = st.file_uploader("📄 Envie a planilha modelo WBGT (.xlsx)", type='xlsx', key="modelo_file")
csv_uploaded = st.file_uploader("📂 Envie os arquivos CSV do INMET", accept_multiple_files=True, type='csv', key="csv_files")

# Processamento
if modelo_uploaded and csv_uploaded:
    modelo_bytes = modelo_uploaded.read()
    resultados = []

    for arquivo_csv in csv_uploaded:
        st.markdown(f"### ⏳ Processando: `{arquivo_csv.name}`")

        # Extrair latitude e longitude
        latitude = longitude = None
        linhas_cabecalho = arquivo_csv.read().decode('latin1').splitlines()[:10]
        for linha in linhas_cabecalho:
            if 'LATITUDE' in linha.upper():
                latitude = float(linha.split(':')[-1].replace(';', '').replace(',', '.'))
            if 'LONGITUDE' in linha.upper():
                longitude = float(linha.split(':')[-1].replace(';', '').replace(',', '.'))
        if latitude is None or longitude is None:
            st.error("❌ Latitude ou longitude não encontrada.")
            continue

        # Detectar fuso horário
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
        timezone = pytz.timezone(timezone_str)

        # Voltar ponteiro para início do arquivo CSV
        arquivo_csv.seek(0)
        df = pd.read_csv(arquivo_csv, sep=';', skiprows=8, encoding='latin1')
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

        # Carregar planilha modelo
        wb = load_workbook(io.BytesIO(modelo_bytes))
        ws = wb.active

        linha = 4
        for _, row in dados_final.iterrows():
            ibutg_val = ws[f'O{linha}'].value
            if ibutg_val is not None:
                try:
                    ibutg_val = float(str(ibutg_val).replace(',', '.'))
                except:
                    ibutg_val = 0
            else:
                ibutg_val = 0

            if ibutg_val >= 0:
                ws[f'D{linha}'] = row['DATA']
                ws[f'E{linha}'] = row['HORA']
                ws[f'G{linha}'] = row['TAR']
                ws[f'H{linha}'] = row['TPO']
                ws[f'I{linha}'] = row['UR']
                ws[f'J{linha}'] = row['VENTO']
                linha += 1

        nome_saida = f"WBGT_{arquivo_csv.name.replace('.CSV', '').replace(' ', '_')}.xlsx"
        buffer = io.BytesIO()
        wb.save(buffer)
        st.download_button(
            label=f"⬇️ Baixar {nome_saida}",
            data=buffer.getvalue(),
            file_name=nome_saida,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        resultados.append(nome_saida)

    if resultados:
        st.success("✅ Processamento finalizado!")
