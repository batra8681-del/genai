import streamlit as st
from pypdf import PdfReader
import ollama

def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return ""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension == 'txt':
        return uploaded_file.getvalue().decode("utf-8")
    elif file_extension == 'pdf':
        try:
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    else:
        return "Unsupported file type."

def get_system_prompt(app_mode, output_length, current_tone):
    base_prompt = f"You are a direct AI assistant. Respond in a {current_tone} tone."
    if app_mode == "Summarization":
        if output_length == "Short": return f"{base_prompt} Summarize the text in 1-2 sentences."
        elif output_length == "Medium": return f"{base_prompt} Summarize the text into a 3-5 sentence paragraph."
        else: return f"{base_prompt} Provide a detailed summary of all key points."
    elif app_mode == "Grammar Correction":
        return f'''{base_prompt} You are a strict grammar correction tool.

    Your task:
    - Only correct grammar, spelling, and punctuation.
    - Do NOT add, remove, or change meaning.
    - Do NOT include explanations, comments, or extra sentences.
    - Do NOT respond conversationally.

    Output ONLY the corrected sentence.

    Example:
    Input: hello my name is anmol
    Output: Hello, my name is Anmol.'''
    elif app_mode == "Creative Generation":
        return f"{base_prompt} Generate content based on the prompt. Length: {output_length}. Tone: {current_tone}."
    return base_prompt

def stream_llm_response(user_content, system_prompt, model="llama3"):
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_content},
            ],
            stream=True
        )
        for chunk in response:
            yield chunk['message']['content']
    except Exception as e:
        yield f"Error connecting to Ollama: {str(e)}"

st.set_page_config(page_title="GRAMMERLY-LITE")

st.markdown("""
    <style>
   
     .stApp ,h1, h2, h3, h4, h5, h6, p, label, span { color: #ACBF69 !important; }

    .stTextArea textarea {
        font-size: 15px !important;
        line-height: 1.5 !important;
        border-radius: 8px !important;
    }
    div.stButton > button {
        background-color: #373E02 !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        font-weight: bold !important;
        border: none !important;
    }
    div.stButton > button:hover {
        background-color: #556B2F !important;
        color: #ffffff !important;
    }

    [data-testid="stFileUploadDropzone"] {
        background-color: #ffffff !important;
        border-color: #808000 !important;
    }
    [data-testid="stFileUploadDropzone"] *, [data-testid="stFileUploadDropzone"] div {
        color: #2b2b2b !important;
    }
    </style>
""", unsafe_allow_html=True)

if 'user_text' not in st.session_state: st.session_state.user_text = ""
if 'app_mode' not in st.session_state: st.session_state.app_mode = None

if st.session_state.app_mode is None:
    st.title("WriteFlow AI")
    st.markdown("### Choose your tool to begin:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Summarization", use_container_width=True): st.session_state.app_mode = "Summarization"; st.rerun()
    with col2:
        if st.button("Grammar Correction", use_container_width=True): st.session_state.app_mode = "Grammar Correction"; st.rerun()
    with col3:
        if st.button("Creative Writing", use_container_width=True): st.session_state.app_mode = "Creative Generation"; st.rerun()
    st.stop()

with st.sidebar:
    st.title("Settings")
    st.divider()
    if st.button("← Back to Menu"): st.session_state.app_mode = None; st.rerun()
    st.divider()
    output_length = st.select_slider("Output Length", options=["Short", "Medium", "Long"], value="Medium")
    st.divider()
    current_tone = st.text_input("Custom Tone/Style", value="Professional")

st.header(f"Mode: {st.session_state.app_mode}")

if st.session_state.app_mode in ["Summarization", "Grammar Correction"]:
    
    uploaded_file = st.file_uploader("Upload a document (optional)", type=["txt", "pdf"])
    
    if uploaded_file:
    
        if st.session_state.get("current_file") != uploaded_file.name:
            st.session_state.user_text = extract_text_from_file(uploaded_file)
            st.session_state.current_file = uploaded_file.name
            st.rerun()

    
    input_text = st.text_area("Input Text", key="user_text", height=300)
    if st.button("Process Text", type="primary"):
        if not input_text.strip(): st.warning("Please enter text.")
        else:
            system_prompt = get_system_prompt(st.session_state.app_mode, output_length, current_tone)
            col1, col2 = st.columns(2)
            with col1: st.subheader("Original"); st.write(input_text)
            with col2:
                st.subheader("Output")
                res_p = st.empty(); full_res = ""
                for chunk in stream_llm_response(input_text, system_prompt, model='llama3'):
                    full_res += chunk; res_p.markdown(full_res + "▌")
                res_p.markdown(full_res)
else:
    prompt_input = st.text_area("Creative Prompt", height=200)
    if st.button("Generate Content", type="primary"):
        if not prompt_input.strip(): st.warning("Please enter a prompt.")
        else:
            system_prompt = get_system_prompt(st.session_state.app_mode, output_length, current_tone)
            res_p = st.empty(); full_res = ""
            for chunk in stream_llm_response(prompt_input, system_prompt, model='llama3'):
                full_res += chunk; res_p.markdown(full_res + "▌")
            res_p.markdown(full_res)
