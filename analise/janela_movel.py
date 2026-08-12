# analise/janela_movel.py
import psycopg2
import pandas as pd
from collections import Counter
from config import DB_CONFIG, COLUNAS_BOLAS_DB, TOTAL_NUMEROS

def analisar_janela_movel(janela=50):
    """Analisa números quentes e frios nos últimos N sorteios"""
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql(f"""
        SELECT * FROM sorteios 
        ORDER BY concurso DESC 
        LIMIT {janela}
    """, conn)
    conn.close()
    
    # Extrair números
    todos = []
    for _, row in df.iterrows():
        for col in COLUNAS_BOLAS_DB:
            todos.append(int(row[col]))
    
    freq = Counter(todos)
    total_sorteios = len(df)
    freq_esperada = total_sorteios * 15 / TOTAL_NUMEROS
    
    resultados = []
    for num in range(1, TOTAL_NUMEROS + 1):
        obs = freq.get(num, 0)
        diff = obs - freq_esperada
        resultados.append({
            'numero': num,
            'freq': obs,
            'esperado': round(freq_esperada, 1),
            'diferenca': round(diff, 1),
            'status': '🔥 Quente' if diff > 0 else '❄️ Frio'
        })
    
    resultados.sort(key=lambda x: x['diferenca'], reverse=True)
    
    print(f"📊 NÚMEROS QUENTES E FRIOS (últimos {janela} sorteios)")
    print(f"Frequência esperada: {freq_esperada:.1f}x cada número")
    print("-" * 55)
    print("\n🔥 TOP 5 QUENTES:")
    for r in resultados[:5]:
        print(f"   Nº {r['numero']:2d}: {r['freq']:.0f}x (+{r['diferenca']:.0f} acima do esperado)")
    
    print("\n❄️ TOP 5 FRIOS:")
    for r in resultados[-5:]:
        print(f"   Nº {r['numero']:2d}: {r['freq']:.0f}x ({r['diferenca']:.0f} abaixo do esperado)")
    
    return resultados

if __name__ == "__main__":
    analisar_janela_movel(50)
