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

# --- SELETOR DE MODELO ---
def get_best_model():
    # Tenta achar o Flash 1.5 (Melhor custo/benefício para muitos livros)
    return 'models/gemini-1.5-flash'

# --- CARREGAMENTO MULTI-ARQUIVO (NOVO) ---
@st.cache_resource
def load_multiple_files(api_key):
    """
    Varre a pasta 'files' e faz upload de TODOS os PDFs encontrados.
    Retorna uma lista de referências de arquivos.
    """
    genai.configure(api_key=api_key)
    
    # Localiza a pasta
    current_dir = os.path.dirname(os.path.abspath(__file__))
    files_dir = os.path.join(current_dir, "files")
    
    if not os.path.exists(files_dir):
        return None, f"Pasta 'files' não encontrada em {current_dir}"

    # Lista todos os PDFs
    pdf_files = [f for f in os.listdir(files_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        return None, "Nenhum PDF encontrado na pasta 'files'."

    uploaded_refs = []
    failed_files = []

    # Barra de progresso visual
    progress_text = "Processando Biblioteca..."
    my_bar = st.progress(0, text=progress_text)

    for i, filename in enumerate(pdf_files):
        file_path = os.path.join(files_dir, filename)
        try:
            # Upload
            file_ref = genai.upload_file(file_path, mime_type="application/pdf")
            
            # Espera ficar ATIVO (Loop de verificação)
            ready = False
            for _ in range(15): # Tenta por 30 segundos
                if file_ref.state.name == "ACTIVE":
                    ready = True
                    break
                if file_ref.state.name == "FAILED":
                    ready = False
                    break
                time.sleep(2)
                file_ref = genai.get_file(file_ref.name)
            
            if ready:
                uploaded_refs.append(file_ref)
            else:
                failed_files.append(filename)
                
        except Exception as e:
            failed_files.append(f"{filename} ({str(e)})")
        
        # Atualiza barra
        percent_complete = (i + 1) / len(pdf_files)
        my_bar.progress(percent_complete, text=f"Lendo: {filename}")

    my_bar.empty() # Remove barra ao fim
    
    if failed_files:
        return uploaded_refs, f"Alguns arquivos falharam: {failed_files}"
    
    return uploaded_refs, None

# --- APP PRINCIPAL ---
if check_password():
    with st.sidebar:
        st.title("📚 Biblioteca Ativa")
        
        # Mostra status da biblioteca na barra lateral (Visualização Útil)
        if "library_refs" in st.session_state and st.session_state["library_refs"]:
            st.success(f"{len(st.session_state['library_refs'])} Livros Carregados")
        
        if st.button("🔄 Recarregar Biblioteca"):
            st.cache_resource.clear()
            if "library_refs" in st.session_state:
                del st.session_state["library_refs"]
            st.rerun()

        st.divider()
        if st.button("Sair"): 
            st.session_state["logged_in"] = False
            st.rerun()

    st.title("Mentor AI: Expert 🏋️")
    st.caption("Baseado em Evidências: Schoenfeld, IUSCA & Revisões Sistemáticas")

    api_key = configure_api()

    # Carrega a Biblioteca (Multi-arquivos)
    if "library_refs" not in st.session_state or not st.session_state["library_refs"]:
        with st.spinner("O Mentor está estudando seus novos livros... (Isso pode levar 1 minuto)"):
            refs, err = load_multiple_files(api_key)
            
            if refs:
                st.session_state["library_refs"] = refs
                if err: st.warning(err) # Aviso se algum falhou, mas continua com os que deram certo
                else: st.toast("Biblioteca Completa Carregada!", icon="✅")
            else:
                st.error(f"Falha crítica: {err}")

    # Chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Olá! Minha base de conhecimento foi atualizada. Pergunte sobre hipertrofia, glúteos ou recomendações da IUSCA."}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ex: Segundo Schoenfeld, qual o volume ideal para hipertrofia?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            container = st.empty()
            library = st.session_state.get("library_refs")
            
            if library:
                try:
                    model_name = get_best_model()
                    model = genai.GenerativeModel(model_name, 
                        system_instruction="""
                        Você é um Mentor de Elite. 
                        Use EXCLUSIVAMENTE os livros fornecidos.
                        Ao responder, CITE A FONTE (ex: 'Segundo Schoenfeld...', 'De acordo com a IUSCA...').
                        Se houver conflito entre autores, apresente as duas visões.
                        """)
                    
                    # AQUI ESTÁ A MÁGICA: Passamos a lista inteira de arquivos + a pergunta
                    request_content = library + [prompt]
                    
                    response = model.generate_content(request_content)
                    container.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    container.error(f"Erro: {e}")
                    if "429" in str(e): st.error("Muitos livros carregados. Tente remover o arquivo maior.")
            else:
                container.error("Biblioteca desconectada.")
