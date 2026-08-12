# lotofacil_app.py - Streamlit App Completo
import streamlit as st
import psycopg2
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from config import DB_CONFIG, COLUNAS_BOLAS_DB, TOTAL_NUMEROS

PRECOS = {15: 3.50, 16: 56.00, 17: 476.00}

# ==========================================
# FUNÇÕES DE BANCO
# ==========================================
def conectar():
    return psycopg2.connect(**DB_CONFIG)

def carregar_dados(janela=0):
    conn = conectar()
    df_total = pd.read_sql("SELECT COUNT(*) as total FROM sorteios", conn)
    total_banco = df_total['total'].iloc[0]
    
    if janela == 0:
        limite = total_banco
        label = "TODOS"
    elif janela == 1000:
        limite = 1000
        label = "1000"
    else:
        limite = int(total_banco * 0.5)
        label = f"50% ({limite})"
    
    if limite >= total_banco:
        df = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso DESC", conn)
    else:
        df = pd.read_sql(f"SELECT * FROM sorteios ORDER BY concurso DESC LIMIT {limite}", conn)
    
    conn.close()
    
    ultimo = df.iloc[0]
    ultimos_numeros = [int(ultimo[col]) for col in COLUNAS_BOLAS_DB]
    
    scores = {}
    for num in range(1, 26):
        count = sum(1 for _, r in df.iterrows() 
                    if num in [int(r[c]) for c in COLUNAS_BOLAS_DB])
        freq = count / len(df)
        
        atraso = 0
        for _, r in df.iterrows():
            if num in [int(r[c]) for c in COLUNAS_BOLAS_DB]:
                break
            atraso += 1
        
        bonus = 0.20 if num in ultimos_numeros else 0
        scores[num] = freq * 0.30 + (1 - 0.4**atraso) * 0.50 + bonus * 0.20
    
    return scores, ultimos_numeros, len(df), label

def gerar_jogo(ultimos, scores, semente):
    np.random.seed(semente)
    qtd_repetir = 8 if np.random.random() < 0.5 else 9
    qtd_fora = 15 - qtd_repetir
    
    repetir_ordenados = sorted(ultimos, key=lambda x: scores[x], reverse=True)
    fixos = repetir_ordenados[:5]
    candidatos = [n for n in repetir_ordenados if n not in fixos]
    np.random.shuffle(candidatos)
    variaveis = candidatos[:qtd_repetir - 5]
    escolhidos = fixos + variaveis
    
    nao_sairam = [n for n in range(1, 26) if n not in ultimos]
    fora_ordenados = sorted(nao_sairam, key=lambda x: scores[x], reverse=True)
    fixos_fora = fora_ordenados[:3]
    candidatos_fora = [n for n in fora_ordenados if n not in fixos_fora]
    np.random.shuffle(candidatos_fora)
    variaveis_fora = candidatos_fora[:qtd_fora - 3]
    
    escolhidos = escolhidos + fixos_fora + variaveis_fora
    jogo = sorted(set(escolhidos))[:15]
    
    while len(jogo) < 15:
        extras = [n for n in range(1, 26) if n not in jogo]
        extras.sort(key=lambda x: scores[x], reverse=True)
        jogo = sorted(jogo + [extras[0]])
    
    return jogo[:15]

def calcular_opcoes(orcamento):
    opcoes = []
    qtd_15 = int(orcamento / PRECOS[15])
    opcoes.append({'id': 1, 'label': f"{qtd_15} jogos de 15", 'qtd_15': qtd_15, 'qtd_16': 0, 'qtd_17': 0, 'total': int(qtd_15 * PRECOS[15])})
    
    if orcamento >= PRECOS[16]:
        resto = orcamento - PRECOS[16]
        qtd_15 = int(resto / PRECOS[15])
        opcoes.append({'id': 2, 'label': f"1 de 16 + {qtd_15} de 15", 'qtd_15': qtd_15, 'qtd_16': 1, 'qtd_17': 0, 'total': int(PRECOS[16] + qtd_15 * PRECOS[15])})
    
    if orcamento >= PRECOS[16] * 2:
        resto = orcamento - PRECOS[16] * 2
        qtd_15 = int(resto / PRECOS[15])
        opcoes.append({'id': 3, 'label': f"2 de 16 + {qtd_15} de 15", 'qtd_15': qtd_15, 'qtd_16': 2, 'qtd_17': 0, 'total': int(PRECOS[16] * 2 + qtd_15 * PRECOS[15])})
    
    if orcamento >= PRECOS[17]:
        resto = orcamento - PRECOS[17]
        qtd_15 = int(resto / PRECOS[15])
        opcoes.append({'id': 4, 'label': f"1 de 17 + {qtd_15} de 15", 'qtd_15': qtd_15, 'qtd_16': 0, 'qtd_17': 1, 'total': int(PRECOS[17] + qtd_15 * PRECOS[15])})
    
    return opcoes

# ==========================================
# STREAMLIT APP
# ==========================================
st.set_page_config(page_title="Lotofácil - Análise Estatística", layout="wide")
st.title("🎯 LOTOFÁCIL - SISTEMA INTELIGENTE")
st.markdown("---")

# Sidebar
st.sidebar.header("📊 Configurações")
janela_op = st.sidebar.selectbox("Janela de análise:", ["TODOS", "1000", "50%"])
janela_map = {"TODOS": 0, "1000": 1000, "50%": 50}
janela = janela_map[janela_op]

# Carregar dados
scores, ultimos, total, label = carregar_dados(janela)

# ==========================================
# ABA 1: GERADOR
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["🎲 Gerador", "📊 Análise", "📥 Alimentar", "📋 Resultados"])

with tab1:
    st.header("🎲 Gerador Inteligente de Palpites")
    
    col1, col2 = st.columns(2)
    with col1:
        orcamento = st.number_input("💰 Quanto gastar? (R$)", min_value=3.50, max_value=10000.0, value=20.0, step=1.0)
    with col2:
        st.write(f"📊 Base: **{label}** ({total} sorteios)")
        st.write(f"🎱 Último sorteio: **{ultimos}**")
    
    if st.button("🚀 Gerar Palpites", type="primary"):
        opcoes = calcular_opcoes(orcamento)
        
        st.subheader("🎯 Estratégias disponíveis:")
        for op in opcoes:
            economia = int(orcamento) - op['total']
            st.write(f"   **{op['id']}** - {op['label']} = R$ {op['total']:.2f} (sobra: R$ {economia:.2f})")
        
        opcao_id = st.selectbox("Escolha a estratégia:", [o['id'] for o in opcoes], 
                                format_func=lambda x: [o['label'] for o in opcoes if o['id'] == x][0])
        
        if st.button("✅ Confirmar e Gerar"):
            escolhida = [o for o in opcoes if o['id'] == opcao_id][0]
            
            jogos = []
            semente = 42
            
            for _ in range(escolhida['qtd_17']):
                jogo = gerar_jogo(ultimos, scores, semente)
                semente += 1
                extras = [n for n in range(1, 26) if n not in jogo]
                extras.sort(key=lambda x: scores[x], reverse=True)
                jogos.append({'tipo': 17, 'numeros': sorted(jogo + extras[:2]), 'preco': PRECOS[17]})
            
            for _ in range(escolhida['qtd_16']):
                jogo = gerar_jogo(ultimos, scores, semente)
                semente += 1
                extras = [n for n in range(1, 26) if n not in jogo]
                extras.sort(key=lambda x: scores[x], reverse=True)
                jogos.append({'tipo': 16, 'numeros': sorted(jogo + [extras[0]]), 'preco': PRECOS[16]})
            
            for i in range(escolhida['qtd_15']):
                jogo = gerar_jogo(ultimos, scores, semente + i)
                jogos.append({'tipo': 15, 'numeros': jogo, 'preco': PRECOS[15]})
            
            st.success(f"✅ {len(jogos)} jogos gerados! Total: R$ {sum(j['preco'] for j in jogos):.2f}")
            
            for i, jogo in enumerate(jogos, 1):
                repete = len(set(jogo['numeros']) & set(ultimos))
                imp = sum(1 for n in jogo['numeros'] if n % 2 == 1)
                soma = sum(jogo['numeros'])
                with st.expander(f"🎯 Jogo {i} ({jogo['tipo']} números - R$ {jogo['preco']:.2f})"):
                    st.write(f"**Números:** {jogo['numeros']}")
                    st.write(f"Repete do último: {repete} | Ímpares: {imp} | Pares: {15 - imp} | Soma: {soma}")

with tab2:
    st.header("📊 Análise Estatística Completa")
    
    # Frequência
    st.subheader("📈 Frequência dos Números")
    conn = conectar()
    df_total = pd.read_sql("SELECT * FROM sorteios", conn)
    conn.close()
    
    freq_data = []
    for num in range(1, 26):
        count = sum(1 for _, r in df_total.iterrows() if num in [int(r[c]) for c in COLUNAS_BOLAS_DB])
        freq_data.append({'Número': num, 'Frequência': count, '%': f"{count/len(df_total)*100:.1f}%"})
    
    df_freq = pd.DataFrame(freq_data)
    fig = px.bar(df_freq, x='Número', y='Frequência', text='%', 
                 title='Frequência de cada número da Lotofácil',
                 color='Frequência', color_continuous_scale='Viridis')
    st.plotly_chart(fig, use_container_width=True)
    
    # Atraso
    st.subheader("⏰ Atraso Atual")
    conn = conectar()
    df_desc = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso DESC", conn)
    conn.close()
    
    atraso_data = []
    for num in range(1, 26):
        atraso = 0
        for _, r in df_desc.iterrows():
            if num in [int(r[c]) for c in COLUNAS_BOLAS_DB]:
                break
            atraso += 1
        prob = 0.4 ** atraso * 100
        atraso_data.append({'Número': num, 'Atraso': atraso, 'Probabilidade': f"{prob:.2f}%"})
    
    df_atraso = pd.DataFrame(atraso_data)
    fig = px.bar(df_atraso, x='Número', y='Atraso', text='Probabilidade',
                 title='Atraso atual (sorteios sem sair)',
                 color='Atraso', color_continuous_scale='Reds')
    st.plotly_chart(fig, use_container_width=True)
    
    # Ímpares x Pares
    st.subheader("📊 Distribuição Ímpares x Pares")
    from collections import Counter
    dist = Counter()
    for _, row in df_total.iterrows():
        imp = sum(1 for c in COLUNAS_BOLAS_DB if int(row[c]) % 2 == 1)
        par = 15 - imp
        dist[(imp, par)] += 1
    
    imp_par_data = []
    for (imp, par), count in sorted(dist.items()):
        imp_par_data.append({'Ímpares': imp, 'Pares': par, 'Vezes': count, '%': f"{count/len(df_total)*100:.1f}%"})
    
    df_ip = pd.DataFrame(imp_par_data)
    fig = px.bar(df_ip, x='Ímpares', y='Vezes', text='%',
                 title='Distribuição de Ímpares x Pares nos sorteios',
                 color='Vezes', color_continuous_scale='Blues')
    st.plotly_chart(fig, use_container_width=True)
    
    # Soma
    st.subheader("📈 Distribuição da Soma dos Números")
    somas = df_total[COLUNAS_BOLAS_DB].sum(axis=1)
    media = np.mean(somas)
    dp = np.std(somas)
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=somas, nbinsx=30, name='Somas', marker_color='green'))
    fig.add_vline(x=media, line_dash="dash", line_color="red", annotation_text=f"Média: {media:.0f}")
    fig.add_vline(x=media - dp, line_dash="dot", line_color="orange", annotation_text=f"-1σ: {media-dp:.0f}")
    fig.add_vline(x=media + dp, line_dash="dot", line_color="orange", annotation_text=f"+1σ: {media+dp:.0f}")
    fig.update_layout(title=f'Distribuição da Soma (média: {media:.1f}, DP: {dp:.1f})')
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("📥 Alimentar Banco de Dados")
    
    op_alimentar = st.radio("Opção:", ["📝 Inserir manualmente", "📂 Importar planilha"])
    
    if op_alimentar == "📝 Inserir manualmente":
        col1, col2 = st.columns(2)
        with col1:
            concurso = st.number_input("Nº do concurso:", min_value=1, value=3759)
            data = st.date_input("Data:", value=datetime.now())
        with col2:
            bolas_input = st.text_input("Números (separados por vírgula):", "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15")
        
        if st.button("✅ Salvar"):
            try:
                bolas = [int(b.strip()) for b in bolas_input.split(',')]
                if len(bolas) != 15:
                    st.error("❌ Devem ser 15 números!")
                elif any(b < 1 or b > 25 for b in bolas):
                    st.error("❌ Números devem estar entre 1 e 25!")
                else:
                    conn = conectar()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO sorteios (concurso, data, 
                            bola_1, bola_2, bola_3, bola_4, bola_5,
                            bola_6, bola_7, bola_8, bola_9, bola_10,
                            bola_11, bola_12, bola_13, bola_14, bola_15)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (concurso) DO UPDATE SET
                            data = EXCLUDED.data,
                            bola_1 = EXCLUDED.bola_1, bola_2 = EXCLUDED.bola_2,
                            bola_3 = EXCLUDED.bola_3, bola_4 = EXCLUDED.bola_4,
                            bola_5 = EXCLUDED.bola_5, bola_6 = EXCLUDED.bola_6,
                            bola_7 = EXCLUDED.bola_7, bola_8 = EXCLUDED.bola_8,
                            bola_9 = EXCLUDED.bola_9, bola_10 = EXCLUDED.bola_10,
                            bola_11 = EXCLUDED.bola_11, bola_12 = EXCLUDED.bola_12,
                            bola_13 = EXCLUDED.bola_13, bola_14 = EXCLUDED.bola_14,
                            bola_15 = EXCLUDED.bola_15
                    """, (concurso, data, *bolas))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(f"✅ Concurso {concurso} salvo com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro: {e}")
    
    else:
        st.info("📂 Para importar planilha, use o alimentar.py no terminal.")

with tab4:
    st.header("📋 Últimos Sorteios")
    
    conn = conectar()
    df_ultimos = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso DESC LIMIT 20", conn)
    conn.close()
    
    for _, row in df_ultimos.iterrows():
        bolas = [int(row[f'bola_{i}']) for i in range(1, 16)]
        with st.expander(f"Concurso {int(row['concurso'])} - {row['data']}"):
            st.write(f"**Números:** {bolas}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✏️ Editar", key=f"edit_{row['concurso']}"):
                    st.info("Edição será implementada em breve")
            with col2:
                if st.button(f"🗑️ Excluir", key=f"del_{row['concurso']}"):
                    conn = conectar()
                    cur = conn.cursor()
                    cur.execute(f"DELETE FROM sorteios WHERE concurso = {int(row['concurso'])}")
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(f"🗑️ Concurso {int(row['concurso'])} excluído!")
                    st.rerun()

st.markdown("---")