import streamlit as st
import google.generativeai as genai
import time
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Mentor Homebrew", page_icon="🧠", layout="wide")

# --- GESTÃO DE ACESSO (SEUS 5 PRIMEIROS CLIENTES) ---
# Dica: Mude as senhas antes de enviar!
USUARIOS = {
    "admin": "homebrew2025",    # Você
    "cliente1": "treino01",     # Personal 1
    "cliente2": "forca02",      # Personal 2
    "cliente3": "saude03",      # Personal 3
    "cliente4": "meta2025",     # Personal 4
    "cliente5": "vip05"         # Personal 5
}

# --- FUNÇÃO DE LOGIN ---
def check_password():
    if st.session_state.get("logged_in"): return True
    
    # Design da Tela de Login
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Mentor AI: Acesso Exclusivo")
        st.info("Entre com suas credenciais de assinante.")
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Acessar Sistema"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("Acesso negado.")
    return False

# --- CONFIGURAÇÃO DA API (AUTOMÁTICA) ---
def configure_api():
    # Tenta pegar do cofre (Secrets)
    api_key = st.secrets.get("GOOGLE_API_KEY")
    
    if not api_key:
        st.error("ERRO CRÍTICO: Chave de API não configurada no servidor.")
        st.stop()
        
    return api_key

# --- FUNÇÃO INTELIGENTE DE MODELO ---
def get_best_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name
        return 'models/gemini-pro'
    except: return 'models/gemini-1.5-flash'

# --- CARREGAMENTO DA BIBLIOTECA ---
@st.cache_resource
def load_library_robust(api_key):
    # Caminho absoluto para evitar erro de pasta
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "files", "biblioteca_mestre.pdf")
    
    if not os.path.exists(file_path):
        return None, f"Erro interno: Arquivo de base não encontrado."
        
    try:
        genai.configure(api_key=api_key)
        # Verifica se já existe um arquivo com esse nome no Google para não subir duplicado (Otimização)
        # Para o MVP simples, vamos subir sempre para garantir que funcione
        file_ref = genai.upload_file(file_path, mime_type="application/pdf")
        
        # Espera ficar ATIVO
        for _ in range(10):
            if file_ref.state.name == "ACTIVE": break
            if file_ref.state.name == "FAILED": return None, "Falha no processamento do arquivo."
            time.sleep(1)
            file_ref = genai.get_file(file_ref.name)
            
        return file_ref, None
    except Exception as e: return None, str(e)

# --- APP PRINCIPAL ---
if check_password():
    # BARRA LATERAL LIMPA (Sem campo de senha)
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2586/2586866.png", width=50)
        st.title("Área do Membro")
        st.success("Status: ✅ Ativo")
        
        st.divider()
        if st.button("Sair / Logout"): 
            st.session_state["logged_in"] = False
            st.rerun()
        
        st.caption("v1.0 - Homebrew Tech")

    # ÁREA PRINCIPAL
    st.title("Mentor AI: Especialista em Treinamento 🏋️")
    st.markdown("Use este chat para tirar dúvidas sobre fisiologia, biomecânica e montagem de treino.")

    # 1. Configura API Silenciosamente
    api_key = configure_api()

    # 2. Conecta o Cérebro
    if "library_ref" not in st.session_state or not st.session_state["library_ref"]:
        with st.spinner("Inicializando assistente inteligente..."):
            ref, err = load_library_robust(api_key)
            if err: st.error(f"Erro de conexão: {err}")
            else: st.session_state["library_ref"] = ref

    # 3. Chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Olá! Sou seu Mentor Técnico. Como posso ajudar com seus alunos hoje?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ex: Meu aluno sente dor no ombro durante o supino..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            container = st.empty()
            lib = st.session_state.get("library_ref")
            
            if lib:
                try:
                    model_name = get_best_model()
                    model = genai.GenerativeModel(model_name, 
                        system_instruction="Você é um Mentor Técnico Sênior. Responda APENAS com base no arquivo fornecido. Se a resposta não estiver no livro, diga que não consta na bibliografia.")
                    
                    # Gera resposta
                    response = model.generate_content([lib, prompt])
                    container.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    container.error(f"Erro momentâneo: {e}. Tente novamente.")
            else:
                container.error("O sistema está reconectando. Aguarde um instante e tente novamente.")
