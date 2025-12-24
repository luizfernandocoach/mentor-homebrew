import streamlit as st
import google.generativeai as genai
import time
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA E CSS (O DESIGN) ---
st.set_page_config(
    page_title="Mentor AI | Homebrew",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de Cores
COR_LARANJA = "#FF4D00"
COR_FUNDO = "#0E1117"
COR_SIDEBAR = "#262730"

# CSS Personalizado (Injeção de Estilo)
st.markdown(f"""
<style>
    /* Importando fonte (opcional, usa sistema por padrão) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Fundo Geral */
    .stApp {{
        background-color: {COR_FUNDO};
        font-family: 'Inter', sans-serif;
    }}

    /* Títulos (H1, H2...) */
    h1, h2, h3 {{
        color: white !important;
        font-weight: 800 !important;
    }}
    
    /* Destaque Laranja para Títulos Específicos */
    .highlight-orange {{
        color: {COR_LARANJA} !important;
    }}

    /* Botões (Estilo Industrial) */
    div.stButton > button {{
        background-color: {COR_LARANJA};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        width: 100%;
    }}
    div.stButton > button:hover {{
        background-color: #CC3D00; /* Laranja mais escuro */
        border: 1px solid white;
    }}

    /* Caixas de Texto (Inputs) */
    .stTextInput > div > div > input {{
        background-color: #1E1E1E;
        color: white;
        border: 1px solid #333;
        border-radius: 4px;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: {COR_LARANJA};
        box-shadow: 0 0 5px {COR_LARANJA};
    }}

    /* Barra Lateral */
    section[data-testid="stSidebar"] {{
        background-color: {COR_SIDEBAR};
        border-right: 1px solid #333;
    }}

    /* Chat Messages */
    .stChatMessage {{
        background-color: transparent;
        border-bottom: 1px solid #333;
    }}
    
    /* Toast (Mensagens flutuantes) */
    div[data-testid="stToast"] {{
        background-color: {COR_LARANJA};
        color: white;
    }}
    
</style>
""", unsafe_allow_html=True)

# --- 2. GESTÃO DE ACESSO ---
USUARIOS = {
    "admin": "homebrew",
    "cliente1": "treino01",
    "cliente2": "forca02",
    "cliente3": "saude03"
}

# --- 3. FUNÇÕES DO SISTEMA ---
def check_password():
    if st.session_state.get("logged_in"): return True
    
    # Tela de Login Estilizada
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown(f"<h1 style='text-align: center; color: {COR_LARANJA};'>MENTOR <span style='color:white'>AI</span></h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray; margin-bottom: 30px;'>Homebrew Marketing Intelligence</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            u = st.text_input("ID DE ACESSO", placeholder="Seu usuário")
            p = st.text_input("CHAVE DE SEGURANÇA", type="password", placeholder="Sua senha")
            st.markdown(" ") # Espaço
            if st.button("INICIAR SESSÃO ⚡"):
                if u in USUARIOS and USUARIOS[u] == p:
                    st.session_state["logged_in"] = True
                    st.rerun()
                else: st.error("ACESSO NEGADO.")
    return False

def configure_api():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("ERRO CRÍTICO: API KEY não encontrada.")
        st.stop()
    return api_key

def get_best_model():
    # Lógica inteligente de fallback
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name
        return 'models/gemini-1.5-flash'
    except: return 'models/gemini-1.5-flash'

@st.cache_resource
def load_multiple_files(api_key):
    genai.configure(api_key=api_key)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files_dir = os.path.join(current_dir, "files")
    
    if not os.path.exists(files_dir): return None, "Diretório de arquivos não encontrado."
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

# --- 4. APLICAÇÃO PRINCIPAL ---
if check_password():
    api_key = configure_api()

    # --- BARRA LATERAL (BRANDING) ---
    with st.sidebar:
        # Título da Sidebar com Estilo
        st.markdown(f"<h2 style='color:{COR_LARANJA}; margin-bottom:0;'>HOMEBREW</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 12px; color: gray; letter-spacing: 2px;'>MARKETING TECH</p>", unsafe_allow_html=True)
        st.divider()
        
        st.markdown("### STATUS DO SISTEMA")
        if "library_refs" in st.session_state and st.session_state["library_refs"]:
            st.success(f"● ONLINE | {len(st.session_state['library_refs'])} Fontes")
        else:
            st.warning("○ OFFLINE | Reconectando...")
            
        st.markdown("### FERRAMENTAS")
        if st.button("LIMPAR CONVERSA 🗑️"):
            st.session_state.messages = []
            st.rerun()
            
        if st.button("RECARREGAR IA 🔄"):
            st.cache_resource.clear()
            if "library_refs" in st.session_state: del st.session_state["library_refs"]
            st.rerun()

        st.divider()
        if st.button("SAIR (LOGOUT)"): 
            st.session_state["logged_in"] = False
            st.rerun()

    # --- CABEÇALHO DO CHAT ---
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(f"<h1 style='margin-bottom: 0;'>MENTOR <span class='highlight-orange'>AI</span></h1>", unsafe_allow_html=True)
        st.caption("Especialista em Fisiologia do Exercício & Biomecânica")
    
    # Carregamento da Biblioteca (Invisível)
    if "library_refs" not in st.session_state or not st.session_state["library_refs"]:
        with st.spinner("Inicializando protocolo neural..."):
            refs, err = load_multiple_files(api_key)
            if refs: 
                st.session_state["library_refs"] = refs
            else: 
                st.error("Falha na conexão com a base de dados.")

    # --- ÁREA DE CHAT ---
    # Container para mensagens (para dar um respiro no layout)
    chat_container = st.container()

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Olá. Sou seu assistente técnico. Analiso seus livros de fisiologia para responder perguntas complexas. Mande sua dúvida."}]

    with chat_container:
        for msg in st.session_state.messages:
            # Ícones personalizados: Robô para AI, Pessoa para User
            avatar = "🤖" if msg["role"] == "assistant" else "👤"
            st.chat_message(msg["role"], avatar=avatar).write(msg["content"])

    # Input Flutuante
    if prompt := st.chat_input("Digite sua dúvida técnica..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user", avatar="👤").write(prompt)

        with st.chat_message("assistant", avatar="⚡"):
            container = st.empty()
            library = st.session_state.get("library_refs")
            
            if library:
                try:
                    model_name = get_best_model()
                    model = genai.GenerativeModel(model_name, 
                        system_instruction="Você é um Mentor Sênior. Responda de forma direta, técnica e seca. Use APENAS os arquivos fornecidos. Cite as fontes.")
                    
                    response = model.generate_content(library + [prompt])
                    container.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    container.error(f"Erro de processamento: {e}")
            else:
                container.error("Erro: Base de conhecimento desconectada.")
