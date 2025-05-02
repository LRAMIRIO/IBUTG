
# Conversor IBUTG

Este aplicativo transforma dados do INMET (.csv, .xls, .xlsx) no formato compatível com a planilha IBUTG fornecida pelo usuário.

## Funcionalidades
- Aceita múltiplos arquivos.
- Detecta automaticamente fuso horário pelo cabeçalho (CSV).
- Converte UTC para horário local.
- Insere dados entre 08h e 17h.
- Elimina linhas com IBUTG negativo (coluna O).
- Permite download individual por arquivo.

## Como usar
1. Acesse https://streamlit.io/cloud
2. Faça login com GitHub.
3. Crie novo app com este repositório.
4. O app será executado automaticamente.
