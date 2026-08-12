# analise/posicao.py
import psycopg2
import pandas as pd
import numpy as np
from config import DB_CONFIG, COLUNAS_BOLAS_DB, TOTAL_NUMEROS

def analisar_posicoes():
    """Analisa média, desvio padrão e quartis por posição (bola 1 a 15)"""
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso", conn)
    conn.close()
    
    print(f"{'Posição':<10} {'Média':<8} {'Mediana':<10} {'DP':<8} {'Mín':<6} {'Máx':<6} {'Q1':<6} {'Q3':<6}")
    print("-" * 60)
    
    dados_posicao = {}
    for i, col in enumerate(COLUNAS_BOLAS_DB, 1):
        valores = df[col].values
        media = np.mean(valores)
        mediana = np.median(valores)
        dp = np.std(valores)
        minimo = np.min(valores)
        maximo = np.max(valores)
        q1 = np.percentile(valores, 25)
        q3 = np.percentile(valores, 75)
        
        print(f"Bola {i:<4} {media:<8.1f} {mediana:<10.1f} {dp:<8.2f} {minimo:<6.0f} {maximo:<6.0f} {q1:<6.0f} {q3:<6.0f}")
        
        dados_posicao[f'bola_{i}'] = {
            'media': round(media, 1),
            'mediana': round(mediana, 1),
            'dp': round(dp, 2),
            'min': int(minimo),
            'max': int(maximo),
            'q1': int(q1),
            'q3': int(q3)
        }
    
    return dados_posicao

if __name__ == "__main__":
    analisar_posicoes()
