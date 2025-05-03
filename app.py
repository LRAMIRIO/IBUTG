
import streamlit as st
import pandas as pd
from timezonefinder import TimezoneFinder
from openpyxl import load_workbook
import pytz
from datetime import datetime
import io
import os

st.title("Conversor WBGT com Detecção de Fuso Horário")

modelo_uploaded = st.file_uploader("📄 Envie a planilha modelo WBGT (.xlsx):", type=["xlsx"], key="modelo")
csv_uploaded = st.file_uploader("📄 Envie os arquivos CSV do INMET:", type=["csv"], accept_multiple_files=True, key="csvs")

if modelo_uploaded and csv_uploaded:
    modelo_bytes = modelo_uploaded.read()
    os.makedirs("saidas", exist_ok=True)

    for csv_file in csv_uploaded:
        st.write(f"🔄 Processando: {csv_file.name}")
        latitude = longitude = None

        lines = csv_file.read().decode("latin1").splitlines()
        for line in lines[:10]:
            if "LATITUDE" in line.upper():
                latitude = float(line.split(":")[-1].replace(";", "").replace(",", "."))
            if "LONGITUDE" in line.upper():
                longitude = float(line.split(":")[-1].replace(";", "").replace(",", "."))

        if latitude is None or longitude is None:
            st.error("❌ Latitude ou longitude não encontrada no cabeçalho.")
            continue

        tf = TimezoneFinder()
        timezone = pytz.timezone(tf.timezone_at(lng=longitude, lat=latitude))

        csv_file.seek(0)
        df = pd.read_csv(csv_file, sep=";", skiprows=8, encoding="latin1")

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

        wb = load_workbook(io.BytesIO(modelo_bytes))
        ws = wb.active

        linha = 4
        for _, row in dados_final.iterrows():
            ibutg_val = ws[f'O{linha}'].value
            try:
                ibutg_val = float(str(ibutg_val).replace(',', '.')) if ibutg_val is not None else 0
            except:
                ibutg_val = 0

            if ibutg_val >= 0:
                ws[f'D{linha}'] = row['DATA']
                ws[f'E{linha}'] = row['HORA']
                ws[f'G{linha}'] = row['TAR']
                ws[f'H{linha}'] = row['TPO']
                ws[f'I{linha}'] = row['UR']
                ws[f'J{linha}'] = row['VENTO']
                linha += 1

        nome_saida = f"saidas/WBGT_{csv_file.name.replace('.CSV', '').replace(' ', '_')}.xlsx"
        wb.save(nome_saida)
        with open(nome_saida, "rb") as f:
            st.download_button(f"⬇️ Baixar {os.path.basename(nome_saida)}", f, file_name=os.path.basename(nome_saida))
