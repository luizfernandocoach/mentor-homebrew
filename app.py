import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components
import time
import os

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(
    page_title="Mentor AI | Homebrew",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta
COR_LARANJA = "#FF4D00"
COR_FUNDO = "#0E1117"
COR_SIDEBAR = "#262730"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp {{ background-color: {COR_FUNDO}; font-family: 'Inter', sans-serif; }}
    h1, h2, h3 {{ color: white !important; font-weight: 800 !important; }}
    .highlight-orange {{ color: {COR_LARANJA} !important; }}
    div.stButton > button {{
        background-color: {COR_LARANJA}; color: white; border: none; border-radius: 4px;
        padding: 0.5rem 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;
        transition: all 0.3s ease; width: 100%;
    }}
    div.stButton > button:hover {{ background-color: #CC3D00; border: 1px solid white; }}
    .stTextInput > div > div > input {{ background-color: #1E1E1E; color: white; border: 1px solid #333; }}
    .stTextInput > div > div > input:focus {{ border-color: {COR_LARANJA}; }}
    section[data-testid="stSidebar"] {{ background-color: {COR_SIDEBAR}; border-right: 1px solid #333; }}
    .stChatMessage {{ background-color: transparent; border-bottom: 1px solid #333; }}
    div[data-testid="stToast"] {{ background-color: {COR_LARANJA}; color: white; }}
    
    /* Ajuste para Mobile: Espaço extra no fim para o teclado não cobrir tudo */
    .stChatInput {{ padding-bottom: 20px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. GESTÃO DE ACESSO ---
USUARIOS = {
    "admin": "homebrew", 
    "beta": "treino2025"
}

# --- 3. FUNÇÕES TÉCNICAS ---
def check_password():
    if st.session_state.get("logged_in"): return True
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown(f"<h1 style='text-align: center; color: {COR_LARANJA};'>MENTOR <span style='color:white'>AI</span></h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray; margin-bottom: 30px;'>Acesso Beta Restrito</p>", unsafe_allow_html=True)
        with st.container(border=True):
            u = st.text_input("USUÁRIO", placeholder="beta")
            p = st.text_input("SENHA", type="password", placeholder="••••••")
            st.markdown(" ")
            if st.button("ACESSAR SISTEMA ⚡"):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state["logged_in"] = True
                    st.rerun()
                else: st.error("DADOS INCORRETOS.")
    return False

def configure_api():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("ERRO: API KEY ausente nos Secrets.")
        st.stop()
    return api_key

def get_best_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name
        return 'models/gemini-1.5-flash'
    except: return 'models/gemini-1.5-flash'

# Função para fechar o teclado no celular
def dismiss_keyboard():
    components.html("""
        <script>
            var input = window.parent.document.querySelector("textarea[data-testid='stChatInputTextArea']");
            if (input) { input.blur(); }
        </script>
    """, height=0, width=0)

@st.cache_resource
def load_multiple_files(api_key):
    genai.configure(api_key=api_key)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files_dir = os.path.join(current_dir, "files")
    
    if not os.path.exists(files_dir): return None, "Pasta 'files' não encontrada."
    pdf_files = [f for f in os.listdir(files_dir) if f.lower().endswith('.pdf')]
    if not pdf_files: return None, "Biblioteca vazia."

    uploaded_refs = []
    my_bar = st.progress(0, text="Sincronizando Base de Conhecimento...")

    for i, filename in enumerate(pdf_files):
        file_path = os.path.join(files_dir, filename)
        try:
            file_ref = genai.upload_file(file_path, mime_type="application/pdf")
            ready = False
            for _ in range(15):
                if file_ref.state.name == "ACTIVE":
                    ready = True
                    break
                if file_ref.state.name == "FAILED": break
                time.sleep(1)
                file_ref = genai.get_file(file_ref.name)
            if ready: uploaded_refs.append(file_ref)
        except: pass
        my_bar.progress((i + 1) / len(pdf_files), text=f"Indexando: {filename}")

    my_bar.empty()
    return uploaded_refs, None

# --- 4. APLICAÇÃO ---
if check_password():
    api_key = configure_api()

    with st.sidebar:
        st.markdown(f"<h2 style='color:{COR_LARANJA}; margin-bottom:0;'>HOMEBREW</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 12px; color: gray; letter-spacing: 2px;'>BETA TESTER</p>", unsafe_allow_html=True)
        st.divider()
        st.markdown("### STATUS")
        if "library_refs" in st.session_state and st.session_state["library_refs"]:
            st.success(f"● ONLINE | {len(st.session_state['library_refs'])} Livros")
        else: st.warning("○ CARREGANDO...")
        
        if st.button("LIMPAR CHAT 🗑️"):
            st.session_state.messages = []
            st.rerun()
        if st.button("SAIR"): 
            st.session_state["logged_in"] = False
            st.rerun()

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(f"<h1 style='margin-bottom: 0;'>MENTOR <span class='highlight-orange'>AI</span></h1>", unsafe_allow_html=True)
        st.caption("Especialista em Fisiologia & Treinamento Baseado em Evidência")
    
    if "library_refs" not in st.session_state or not st.session_state["library_refs"]:
        with st.spinner("Conectando aos livros (Schoenfeld, IUSCA)..."):
            refs, err = load_multiple_files(api_key)
            if refs: st.session_state["library_refs"] = refs
            else: st.error("Erro na base de dados.")

    chat_container = st.container()

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Olá! Acesso Beta liberado. Minha base de dados (Hipertrofia & Glúteos) está ativa. Qual sua dúvida técnica?"}]

    with chat_container:
        for msg in st.session_state.messages:
            avatar = "⚡" if msg["role"] == "assistant" else "👤"
            st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

    if prompt := st.chat_input("Pergunte ao Mentor..."):
        # 1. Adiciona pergunta do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user", avatar="👤").write(prompt)

        # 2. Tenta fechar o teclado (Mobile Hack)
        dismiss_keyboard()

        # 3. Resposta com STREAMING (Efeito de Digitação)
        with st.chat_message("assistant", avatar="⚡"):
            library = st.session_state.get("library_refs")
            if library:
                try:
                    # Aviso visual rápido antes de começar a escrever
                    status_placeholder = st.empty()
                    status_placeholder.markdown("`Consultando biblioteca...`")
                    
                    model_name = get_best_model()
                    system_prompt = """
                    Você é um Mentor Sênior de Educação Física.
                    Responda de forma direta, técnica e baseada APENAS nos arquivos fornecidos.
                    Sempre cite a fonte (ex: 'Segundo Schoenfeld...', 'Tabela 2 da IUSCA').
                    """
                    model = genai.GenerativeModel(model_name, system_instruction=system_prompt)
                    
                    # ATIVA O STREAMING AQUI
                    response_stream = model.generate_content(library + [prompt], stream=True)
                    
                    # Limpa o aviso de "Consultando"
                    status_placeholder.empty()
                    
                    # Placeholder para o texto que vai surgindo
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    # Loop para escrever em tempo real
                    for chunk in response_stream:
                        if chunk.text:
                            full_response += chunk.text
                            # Atualiza a tela a cada pedaço de texto
                            response_placeholder.markdown(full_response + "▌") 
                    
                    # Remove o cursor '▌' no final
                    response_placeholder.markdown(full_response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("Sistema desconectado.")
