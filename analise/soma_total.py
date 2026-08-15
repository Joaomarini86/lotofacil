# analise/soma_total.py
import psycopg2
import pandas as pd
import numpy as np
from config import DB_CONFIG, COLUNAS_BOLAS_DB

def analisar_soma():
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso", conn)
    conn.close()
    
    # Calcular soma de cada sorteio
    somas = df[COLUNAS_BOLAS_DB].sum(axis=1).values
    
    media = np.mean(somas)
    dp = np.std(somas)
    minimo = int(np.min(somas))
    maximo = int(np.max(somas))
    q1 = int(np.percentile(somas, 25))
    q3 = int(np.percentile(somas, 75))
    
    print("📊 ANÁLISE DA SOMA DOS NÚMEROS")
    print("-" * 35)
    print(f"Média:          {media:.1f}")
    print(f"Desvio Padrão:  {dp:.1f}")
    print(f"Mínimo:         {minimo}")
    print(f"Máximo:         {maximo}")
    print(f"Q1 (25%):       {q1}")
    print(f"Q3 (75%):       {q3}")
    print(f"IC 95%:         {media - 2*dp:.0f} a {media + 2*dp:.0f}")
    
    # Distribuição
    print(f"\n📈 Distribuição das somas:")
    print(f"   {media - 3*dp:.0f} a {media - 2*dp:.0f}: {sum(1 for s in somas if media - 3*dp <= s < media - 2*dp)} sorteios")
    print(f"   {media - 2*dp:.0f} a {media - 1*dp:.0f}: {sum(1 for s in somas if media - 2*dp <= s < media - 1*dp)} sorteios")
    print(f"   {media - 1*dp:.0f} a {media:.0f}:      {sum(1 for s in somas if media - dp <= s < media)} sorteios")
    print(f"   {media:.0f} a {media + 1*dp:.0f}:      {sum(1 for s in somas if media <= s < media + dp)} sorteios")
    print(f"   {media + 1*dp:.0f} a {media + 2*dp:.0f}: {sum(1 for s in somas if media + dp <= s < media + 2*dp)} sorteios")
    print(f"   {media + 2*dp:.0f} a {media + 3*dp:.0f}: {sum(1 for s in somas if media + 2*dp <= s < media + 3*dp)} sorteios")
    
    return {'somas': somas, 'media': media, 'dp': dp, 'q1': q1, 'q3': q3, 'min': minimo, 'max': maximo}

if __name__ == "__main__":
    analisar_soma()
