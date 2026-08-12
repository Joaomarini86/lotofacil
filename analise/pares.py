# analise/pares.py
import psycopg2
import pandas as pd
from collections import Counter
from itertools import combinations
from config import DB_CONFIG, COLUNAS_BOLAS_DB, TOTAL_NUMEROS

def analisar_pares():
    """Analisa quais números mais saem juntos"""
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso", conn)
    conn.close()
    
    pares = Counter()
    for _, row in df.iterrows():
        nums = sorted([int(row[col]) for col in COLUNAS_BOLAS_DB])
        for par in combinations(nums, 2):
            pares[par] += 1
    
    total = len(df)
    print("🔗 TOP 10 PARES QUE MAIS SAEM JUNTOS:")
    print(f"{'Par':<12} {'Vezes':<8} {'% dos sorteios':<15}")
    print("-" * 35)
    for (a, b), count in pares.most_common(10):
        print(f"  {a:2d}-{b:<2d}      {count:<8} {count/total*100:.1f}%")
    
    print("\n🔗 TOP 10 PARES QUE MENOS SAEM JUNTOS:")
    for (a, b), count in sorted(pares.items(), key=lambda x: x[1])[:10]:
        print(f"  {a:2d}-{b:<2d}      {count:<8} {count/total*100:.1f}%")
    
    return pares

if __name__ == "__main__":
    analisar_pares()
