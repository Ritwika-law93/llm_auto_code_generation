"""Streamlit UI for the LLM-powered auto code generation demo."""
from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path

import streamlit as st

from config import MODEL, TEMPERATURE
from generator import generate_all
from prompts import STACKS, DEFAULT_STACK

# Streamlit reruns this module on every interaction, so module-level logging
# config must be idempotent — basicConfig is a no-op if handlers already exist.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

SAMPLES_DIR = Path(__file__).parent / "samples"


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Code Generator | PRD to Production",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #f5f3ff;
            border-radius: 8px 8px 0 0;
            padding: 10px 18px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #a100ff !important;
            color: white !important;
        }
        .metric-card {
            padding: 14px; border-radius: 10px;
            background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
            border: 1px solid #e0d4ff;
        }
        h1 { color: #2d1b69; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_samples() -> dict[str, str]:
    """Read all .md files from the samples directory and return {display_name: content}."""
    out: dict[str, str] = {}
    if SAMPLES_DIR.exists():
        for path in sorted(SAMPLES_DIR.glob("*.md")):
            display_name = path.stem.replace("_", " ").title()
            out[display_name] = path.read_text(encoding="utf-8")
        logger.info("Loaded %d sample PRD(s) from %s", len(out), SAMPLES_DIR)
    else:
        logger.warning("Samples directory not found: %s", SAMPLES_DIR)
    return out


def extract_text_from_upload(uploaded_file) -> str:
    """Extract plain text from an uploaded .txt, .md, or .pdf file."""
    name = uploaded_file.name.lower()
    logger.info("Extracting text from uploaded file: %s", uploaded_file.name)

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader  # local import: optional dependency
        except ImportError:
            st.error("PDF support requires `pypdf`. Run: pip install pypdf")
            logger.error("pypdf not installed — cannot parse PDF upload")
            return ""
        reader = PdfReader(uploaded_file)
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        logger.info("Extracted %d chars from PDF (%d pages)", len(text), len(reader.pages))
        return text

    # Plain text or markdown — decode directly.
    text = uploaded_file.read().decode("utf-8", errors="ignore")
    logger.info("Extracted %d chars from text file", len(text))
    return text


def build_zip(artifacts: dict) -> bytes:
    """Pack all pipeline artifacts into an in-memory ZIP and return raw bytes."""
    logger.info("Building ZIP for stack=%r", artifacts.get("stack"))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("01_prd.md", artifacts["prd"])
        zf.writestr("02_system_design.md", artifacts["design"])
        zf.writestr("03_generated_code.md", artifacts["code"])
        zf.writestr("04_test_cases.md", artifacts["tests"])
        zf.writestr(
            "README.txt",
            f"Generated for stack: {artifacts['stack']}\n"
            f"Pipeline: PRD -> System Design -> Code -> Tests\n",
        )
    zip_size = buf.tell()
    logger.info("ZIP built — size=%d bytes", zip_size)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### API Key")
    api_key_input = st.text_input(
        "OpenRouter / OpenAI API key",
        type="password",
        placeholder="sk-or-v1-... or sk-...",
        help="Your key is used only for this session and never stored.",
    )
    if api_key_input:
        st.success("Key provided", icon="🔑")
    else:
        st.warning("Enter an API key to generate.", icon="⚠️")

    st.markdown("---")
    st.markdown("### Configuration")
    stack = st.selectbox("Target stack", list(STACKS.keys()), index=list(STACKS.keys()).index(DEFAULT_STACK))
    stack_info = STACKS[stack]
    st.caption(f"**Language:** {stack_info['language']}")
    st.caption(f"**Framework:** {stack_info['framework']}")
    st.caption(f"**Tests:** {stack_info['test_framework']}")

    st.markdown("---")
    st.markdown("### Model")
    st.caption(f"**Model:** `{MODEL}`")
    st.caption(f"**Temperature:** `{TEMPERATURE}`")

    st.markdown("---")
    st.markdown("### Pipeline")
    st.markdown(
        """
        1. **PRD** — what the product should do
        2. **System Design** — architecture, schema, APIs
        3. **Code** — production-grade implementation
        4. **Tests** — unit + integration + edge cases
        """
    )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("⚙️ AI Code Generator")
st.markdown(
    "##### From a one-paragraph PRD to a documented, tested codebase — in minutes."
)

# Metric tiles — one per pipeline stage/stat.
c1, c2, c3, c4 = st.columns(4)
for col, label, value in [
    (c1, "Pipeline stages", "4"),
    (c2, "Target stacks", str(len(STACKS))),
    (c3, "Model", MODEL),
    (c4, "Avg run", "~45s"),
]:
    with col:
        st.markdown(
            f"<div class='metric-card'><b>{label}</b><br><span style='font-size:20px'>{value}</span></div>",
            unsafe_allow_html=True,
        )

st.markdown("---")


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------
st.subheader("1. Provide a Product Requirements Document")

samples = load_samples()

# prd_text is declared before the tabs so all three input paths can assign to it.
# Streamlit re-executes this script on every interaction, so the last active tab wins.
prd_text = ""
input_tab1, input_tab2, input_tab3 = st.tabs(["Paste text", "Upload file", "Examples"])

with input_tab1:
    prd_text = st.text_area(
        "Paste your PRD here",
        height=220,
        placeholder="Describe the product: features, users, workflows, constraints...",
        key="prd_paste",
    )

with input_tab2:
    uploaded = st.file_uploader(
        "Upload a PRD (.txt, .md, or .pdf)", type=["txt", "md", "pdf"]
    )
    if uploaded is not None:
        prd_text = extract_text_from_upload(uploaded)
        st.success(f"Loaded {uploaded.name} ({len(prd_text)} chars)")
        with st.expander("Preview"):
            # Cap preview at 2000 chars to avoid flooding the UI.
            st.text(prd_text[:2000] + ("..." if len(prd_text) > 2000 else ""))

with input_tab3:
    if not samples:
        st.info("No samples found in `samples/` folder.")
    else:
        choice = st.selectbox("Pick an example PRD", list(samples.keys()))
        prd_text = samples[choice]
        st.code(prd_text, language="markdown")


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("2. Generate")

go = st.button("🚀 Generate Design, Code & Tests", type="primary", use_container_width=True)

if go:
    if not prd_text.strip():
        st.error("Please provide a PRD first.")
        logger.warning("Generate clicked with empty PRD")
        st.stop()
    if not api_key_input.strip():
        st.error("Please enter your API key in the sidebar.")
        logger.warning("Generate clicked with no API key")
        st.stop()

    logger.info("Generation triggered — stack=%r prd_chars=%d", stack, len(prd_text))

    progress = st.progress(0, text="Starting...")
    status = st.empty()

    # Maps pipeline status messages to approximate progress percentages.
    step_weights = {
        "Generating system design...": 10,
        "Generating code...":          40,
        "Generating test cases...":    75,
        "Done.":                       100,
    }

    def on_step(msg: str) -> None:
        pct = step_weights.get(msg, 50)
        logger.info("Pipeline step: %s (%d%%)", msg, pct)
        progress.progress(pct, text=msg)
        status.info(msg)

    try:
        artifacts = generate_all(
            prd=prd_text,
            stack=stack,
            on_step=on_step,
            api_key=api_key_input.strip(),
        )
        st.session_state["artifacts"] = artifacts
        progress.progress(100, text="Done.")
        status.success("Generation complete.")
        logger.info("Generation complete — artifacts stored in session state")
    except Exception as e:
        progress.empty()
        status.error(f"Generation failed: {e}")
        logger.exception("Pipeline raised an exception: %s", e)
        st.stop()


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
artifacts = st.session_state.get("artifacts")
if artifacts:
    st.markdown("---")
    st.subheader("3. Results")

    tab_design, tab_code, tab_tests = st.tabs(
        ["📐 System Design", "💻 Generated Code", "✅ Test Cases"]
    )
    with tab_design:
        st.markdown(artifacts["design"])
    with tab_code:
        st.markdown(artifacts["code"])
    with tab_tests:
        st.markdown(artifacts["tests"])

    st.markdown("---")
    st.subheader("4. Download")
    st.download_button(
        "📦 Download all artifacts (.zip)",
        data=build_zip(artifacts),
        file_name="generated_artifacts.zip",
        mime="application/zip",
        use_container_width=True,
    )
