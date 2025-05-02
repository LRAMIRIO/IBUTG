# Aplicativo WBGT com Horário Local

Este aplicativo Streamlit permite processar arquivos CSV do INMET, detectar automaticamente o fuso horário da estação com base na latitude e longitude no cabeçalho, converter os horários de UTC para horário local e inserir os dados filtrados (das 08h às 17h locais) em uma planilha modelo no formato WBGT.

## Funcionalidades:
- Upload de múltiplos arquivos CSV do INMET.
- Upload da planilha modelo (modelo.xlsx).
- Conversão automática do horário UTC para local (UTC-3 ou UTC-4, conforme cidade).
- Filtragem dos dados apenas entre 08:00 e 17:00 no horário local.
- Inserção automática dos dados nas colunas padrão: DATA, HORA, TAR, TPO, UR, VENTO.
- Download automático de cada planilha processada.

## Instruções:
1. Envie a planilha modelo WBGT (modelo.xlsx).
2. Envie os arquivos CSV do INMET.
3. Baixe os arquivos processados prontos para análise.

## Dependências
Listadas em `requirements.txt` para instalação automática no Streamlit Cloud.

Desenvolvido com apoio do ChatGPT, adaptado do script original usado no Google Colab.
