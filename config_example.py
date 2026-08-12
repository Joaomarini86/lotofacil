# config_example.py - COPIE para config.py e preencha
DB_CONFIG = {
    "host": "SEU_IP",
    "port": 5432,
    "database": "lotofacil",
    "user": "SEU_USUARIO",
    "password": "SUA_SENHA"
}

CAMINHO_EXCEL = "caminho/para/loto.xlsx"
SHEET_NAME = "lotofacil_www.asloterias.com.br"
COLUNAS_BOLAS_DB = [f"bola_{i}" for i in range(1, 16)]
TOTAL_NUMEROS = 25
NUMEROS_POR_SORTEIO = 15
