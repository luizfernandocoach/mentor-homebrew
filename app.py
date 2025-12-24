import streamlit as st
import google.generativeai as genai
import time
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Mentor Homebrew", page_icon="🧠", layout="wide")

# --- SENHAS ---
USUARIOS = {"teste": "1234", "admin": "admin"}

# --- FUNÇÃO INTELIGENTE PARA ACHAR O MODELO (A CORREÇÃO) ---
def get_best_model():
    """Pergunta ao Google qual modelo Flash está disponível para evitar erro 404"""
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name # Prioriza Flash
        return 'models/gemini-pro' # Fallback
    except:
        return 'models/gemini-1.5-flash' # Tentativa final

# --- FUNÇÃO DE LOGIN ---
def check_password():
    if st.session_state.get("logged_in"): return True
    st.markdown("## 🔐 Acesso Restrito")
    col1, col2 = st.columns([1, 2])
    with col1:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("Incorreto")
    return False

# --- CARREGAMENTO DA BIBLIOTECA ---
@st.cache_resource
def load_library_robust(api_key):
    # Caminho absoluto
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "files", "biblioteca_mestre.pdf")
    
    if not os.path.exists(file_path):
        return None, f"ARQUIVO NÃO ACHADO EM: {file_path}"
        
    try:
        genai.configure(api_key=api_key)
        file_ref = genai.upload_file(file_path, mime_type="application/pdf")
        
        # Espera ficar ATIVO
        for _ in range(10):
            if file_ref.state.name == "ACTIVE": break
            if file_ref.state.name == "FAILED": return None, "Falha no Google."
            time.sleep(2)
            file_ref = genai.get_file(file_ref.name)
            
        return file_ref, None
    except Exception as e: return None, str(e)

# --- APP ---
if check_password():
    with st.sidebar:
        st.title("Painel VIP")
        api_key = st.text_input("Chave API:", type="password")
        if st.button("Sair"): 
            st.session_state["logged_in"] = False
            st.rerun()

    st.title("Mentor AI: Especialista 🏋️")
    
    if not api_key:
        st.warning("Insira a Chave API.")
        st.stop()

    # Carrega Biblioteca
    if "library_ref" not in st.session_state or not st.session_state["library_ref"]:
        with st.spinner("Conectando..."):
            ref, err = load_library_robust(api_key)
            if err: st.error(f"Erro: {err}")
            else: 
                st.session_state["library_ref"] = ref
                st.toast("Conectado!", icon="✅")

    # Chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Olá! Pode perguntar sobre o livro."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Sua dúvida..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            container = st.empty()
            lib = st.session_state.get("library_ref")
            
            if lib:
                try:
                    # AQUI ESTÁ A MÁGICA: Usa a função para pegar o nome certo
                    model_name = get_best_model()
                    
                    model = genai.GenerativeModel(model_name, 
                        system_instruction="Você é um Mentor Técnico. Responda APENAS com base no arquivo.")
                    
                    response = model.generate_content([lib, prompt])
                    container.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    container.error(f"Erro: {e}")
            else:
                container.error("Biblioteca desconectada.")