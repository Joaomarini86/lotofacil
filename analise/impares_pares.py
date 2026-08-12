# analise/impares_pares.py
import psycopg2
import pandas as pd
from collections import Counter
from config import DB_CONFIG, COLUNAS_BOLAS_DB

def analisar_impares_pares():
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso", conn)
    conn.close()
    
    distribuicao = Counter()
    for _, row in df.iterrows():
        impares = sum(1 for col in COLUNAS_BOLAS_DB if int(row[col]) % 2 == 1)
        pares = 15 - impares
        distribuicao[(impares, pares)] += 1
    
    total = len(df)
    print("📊 DISTRIBUIÇÃO ÍMPARES x PARES:")
    print(f"{'Ímpares':<10} {'Pares':<8} {'Vezes':<8} {'%':<8}")
    print("-" * 35)
    
    for (imp, par), count in sorted(distribuicao.most_common(), key=lambda x: x[0][0]):
        print(f"   {imp:<8} {par:<8} {count:<8} {count/total*100:.1f}%")
    
    moda = distribuicao.most_common(1)[0]
    print(f"\n📌 Mais comum: {moda[0][0]} ímpares + {moda[0][1]} pares ({moda[1]/total*100:.1f}%)")

if __name__ == "__main__":
    analisar_impares_pares()
