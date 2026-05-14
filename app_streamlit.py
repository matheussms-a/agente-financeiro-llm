# app_streamlit.py
import streamlit as st
import pandas as pd
import json
import tempfile
import os
from extract_transactions import extrair_transacoes_do_pdf
from analyze_expenses import analisar_gastos_com_agente

st.set_page_config(page_title="Agente Financeiro",
                   page_icon="💰", layout="wide")

# 1. Uso de Session State para evitar recarregamentos pesados
if "relatorio" not in st.session_state:
    st.session_state["relatorio"] = None
if "transacoes_extraidas" not in st.session_state:
    st.session_state["transacoes_extraidas"] = None

st.title("💰 Agente Financeiro Pessoal com IA")
st.markdown(
    "Faça upload do seu extrato bancário em PDF e obtenha uma análise completa dos seus gastos.")

uploaded_file = st.file_uploader(
    "Selecione o arquivo PDF do extrato", type="pdf")

# 2. Uso de um botão explícito para iniciar a análise de arquivos grandes
if uploaded_file is not None:
    if st.button("Analisar Extrato", type="primary"):
        # Reseta o estado atual ao iniciar nova análise
        st.session_state["relatorio"] = None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            caminho_pdf = tmp_file.name

        try:
            # 3. st.status fornece um feedback visual muito melhor para processos longos
            with st.status("Processando documento de texto...", expanded=True) as status:

                st.write(
                    "🔍 Lendo PDF e extraindo transações (isso pode demorar em arquivos de 90 dias)...")
                transacoes = extrair_transacoes_do_pdf(caminho_pdf)

                if not transacoes:
                    status.update(
                        label="Nenhuma transação encontrada.", state="error")
                    st.stop()

                st.session_state["transacoes_extraidas"] = transacoes
                st.write(
                    f"✅ Extração concluída: {len(transacoes)} transações identificadas.")

                st.write("🧠 Enviando para análise da IA (DeepSeek)...")
                relatorio = analisar_gastos_com_agente(transacoes)

                # Validação do formato JSON
                if isinstance(relatorio, str):
                    try:
                        relatorio = json.loads(relatorio)
                    except json.JSONDecodeError:
                        status.update(
                            label="Erro de formatação da IA.", state="error")
                        st.error(
                            "A resposta da IA não está em formato JSON válido.")
                        st.text_area("Resposta bruta", relatorio, height=200)
                        st.stop()

                st.session_state["relatorio"] = relatorio
                status.update(label="Análise concluída com sucesso!",
                              state="complete", expanded=False)

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")
        finally:
            if os.path.exists(caminho_pdf):
                os.remove(caminho_pdf)

# 4. Renderização baseada no Session State (não se perde se a página atualizar)
if st.session_state["relatorio"] is not None:
    relatorio = st.session_state["relatorio"]

    if "erro" in relatorio:
        st.error(relatorio["erro"])
        if "resposta_bruta" in relatorio:
            st.text_area("Resposta bruta do modelo",
                         relatorio["resposta_bruta"], height=200)
    else:
        # Dividindo em abas para organizar melhor grandes volumes de dados
        st.divider()
        st.subheader("Resultados da Análise")
        tab1, tab2, tab3 = st.tabs(
            ["📊 Resumo e Insights", "📋 Todas as Transações", "🔄 Recorrências"])

        with tab1:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown("**Resumo por Categoria**")
                resumo = relatorio.get("resumo_por_categoria")
                if isinstance(resumo, dict) and resumo:
                    try:
                        df_resumo = pd.DataFrame(
                            list(resumo.items()),
                            columns=["Categoria", "Total (R$)"]
                        ).sort_values("Total (R$)", ascending=False)

                        # Correção essencial: Força a conversão para número numérico.
                        # Evita que o Streamlit quebre se a IA retornar string nos valores ("100,00").
                        df_resumo["Total (R$)"] = pd.to_numeric(
                            df_resumo["Total (R$)"].astype(
                                str).str.replace(',', '.'),
                            errors='coerce'
                        )

                        st.dataframe(df_resumo, use_container_width=True)
                        st.bar_chart(df_resumo.set_index("Categoria"))
                    except Exception as e:
                        st.warning(
                            f"Erro ao renderizar o gráfico. Exibindo dados crus: {e}")
                        st.json(resumo)
                else:
                    st.info("Nenhum resumo por categoria.")

            with col2:
                st.markdown("**Insights Financeiros**")
                insights = relatorio.get("insights")
                if isinstance(insights, list) and insights:
                    for insight in insights:
                        st.success(f"💡 {insight}")
                else:
                    st.info("Nenhum insight gerado.")

        with tab2:
            st.markdown(
                f"**Transações Categorizadas ({len(st.session_state['transacoes_extraidas'])} itens)**")
            trans = relatorio.get("transacoes_categorizadas")
            if isinstance(trans, list) and trans:
                st.dataframe(pd.DataFrame(trans), use_container_width=True)
            else:
                st.info("Nenhuma transação categorizada.")

        with tab3:
            st.markdown("**Assinaturas / Cobranças Recorrentes**")
            recorrencias = relatorio.get("recorrencias")
            if isinstance(recorrencias, list) and recorrencias:
                for rec in recorrencias:
                    st.info(f"🔄 {rec}")
            else:
                st.info("Nenhuma recorrência identificada.")

        st.divider()
        with st.expander("🛠️ Modo Debug: Ver JSON original retornado pela IA"):
            st.json(relatorio)
