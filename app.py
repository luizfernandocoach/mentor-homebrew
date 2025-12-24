import streamlit as st
import google.generativeai as genai
import time
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Mentor Homebrew", page_icon="🧠", layout="wide")

# --- GESTÃO DE ACESSO ---
USUARIOS = {
    "admin": "homebrew2025",
    "cliente1": "treino01",
    "cliente2": "forca02",
    "cliente3": "saude03",
    "cliente4": "meta2025",
    "cliente5": "vip05"
}

# --- LOGIN ---
def check_password():
    if st.session_state.get("logged_in"): return True
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Mentor AI: Login")
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("Acesso negado.")
    return False

# --- CONFIG API ---
def configure_api():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("ERRO: Configure a GOOGLE_API_KEY nos Secrets do Streamlit.")
        st.stop()
    return api_key

# --- SELETOR DE MODELO INTELIGENTE (RESTAURADO) ---
def get_best_model():
    """Busca dinâmica para evitar erro 404"""
    try:
        # Tenta listar o que tem disponível na conta
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name # Prioriza Flash (qualquer versão)
        return 'models/gemini-1.5-flash' # Tentativa padrão
    except:
        return 'models/gemini-1.5-flash' # Fallback final

# --- CARREGAMENTO MULTI-ARQUIVO ---
@st.cache_resource
def load_multiple_files(api_key):
    genai.configure(api_key=api_key)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files_dir = os.path.join(current_dir, "files")
    
    if not os.path.exists(files_dir): return None, "Pasta 'files' não encontrada."

    pdf_files = [f for f in os.listdir(files_dir) if f.lower().endswith('.pdf')]
    if not pdf_files: return None, "Nenhum PDF na pasta."

    uploaded_refs = []
    failed_files = []
    
    # Barra de progresso
    my_bar = st.progress(0, text="Processando Biblioteca...")

    for i, filename in enumerate(pdf_files):
        file_path = os.path.join(files_dir, filename)
        try:
            file_ref = genai.upload_file(file_path, mime_type="application/pdf")
            
            # Loop de espera (Wait for Active)
            ready = False
            for _ in range(15):
                if file_ref.state.name == "ACTIVE":
                    ready = True
                    break
                if file_ref.state.name == "FAILED":
                    ready = False
                    break
                time.sleep(1)
                file_ref = genai.get_file(file_ref.name)
            
            if ready: uploaded_refs.append(file_ref)
            else: failed_files.append(filename)
                
        except Exception as e:
            failed_files.append(f"{filename}")
        
        my_bar.progress((i + 1) / len(pdf_files), text=f"Lendo: {filename}")

    my_bar.empty()
    
    if failed_files: return uploaded_refs, f"Falha em: {failed_files}"
    return uploaded_refs, None

# --- APP PRINCIPAL ---
if check_password():
    with st.sidebar:
        st.title("📚 Biblioteca")
        if "library_refs" in st.session_state and st.session_state["library_refs"]:
            st.success(f"{len(st.session_state['library_refs'])} Livros Ativos")
        
        if st.button("🔄 Recarregar"):
            st.cache_resource.clear()
            if "library_refs" in st.session_state: del st.session_state["library_refs"]
            st.rerun()

        st.divider()
        if st.button("Sair"): 
            st.session_state["logged_in"] = False
            st.rerun()

    st.title("Mentor AI: Expert 🏋️")
    st.caption("Baseado em Evidências (Schoenfeld, IUSCA, etc)")

    api_key = configure_api()

    # Carrega Biblioteca
    if "library_refs" not in st.session_state or not st.session_state["library_refs"]:
        with st.spinner("Estudando novos livros..."):
            refs, err = load_multiple_files(api_key)
            if refs:
                st.session_state["library_refs"] = refs
                if err: st.warning(err)
                else: st.toast("Biblioteca Pronta!", icon="✅")
            else: st.error(f"Erro: {err}")

    # Chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Olá! Biblioteca atualizada. Pode perguntar."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Dúvida técnica..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            container = st.empty()
            library = st.session_state.get("library_refs")
            
            if library:
                try:
                    # AQUI ESTÁ A CORREÇÃO: Usa a função inteligente novamente
                    model_name = get_best_model()
                    
                    model = genai.GenerativeModel(model_name, 
                        system_instruction="Você é um Mentor Sênior. Responda usando APENAS os arquivos fornecidos. CITE AS FONTES.")
                    
                    response = model.generate_content(library + [prompt])
                    container.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    container.error(f"Erro: {e}")
            else:
                container.error("Biblioteca desconectada.")
