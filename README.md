# 🎯 Lotofácil - Sistema Inteligente de Análise Estatística

Sistema completo para análise estatística da Lotofácil com geração inteligente de palpites.

## 🚀 Funcionalidades

- 🎲 **Gerador Inteligente** — Gera jogos otimizados baseado no orçamento
- 📊 **Análise Completa** — Frequência, atraso, pares, soma, ímpares/pares
- 📥 **Alimentador** — Cadastro manual de resultados
- 📋 **Histórico** — Visualização e gerenciamento dos concursos

## 🛠️ Tecnologias

Python, Streamlit, PostgreSQL, Pandas, NumPy, Plotly, SciPy

## 📦 Como usar

```bash
git clone https://github.com/Joaomarini86/lotofacil.git
cd lotofacil
cp config_example.py config.py
# Edite config.py com seus dados do PostgreSQL
pip install -r requirements.txt
streamlit run lotofacil_app.py
