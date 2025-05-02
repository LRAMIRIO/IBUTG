
import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime
import io
import os

st.set_page_config(page_title="Conversor IBUTG", layout="wide")
st.title("Conversor de Dados INMET para Planilha IBUTG")

st.markdown("### 📤 Envie os arquivos necessários")
modelo_file = st.file_uploader("Envie a planilha modelo IBUTG (.xlsx)", type=["xlsx"], key="modelo")
csv_files = st.file_uploader("Envie os arquivos do INMET (.csv, .xls, .xlsx)", type=["csv", "xls", "xlsx"], accept_multiple_files=True, key="csvs")

if modelo_file and csv_files:
    modelo_bytes = modelo_file.read()
    for arquivo in csv_files:
        nome = arquivo.name
        ext = os.path.splitext(nome)[-1].lower()
        st.write(f"🔄 Processando: {nome}")

        # Detectar latitude e longitude do cabeçalho (caso CSV)
        latitude = longitude = None
        if ext == ".csv":
            cabecalho = arquivo.read().decode("latin1").split("\n")[:10]
            for linha in cabecalho:
                if "LATITUDE" in linha.upper():
                    latitude = float(linha.split(":")[-1].replace(";", "").replace(",", ".").strip())
                if "LONGITUDE" in linha.upper():
                    longitude = float(linha.split(":")[-1].replace(";", "").replace(",", ".").strip())
            arquivo.seek(0)  # resetar ponteiro

        # Se for .xls/.xlsx, latitude/longitude não será usada
        timezone = pytz.timezone("America/Sao_Paulo")  # padrão
        if latitude and longitude:
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
            if timezone_str:
                timezone = pytz.timezone(timezone_str)

        # Leitura
        if ext == ".csv":
            df = pd.read_csv(arquivo, sep=";", skiprows=8, encoding="latin1")
            for col in df.columns[2:]:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors='coerce')
        elif ext in [".xls", ".xlsx"]:
            df = pd.read_excel(arquivo, skiprows=8)
        else:
            st.warning(f"❌ Formato não suportado: {ext}")
            continue

        df = df[[
            'DATA (YYYY-MM-DD)', 'HORA (UTC)',
            'TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)',
            'TEMPERATURA DO PONTO DE ORVALHO (°C)',
            'UMIDADE RELATIVA DO AR, HORARIA (%)',
            'VENTO, VELOCIDADE HORARIA (m/s)'
        ]]
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
            if ws[f"O{linha}"].value is not None:
                try:
                    ibutg = float(str(ws[f"O{linha}"].value).replace(",", "."))
                    if ibutg < 0:
                        linha += 1
                        continue
                except:
                    pass

            ws[f"D{linha}"] = row['DATA']
            ws[f"E{linha}"] = row['HORA']
            ws[f"G{linha}"] = row['TAR']
            ws[f"H{linha}"] = row['TPO']
            ws[f"I{linha}"] = row['UR']
            ws[f"J{linha}"] = row['VENTO']
            linha += 1

        nome_saida = f"IBUTG_{nome.replace(' ', '_').replace('.CSV','').replace('.xlsx','').replace('.xls','')}.xlsx"
        wb.save(nome_saida)
        with open(nome_saida, "rb") as f:
            st.download_button("⬇️ Baixar resultado", f, file_name=nome_saida)
