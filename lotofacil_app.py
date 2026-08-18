# lotofacil_app.py - Streamlit App Completo (Refatorado)
import streamlit as st
import psycopg2
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from config import DB_CONFIG, COLUNAS_BOLAS_DB, TOTAL_NUMEROS

# Importações dos módulos de análise
from analise.frequencia import calcular_frequencias
from analise.atraso import calcular_atrasos
from analise.impares_pares import analisar_impares_pares
from analise.soma_total import analisar_soma

PRECOS = {15: 3.50, 16: 56.00, 17: 476.00}

# ==========================================
# FUNÇÕES DE BANCO E LÓGICA
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
    
    # ---------------------------------------------------------
    # NOVO: CÁLCULO DO CICLO DAS DEZENAS
    # ---------------------------------------------------------
    # Pegamos os últimos 30 concursos e lemos do mais antigo para o mais novo
    df_recentes = df.head(30).iloc[::-1]
    ciclo_atual = set()
    
    for _, r in df_recentes.iterrows():
        bolas_sorteio = set([int(r[c]) for c in COLUNAS_BOLAS_DB])
        ciclo_atual.update(bolas_sorteio)
        if len(ciclo_atual) == 25:
            ciclo_atual = set() # O ciclo fechou! Reseta para começar o próximo
            
    dezenas_faltantes_ciclo = sorted(list(set(range(1, 26)) - ciclo_atual))
    
    # Se a lista estiver vazia, significa que o ciclo acabou de fechar no último concurso
    if not dezenas_faltantes_ciclo:
        dezenas_faltantes_ciclo = list(range(1, 26))
        status_ciclo = "Ciclo fechou no último concurso! Todos os 25 números iniciam um novo ciclo."
    else:
        status_ciclo = f"Faltam {len(dezenas_faltantes_ciclo)} números para fechar o ciclo."

    # ---------------------------------------------------------
    # CÁLCULO DOS SCORES (Agora com Bônus de Ciclo)
    # ---------------------------------------------------------
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
        
        bonus_ultimo = 0.20 if num in ultimos_numeros else 0.0
        
        # Bônus VIP se o número for um dos que faltam para fechar o ciclo
        bonus_ciclo = 0.40 if num in dezenas_faltantes_ciclo and len(dezenas_faltantes_ciclo) < 25 else 0.0
        
        # A fórmula agora leva em conta a urgência do ciclo
        scores[num] = (freq * 0.30) + ((1 - 0.4**atraso) * 0.50) + bonus_ultimo + bonus_ciclo
    
    return scores, ultimos_numeros, len(df), label, dezenas_faltantes_ciclo, status_ciclo

def gerar_jogo_com_fadiga(scores_dinamicos, semente_base, fator_fadiga=0.7):
    """
    Gera um jogo aplicando filtros com margem de respiro para evitar overfitting:
    Paridade, Moldura (8-12), Primos (4-7), Fibonacci (3-6), Soma e Limite de Sequência.
    """
    np.random.seed(semente_base)
    dezenas = list(scores_dinamicos.keys())
    
    # Conjuntos Matemáticos Fixos
    DEZENAS_MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
    DEZENAS_PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
    DEZENAS_FIBONACCI = {1, 2, 3, 5, 8, 13, 21}
    
    while True:
        pesos = list(scores_dinamicos.values())
        soma_pesos = sum(pesos)
        probs = [p / soma_pesos for p in pesos] if soma_pesos > 0 else None
        
        sorteio = np.random.choice(dezenas, size=15, replace=False, p=probs)
        jogo_candidato = sorted([int(x) for x in sorteio])
        jogo_set = set(jogo_candidato) 
        
        # ---------------------------------------------------------
        # FILTROS FLEXIBILIZADOS (Buscando o teto de 14/15 pontos)
        # ---------------------------------------------------------
        
        # 1. PARIDADE (Mantida: 7, 8 ou 9 ímpares)
        qtd_impares = sum(1 for n in jogo_candidato if n % 2 != 0)
        if qtd_impares not in [7, 8, 9]: continue 
            
        # 2. MOLDURA (Expandida: De 8 a 12 dezenas na borda)
        qtd_moldura = len(jogo_set.intersection(DEZENAS_MOLDURA))
        if not (8 <= qtd_moldura <= 12): continue
            
        # 3. PRIMOS (Expandida: De 4 a 7 números primos)
        qtd_primos = len(jogo_set.intersection(DEZENAS_PRIMOS))
        if not (4 <= qtd_primos <= 7): continue
            
        # 4. FIBONACCI (Expandida: De 3 a 6 números de Fibonacci)
        qtd_fibo = len(jogo_set.intersection(DEZENAS_FIBONACCI))
        if not (3 <= qtd_fibo <= 6): continue
            
        # 5. SOMA HISTÓRICA (Mantida: 159 a 231)
        soma_jogo = sum(jogo_candidato)
        if not (159 <= soma_jogo <= 231): continue 
            
        # 6. LIMITE DE SEQUÊNCIA MÁXIMA (Mantida: Escudo Anti-Anomalia Extrema)
        maior_seq = 1
        seq_atual = 1
        for i in range(1, len(jogo_candidato)):
            if jogo_candidato[i] == jogo_candidato[i-1] + 1:
                seq_atual += 1
                if seq_atual > maior_seq:
                    maior_seq = seq_atual
            else:
                seq_atual = 1
                
        # Continua barrando tripas maiores que 8 números
        if maior_seq > 8: 
            continue
            
        # ---------------------------------------------------------
        # JOGO APROVADO! Aplicação do Fator de Fadiga
        # ---------------------------------------------------------
        for num in jogo_candidato:
            scores_dinamicos[num] *= fator_fadiga
            
        return jogo_candidato

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
# Carregar dados
scores, ultimos, total, label, dezenas_faltantes, status_ciclo = carregar_dados(janela)

# ==========================================
# ABAS DO APP
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["🎲 Gerador", "📊 Análise", "📥 Alimentar", "📋 Resultados"])

with tab1:
    st.header("🎲 Gerador Inteligente de Palpites")

    # NOVO: Painel de Aviso do Ciclo
    if len(dezenas_faltantes) < 25:
        st.warning(f"🔄 **Atenção ao Ciclo:** {status_ciclo}\n\n**Dezenas:** {dezenas_faltantes}")
    else:
        st.info(f"🔄 **Ciclo:** {status_ciclo}")
    
    col1, col2 = st.columns(2)
    with col1:
        orcamento = st.number_input("💰 Quanto gastar? (R$)", min_value=3.50, max_value=10000.0, value=20.0, step=1.0)
    with col2:
        st.write(f"📊 Base: **{label}** ({total} sorteios)")
        st.write(f"🎱 Último sorteio: **{ultimos}**")
    
    # CALCULAMOS AS OPÇÕES DIRETAMENTE BASEADO NO ORÇAMENTO
    opcoes = calcular_opcoes(orcamento)
    
    st.subheader("🎯 Estratégias disponíveis:")
    for op in opcoes:
        economia = int(orcamento) - op['total']
        st.write(f"   **{op['id']}** - {op['label']} = R$ {op['total']:.2f} (sobra: R$ {economia:.2f})")
    
    opcao_id = st.selectbox("Escolha a estratégia:", [o['id'] for o in opcoes], 
                            format_func=lambda x: [o['label'] for o in opcoes if o['id'] == x][0])
    
    # APENAS UM BOTÃO DE AÇÃO
    if st.button("🚀 Confirmar e Gerar Jogos", type="primary"):
        escolhida = [o for o in opcoes if o['id'] == opcao_id][0]
        
        jogos = []
        import time
        semente = int(time.time())
        
        # Cria uma cópia dos scores para que a fadiga atue apenas neste lote
        scores_dinamicos = scores.copy()
        
        for _ in range(escolhida['qtd_17']):
            jogo = gerar_jogo_com_fadiga(scores_dinamicos, semente)
            semente += 1
            extras = [n for n in range(1, 26) if n not in jogo]
            extras.sort(key=lambda x: scores_dinamicos[x], reverse=True)
            jogo_final = sorted(jogo + extras[:2])
            
            # Aplica fadiga também nas dezenas extras escolhidas
            for ex in extras[:2]:
                scores_dinamicos[ex] *= 0.7
                
            jogos.append({'tipo': 17, 'numeros': jogo_final, 'preco': PRECOS[17]})
        
        for _ in range(escolhida['qtd_16']):
            jogo = gerar_jogo_com_fadiga(scores_dinamicos, semente)
            semente += 1
            extras = [n for n in range(1, 26) if n not in jogo]
            extras.sort(key=lambda x: scores_dinamicos[x], reverse=True)
            jogo_final = sorted(jogo + [extras[0]])
            
            # Aplica fadiga na dezena extra
            scores_dinamicos[extras[0]] *= 0.7
            
            jogos.append({'tipo': 16, 'numeros': jogo_final, 'preco': PRECOS[16]})
        
        for i in range(escolhida['qtd_15']):
            jogo = gerar_jogo_com_fadiga(scores_dinamicos, semente + i)
            jogos.append({'tipo': 15, 'numeros': jogo, 'preco': PRECOS[15]})
        
        st.success(f"✅ {len(jogos)} jogos gerados! Total: R$ {sum(j['preco'] for j in jogos):.2f}")
        
        for i, jogo in enumerate(jogos, 1):
            repete = len(set(jogo['numeros']) & set(ultimos))
            imp = sum(1 for n in jogo['numeros'] if n % 2 == 1)
            soma = sum(jogo['numeros'])
            with st.expander(f"🎯 Jogo {i} ({jogo['tipo']} números - R$ {jogo['preco']:.2f})"):
                st.write(f"**Números:** {jogo['numeros']}")
                st.write(f"Repete do último: {repete} | Ímpares: {imp} | Pares: {jogo['tipo'] - imp} | Soma: {soma}")

with tab2:
    st.header("📊 Análise Estatística Completa")
    
    # --- 1. Frequência ---
    st.subheader("📈 Frequência dos Números")
    dados_freq = calcular_frequencias() 
    df_freq = pd.DataFrame(dados_freq['resultados'])
    df_freq['%'] = df_freq['freq_relativa'].astype(str) + '%'
    
    fig_freq = px.bar(df_freq, x='numero', y='freq_absoluta', text='%', 
                 title='Frequência de cada número da Lotofácil',
                 color='freq_absoluta', color_continuous_scale='Viridis',
                 labels={'numero': 'Número', 'freq_absoluta': 'Frequência'})
    st.plotly_chart(fig_freq, use_container_width=True)
    
    # --- 2. Atraso ---
    st.subheader("⏰ Atraso Atual")
    dados_atraso = calcular_atrasos() 
    df_atraso = pd.DataFrame(dados_atraso)
    df_atraso['Probabilidade'] = df_atraso['prob_atraso'].astype(str) + '%'
    
    fig_atraso = px.bar(df_atraso, x='numero', y='atraso', text='Probabilidade',
                 title='Atraso atual (sorteios sem sair)',
                 color='atraso', color_continuous_scale='Reds',
                 labels={'numero': 'Número', 'atraso': 'Atraso'})
    st.plotly_chart(fig_atraso, use_container_width=True)
    
    # --- 3. Ímpares x Pares ---
    st.subheader("📊 Distribuição Ímpares x Pares")
    distribuicao, total_sorteios = analisar_impares_pares() 
    
    imp_par_data = []
    for (imp, par), count in sorted(distribuicao.items()):
        imp_par_data.append({'Ímpares': imp, 'Pares': par, 'Vezes': count, '%': f"{count/total_sorteios*100:.1f}%"})
    
    df_ip = pd.DataFrame(imp_par_data)
    fig_ip = px.bar(df_ip, x='Ímpares', y='Vezes', text='%',
                 title='Distribuição de Ímpares x Pares nos sorteios',
                 color='Vezes', color_continuous_scale='Blues')
    st.plotly_chart(fig_ip, use_container_width=True)
    
    # --- 4. Soma ---
    st.subheader("📈 Distribuição da Soma dos Números")
    dados_soma = analisar_soma() 
    somas = dados_soma['somas']
    media = dados_soma['media']
    dp = dados_soma['dp']
    
    fig_soma = go.Figure()
    fig_soma.add_trace(go.Histogram(x=somas, nbinsx=30, name='Somas', marker_color='green'))
    fig_soma.add_vline(x=media, line_dash="dash", line_color="red", annotation_text=f"Média: {media:.0f}")
    fig_soma.add_vline(x=media - dp, line_dash="dot", line_color="orange", annotation_text=f"-1σ: {media-dp:.0f}")
    fig_soma.add_vline(x=media + dp, line_dash="dot", line_color="orange", annotation_text=f"+1σ: {media+dp:.0f}")
    fig_soma.update_layout(title=f"Distribuição da Soma (média: {media:.1f}, DP: {dp:.1f})")
    st.plotly_chart(fig_soma, use_container_width=True)

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