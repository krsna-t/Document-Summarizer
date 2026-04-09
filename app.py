import streamlit as st
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

from ocr.extractor import DocumentExtractor
from llm.gemini_client import GeminiClient
from llm.llama_client import LlamaClient
from utils.langchain_chain import SummarizationChain

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocuSummarize AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ===== Global ===== */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "San Francisco", "Segoe UI", Roboto, sans-serif;
        background-color: #f5f5f7;
        color: #1d1d1f;
    }

    /* ===== Main Container ===== */
    .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }

    /* ===== Header ===== */
    .main-header {
        background: #ffffff;
        padding: 1.8rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 600;
        color: #1d1d1f;
    }
    .main-header p {
        margin-top: 0.4rem;
        font-size: 0.95rem;
        color: #6e6e73;
    }

    /* ===== Section Titles ===== */
    h2, h3 {
        font-weight: 600 !important;
        color: #1d1d1f !important;
    }

    /* ===== Cards ===== */
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .metric-card h3 {
        font-size: 0.75rem;
        color: #6e6e73;
        margin: 0;
    }
    .metric-card p {
        margin-top: 0.4rem;
        font-size: 1.3rem;
        font-weight: 600;
        color: #1d1d1f;
    }

    /* ===== Upload Box Fix ===== */
    .stFileUploader {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #e5e5e7;
    }

    /* ===== Extracted Text ===== */
    .extracted-text-box {
        background: #ffffff;
        border: 1px solid #e5e5e7;
        padding: 1rem;
        border-radius: 10px;
        font-family: monospace;
        font-size: 0.85rem;
        max-height: 300px;
        overflow-y: auto;
        color: #333;
    }

    /* ===== Summary ===== */
    .summary-box {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.5rem;
        border: 1px solid #e5e5e7;
        font-size: 1rem;
        line-height: 1.6;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    }

    /* ===== Buttons ===== */
    .stButton > button {
        background: #1d1d1f;
        color: #ffffff;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-size: 0.9rem;
        font-weight: 500;
        border: none;
    }
    .stButton > button:hover {
        background: #000000;
    }

    /* ===== Inputs ===== */
    .stTextInput input, .stSelectbox div {
        background-color: #ffffff !important;
        border: 1px solid #d2d2d7 !important;
        color: #1d1d1f !important;
        border-radius: 6px !important;
    }

    /* ===== Sidebar (IMPORTANT FIX) ===== */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e5e7;
    }

    section[data-testid="stSidebar"] * {
        color: #1d1d1f !important;
    }

    /* ===== Remove Streamlit weird dark patches ===== */
    .stApp {
        background-color: #f5f5f7;
    }

</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📄 DocuSummarize AI</h1>
    <p>Multimodal Document Summarization · OCR · Gemini & Llama · LangChain</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    st.subheader("LLM Model")
    llm_choice = st.selectbox(
        "Select model",
        ["Gemini 2.5 Flash", "Llama (local via Ollama)", "Both (compare)"],
        help="Gemini requires a Google API key. Llama requires Ollama running locally.",
    )

    st.subheader("Summary Settings")
    summary_style = st.selectbox(
        "Summary style",
        ["Concise (3-5 sentences)", "Detailed (full paragraphs)", "Bullet points", "Executive brief"],
    )
    summary_language = st.selectbox(
        "Output language",
        ["English", "Hindi", "Spanish", "French", "German", "Arabic", "Chinese"],
    )
    max_length = st.slider("Max summary length (words)", 50, 500, 150)

    st.subheader("OCR Settings")
    ocr_language = st.selectbox("OCR language", ["eng", "hin", "spa", "fra", "deu", "ara", "chi_sim"])
    enhance_image = st.checkbox("Enhance image before OCR", value=True)

    st.divider()
    st.subheader("API Keys")
    gemini_key = st.text_input("Google Gemini API Key", type="password",
                               value=os.getenv("GEMINI_API_KEY", ""),
                               help="Get from https://aistudio.google.com/")
    ollama_url = st.text_input("Ollama URL", value=os.getenv("OLLAMA_URL", "http://localhost:11434"))
    ollama_model = st.text_input("Ollama model name", value=os.getenv("OLLAMA_MODEL", "llama3"))

    st.divider()
    st.caption("Built with Streamlit · LangChain · Tesseract OCR")

# ── Main content ──────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📂 Upload Document")
    uploaded_file = st.file_uploader(
        "Drop your file here",
        type=["pdf", "docx", "png", "jpg", "jpeg", "tiff", "bmp"],
        help="Supported: PDF, DOCX, PNG, JPG, TIFF, BMP",
    )

    if uploaded_file:
        # File info metrics
        file_size_kb = len(uploaded_file.getvalue()) / 1024
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""<div class="metric-card"><h3>File type</h3>
                <p>{Path(uploaded_file.name).suffix.upper()}</p></div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card"><h3>File size</h3>
                <p>{file_size_kb:.1f} KB</p></div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="metric-card"><h3>Status</h3>
                <p style="font-size:1rem">Ready</p></div>""", unsafe_allow_html=True)

        # Preview for images
        ext = Path(uploaded_file.name).suffix.lower()
        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            st.image(uploaded_file, caption="Uploaded image", use_column_width=True)
        elif ext == ".pdf":
            st.info("PDF uploaded — text and images will be extracted via OCR.")
        elif ext == ".docx":
            st.info("DOCX uploaded — text content will be extracted.")

        st.divider()

        # Summarize button
        run_btn = st.button("Extract & Summarize", use_container_width=True)
    else:
        st.info(" Upload a document to get started.")
        run_btn = False

with col2:
    st.subheader("Extracted Text")
    extracted_placeholder = st.empty()
    extracted_placeholder.caption("Extracted text will appear here after processing.")

# ── Full-width summary output ─────────────────────────────────────────────────
st.divider()
st.subheader("AI Summary")
summary_placeholder = st.empty()
summary_placeholder.caption("Summary will appear here after processing.")

# ── Processing logic ──────────────────────────────────────────────────────────
if run_btn and uploaded_file:
    # Save upload to temp file
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        # Step 1: OCR / text extraction
        with st.spinner("🔍 Extracting text from document..."):
            extractor = DocumentExtractor(ocr_lang=ocr_language, enhance=enhance_image)
            extracted_text, page_count = extractor.extract(tmp_path)

        if not extracted_text.strip():
            st.error("❌ No text could be extracted. Try a different file or OCR language.")
        else:
            word_count = len(extracted_text.split())
            char_count = len(extracted_text)

            with col2:
                extracted_placeholder.empty()
                with extracted_placeholder.container():
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Words", f"{word_count:,}")
                    c2.metric("Characters", f"{char_count:,}")
                    c3.metric("Pages/Sections", str(page_count))
                    st.markdown(f'<div class="extracted-text-box">{extracted_text[:3000]}{"..." if len(extracted_text) > 3000 else ""}</div>',
                                unsafe_allow_html=True)
                    if len(extracted_text) > 3000:
                        st.caption(f"Showing first 3000 of {char_count} characters.")

            # Step 2: Summarization
            style_map = {
                "Concise (3-5 sentences)": "concise",
                "Detailed (full paragraphs)": "detailed",
                "Bullet points": "bullets",
                "Executive brief": "executive",
            }
            style_key = style_map[summary_style]

            chain = SummarizationChain(style=style_key, language=summary_language, max_words=max_length)

            if llm_choice == "Gemini 2.5 Flash":
                with st.spinner("Generating summary with Gemini 2.5 Flash..."):
                    if not gemini_key:
                        st.error("❌ Please enter your Gemini API key in the sidebar.")
                    else:
                        client = GeminiClient(api_key=gemini_key)
                        prompt = chain.build_prompt(extracted_text)
                        summary = client.summarize(prompt)
                        summary_placeholder.empty()
                        with summary_placeholder.container():
                            st.markdown('<span class="success-badge">✅ Gemini 2.5 Flash</span>', unsafe_allow_html=True)
                            st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
                            st.download_button("⬇️ Download summary (.txt)", summary,
                                               file_name="summary.txt", mime="text/plain")

            elif llm_choice == "Llama (local via Ollama)":
                with st.spinner("Generating summary with Llama..."):
                    client = LlamaClient(base_url=ollama_url, model=ollama_model)
                    prompt = chain.build_prompt(extracted_text)
                    summary = client.summarize(prompt)
                    summary_placeholder.empty()
                    with summary_placeholder.container():
                        st.markdown(f'<span class="success-badge">✅ Llama ({ollama_model})</span>', unsafe_allow_html=True)
                        st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
                        st.download_button("⬇️ Download summary (.txt)", summary,
                                           file_name="summary.txt", mime="text/plain")

            else:  # Both
                summary_placeholder.empty()
                with summary_placeholder.container():
                    tab_g, tab_l = st.tabs(["✨ Gemini 2.5 Flash", " Llama"])
                    prompt = chain.build_prompt(extracted_text)

                    with tab_g:
                        if not gemini_key:
                            st.error("❌ Gemini API key missing.")
                        else:
                            with st.spinner("Gemini thinking..."):
                                g_client = GeminiClient(api_key=gemini_key)
                                g_summary = g_client.summarize(prompt)
                            st.markdown(f'<div class="summary-box">{g_summary}</div>', unsafe_allow_html=True)
                            st.download_button("⬇️ Download Gemini summary", g_summary,
                                               file_name="gemini_summary.txt", mime="text/plain")

                    with tab_l:
                        with st.spinner("Llama thinking..."):
                            l_client = LlamaClient(base_url=ollama_url, model=ollama_model)
                            l_summary = l_client.summarize(prompt)
                        st.markdown(f'<div class="summary-box">{l_summary}</div>', unsafe_allow_html=True)
                        st.download_button("⬇️ Download Llama summary", l_summary,
                                           file_name="llama_summary.txt", mime="text/plain")

    finally:
        os.unlink(tmp_path)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("🛠️ Multimodal Document Summarization Platform · Gemini API & Llama · LangChain · Tesseract OCR · Docker · Azure")
