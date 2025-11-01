"""Interface Streamlit para NFe Processor Agent."""

import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.express as px

from config.configuration import (
    STREAMLIT_TITLE,
    STREAMLIT_ICON,
    STREAMLIT_LAYOUT,
    LLMProvider
)
from src.agents.nf_agent import NFAgentIntelligent
from src.agents.chat_agent import ChatAssistant
from src.database.connection import get_all_notas, get_connection, init_db
from logs.logger import app_logger


# =====================================================
# INICIALIZAR BANCO DE DADOS
# =====================================================
try:
    init_db()
except Exception as e:
    app_logger.warning(f"⚠️  Aviso ao inicializar banco: {e}")


# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(
    page_title=STREAMLIT_TITLE,
    page_icon=STREAMLIT_ICON,
    layout=STREAMLIT_LAYOUT,
    initial_sidebar_state="expanded"
)

# =====================================================
# PLOTLY CONFIG
# =====================================================
plotly_config = {
    'displayModeBar': False,
    'showLink': False
}

# =====================================================
# INICIALIZAÇÃO DE SESSION STATE
# =====================================================
if 'llm_configured' not in st.session_state:
    st.session_state.llm_configured = False
    st.session_state.llm_provider = None
    st.session_state.llm_api_key = None
    st.session_state.agent = None
    st.session_state.chat_assistant = None
    st.session_state.chat_history = []


# =====================================================
# SIDEBAR - CONFIGURAÇÃO LLM
# =====================================================
with st.sidebar:
    st.header("⚙️ Configurações")
    
    st.subheader("🤖 Configuração do LLM")
    
    # Seletor de Provider
    provider_options = [p.value for p in LLMProvider]
    provider_names = {p.value: str(LLMProvider(p)) for p in LLMProvider}
    
    selected_provider = st.selectbox(
        "Provedor de LLM",
        options=provider_options,
        format_func=lambda x: provider_names[x],
        help="Escolha o provedor de LLM (modelo padrão será usado automaticamente)"
    )
    
    # Input de API Key
    api_key_input = st.text_input(
        "API Key",
        type="password",
        help="Insira sua API key do provedor selecionado"
    )
    
                # Botão de configurar
    if st.button("✅ Configurar LLM", use_container_width=True):
        if api_key_input:
            try:
                # Inicializar agente (sem passar model)
                st.session_state.agent = NFAgentIntelligent(
                    llm_provider=selected_provider,
                    api_key=api_key_input
                )
                
                # Inicializar chat assistant (sem passar model)
                st.session_state.chat_assistant = ChatAssistant(
                    llm_provider=selected_provider,
                    api_key=api_key_input
                )
                
                st.session_state.llm_configured = True
                st.session_state.llm_provider = selected_provider
                st.session_state.llm_api_key = api_key_input
                
                st.success("✅ LLM configurado com sucesso!")
                app_logger.info(f"LLM configurado: {selected_provider}")
                
            except Exception as e:
                st.error(f"❌ Erro ao configurar LLM: {e}")
        else:
            st.warning("⚠️ Por favor, insira a API Key")
    
    # Status da configuração
    st.divider()
    if st.session_state.llm_configured:
        st.success("🟢 LLM Configurado")
        st.caption(f"Provider: {st.session_state.llm_provider}")
    else:
        st.warning("🔴 LLM não configurado")
        st.caption("Configure o LLM para começar")


# =====================================================
# MAIN - TABS PRINCIPAIS
# =====================================================

st.title(f"{STREAMLIT_ICON} NFe Processor Agent")
st.caption("Processamento inteligente de Notas Fiscais com IA")

# Verificar se LLM está configurado
if not st.session_state.llm_configured:
    st.warning("⚠️ Configure o LLM na barra lateral para começar")
    st.info("""
    **Como começar:**
    1. Escolha um provedor de LLM (OpenAI, Groq, Claude, Gemini)
    2. Selecione o modelo desejado
    3. Insira sua API Key
    4. Clique em "Configurar LLM"
    """)
    st.stop()

# Tabs principais
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Processar",
    "📊 Dashboard",
    "💬 Chat Assistant",
    "📜 Histórico"
])


# =====================================================
# TAB 1 - PROCESSAR NOTAS
# =====================================================

with tab1:
    st.header("📤 Processar Notas Fiscais")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload de Arquivos")
        uploaded_files = st.file_uploader(
            "Selecione arquivos XML",
            type=["xml"],
            accept_multiple_files=True,
            help="Você pode selecionar múltiplos arquivos"
        )
    
    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} arquivo(s) selecionado(s)")
        
        if st.button("🚀 Processar Arquivos", use_container_width=True, type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_files = len(uploaded_files)
            resultados = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                # Atualizar progresso
                progress = (idx + 1) / total_files
                progress_bar.progress(progress)
                status_text.text(f"Processando {uploaded_file.name}...")
                
                # Salvar arquivo temporariamente
                temp_path = Path("data/temp") / uploaded_file.name
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Processar arquivo (sem passar model)
                try:
                    result = st.session_state.agent.processar(
                        str(temp_path),
                        llm_provider=st.session_state.llm_provider,
                        api_key=st.session_state.llm_api_key
                    )
                    resultados.append(result)
                    
                except Exception as e:
                    st.error(f"❌ Erro ao processar {uploaded_file.name}: {e}")
                
                # Limpar arquivo temporário
                temp_path.unlink()
            
            # Mostrar resultados
            status_text.text("✅ Processamento concluído!")
            
            st.success(f"✅ {len(uploaded_files)} arquivo(s) processado(s)")
            
            print("Resultados do processamento: ", resultados)
            
            # Resumo
            total_notas = sum(len(r['notas_processadas']) for r in resultados)
            total_erros = sum(len(r['erros']) for r in resultados)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Arquivos", len(uploaded_files))
            col2.metric("Notas Processadas", total_notas)
            col3.metric("Erros", total_erros)
            
            # Detalhes
            with st.expander("📋 Ver Detalhes"):
                for result in resultados:
                    for nf in result['notas_processadas']:
                        st.write(f"**NF {nf.get('numero_nf')}**")
                        st.write(f"- Status: {nf.get('status')}")
                        st.write(f"- Valor: R$ {nf.get('valor_total', 0):.2f}")
                        

# =====================================================
# TAB 2 - DASHBOARD
# =====================================================

with tab2:
    st.header("📊 Dashboard de Notas Fiscais")
    
    # Carregar dados
    try:
        notas = get_all_notas()
        
        if not notas:
            st.info("📭 Nenhuma nota processada ainda. Faça upload de arquivos na aba 'Processar'.")
        else:
            df = pd.DataFrame(notas)
            print("DataFrame de notas:", df)
                        
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Notas", len(df))
            
            with col2:
                valor_total = df['valor_total'].sum()
                valor_formatado = f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                st.metric("Valor Total", valor_formatado)
            
            with col3:
                notas_validas = len(df[df['status'] == 'Autorizado'])
                st.metric("Notas Válidas", notas_validas)
            
            with col4:
                notas_erro = len(df[df['status'] == 'Reprovado'])
                st.metric("Com Erros", notas_erro)
            
            st.divider()
            
            st.header("📊 Classificação das Notas Processadas")
            st.subheader("📦 Produtos")
            df_products = df[df['classificacao'] == 'Produto']
            nf_products_total = df_products.shape[0]
            nf_products_authorized = df_products[df_products['status'] == 'Autorizado'].shape[0]
            nf_products_rejected = df_products[df_products['status'] == 'Reprovado'].shape[0]
            
            pct_success_prod = (nf_products_authorized / nf_products_total) * 100 if nf_products_total > 0 else 0
            pct_rejected_prod = (nf_products_rejected / nf_products_total) * 100 if nf_products_total > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="📦 Total de Notas",
                    value=f"{nf_products_total:,}".replace(",", ".")
                )
            with col2:
                st.metric(
                    label="✅ Autorizadas",
                    value=f"{nf_products_authorized:,}".replace(",", "."),
                    delta=f"{pct_success_prod:.1f}% (Sucesso)",
                    delta_color="normal"
                )
            with col3:
                st.metric(
                    label="❌ Rejeitadas",
                    value=f"{nf_products_rejected:,}".replace(",", "."),
                    delta=f"{pct_rejected_prod:.1f}% (Rejeição)",
                    delta_color="inverse"
                )
            
                   
            st.subheader("🛠️ Serviços")
            df_service = df[df['classificacao'] == 'Serviço']
            nf_service_total = df_service.shape[0]
            nf_services_authorized = df_service[df_service['status'] == 'Autorizado'].shape[0]
            nf_services_rejected = df_service[df_service['status'] == 'Reprovado'].shape[0]  
            
            pct_success_serv = (nf_services_authorized / nf_service_total) * 100 if nf_service_total > 0 else 0
            pct_rejected_serv = (nf_services_rejected / nf_service_total) * 100 if nf_service_total > 0 else 0
            col4, col5, col6 = st.columns(3)
            with col4:
                st.metric(
                    label="🛠️ Total Notas",
                    value=f"{nf_service_total:,}".replace(",", ".")
                )
            with col5:
                st.metric(
                    label="✅ Autorizadas",
                    value=f"{nf_services_authorized:,}".replace(",", "."),
                    delta=f"{pct_success_serv:.1f}% (Sucesso)",
                    delta_color="normal"
                )
            with col6:
                st.metric(
                    label="❌ Rejeitadas",
                    value=f"{nf_services_rejected:,}".replace(",", "."),
                    delta=f"{pct_rejected_serv:.1f}% (Rejeição)",
                    delta_color="inverse"
                )
            
            st.divider()
            
            # Impostos
            st.subheader("💰 Impostos por Tipo")
            
            conn = get_connection()
            impostos_df = pd.read_sql_query("""
                SELECT tipo_imposto, SUM(valor_imposto) as total
                FROM impostos
                GROUP BY tipo_imposto
            """, conn)
            conn.close()
            
            if not impostos_df.empty:
                fig_impostos = px.bar(
                    impostos_df,
                    x='tipo_imposto',
                    y='total',
                    title='Total de Impostos por Tipo',
                    labels={'tipo_imposto': 'Tipo', 'total': 'Valor (R$)'}
                )
                st.plotly_chart(fig_impostos, config=plotly_config, use_container_width=True)
            
            # Tabela de notas
            st.subheader("✅ Notas Processadas e Aprovadas para Emissão")
            df_mapped = {
                'numero_nf': 'Número',
                'serie': 'Serie',
                'data_emissao': 'Data Emissão',
                'valor_total': 'Valor',
                'status': 'Status',
                'classificacao': 'Classificação',
                'chave_nfe': 'Chave NFe',
                'protocolo_sefaz': 'Protocolo SEFAZ',
                'data_autorizacao': 'Data Autorização'
            }
            df_notes = df[df['status'] == 'Autorizado'].copy()
            df_notes = df_notes.rename(columns=df_mapped)
            approved_notes = list(df_mapped.values())
            df_notes_final = df_notes[approved_notes]
            st.dataframe(df_notes_final, use_container_width=True)
            
            st.subheader("❌ Notas Processadas e Reprovadas")
            df_service_mapped = {
                'numero_nf': 'Número',
                'serie': 'Serie',
                'data_emissao': 'Data Emissão',
                'valor_total': 'Valor',
                'status': 'Status',
                'mensagem_erro': 'Motivo de Reprovação',
                'classificacao': 'Classificação',
                'chave_nfe': 'Chave NFe',
                'protocolo_sefaz': 'Protocolo SEFAZ',
                'data_autorizacao': 'Data Autorização'
            }
            df_notes_service = df[df['status'] == 'Reprovado'].copy()
            df_notes_service = df_notes_service.rename(columns=df_service_mapped)
            df_service_notes = list(df_service_mapped.values())
            df_notes_service_final = df_notes_service[df_service_notes]
            st.dataframe(df_notes_service_final, use_container_width=True)
            
            for index, row in df_notes_service_final.iterrows():
                nf_num = row['Número']
                mensagem = row['Motivo de Reprovação']

                expander_title = f"Número da NF Reprovada {nf_num}"
                
                with st.expander(expander_title, expanded=False):
                    st.markdown("---")
                    st.error("Detalhes do Erro abaixo:")
                    st.code(mensagem, language='text')
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")


# =====================================================
# TAB 3 - CHAT ASSISTANT
# =====================================================

with tab3:
    st.header("💬 Chat Assistant")
    st.caption("Faça perguntas sobre suas notas fiscais")
    
    # Container para o chat
    chat_container = st.container()
    
    # Mostrar histórico
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                with st.chat_message("user"):
                    st.write(message['content'])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(message['content'])
    
    # Input do usuário
    user_input = st.chat_input("Digite sua pergunta...")
    
    if user_input:
        # Adicionar mensagem do usuário
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Processar com chat assistant
        with st.spinner("🤔 Pensando..."):
            try:
                response = st.session_state.chat_assistant.chat(user_input)
                
                # Adicionar resposta do assistente
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response
                })
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro no chat: {e}")
    
    # Botão para limpar histórico
    if st.button("🗑️ Limpar Conversa"):
        st.session_state.chat_history = []
        if st.session_state.chat_assistant:
            st.session_state.chat_assistant.reset_conversation()
        st.rerun()


# =====================================================
# TAB 4 - HISTÓRICO
# =====================================================

with tab4:
    st.header("📜 Histórico de Processamento")
    
    try:
        notas = get_all_notas()
        
        if not notas:
            st.info("📭 Nenhuma nota no histórico")
        else:
            df = pd.DataFrame(notas)
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.multiselect(
                    "Status",
                    options=df['status'].unique(),
                    default=df['status'].unique()
                )
            
            with col2:
                classificacao_filter = st.multiselect(
                    "Classificação",
                    options=df['classificacao'].unique(),
                    default=df['classificacao'].unique()
                )
            
            with col3:
                tipo_filter = st.multiselect(
                    "Tipo",
                    options=df['tipo_nf'].unique(),
                    default=df['tipo_nf'].unique()
                )
            
            # Aplicar filtros
            df_filtered = df[
                (df['status'].isin(status_filter)) &
                (df['classificacao'].isin(classificacao_filter)) &
                (df['tipo_nf'].isin(tipo_filter))
            ]
            
            # Mostrar tabela completa
            st.dataframe(
                df_filtered,
                use_container_width=True,
                height=400
            )
            
            # Download CSV
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name="notas_fiscais.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar histórico: {e}")


# =====================================================
# FOOTER
# =====================================================

st.divider()
st.caption("🤖 NFe Processor Agent - Powered by AgenteFin Group ")