"""Streamlit UI for the LLM-powered auto code generation demo."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import streamlit as st

from config import MODEL, TEMPERATURE
from generator import generate_all
from prompts import STACKS, DEFAULT_STACK

EXAMPLES_DIR = Path(__file__).parent / "examples"


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
def load_examples() -> dict[str, str]:
    out: dict[str, str] = {}
    if EXAMPLES_DIR.exists():
        for path in sorted(EXAMPLES_DIR.glob("*.md")):
            out[path.stem.replace("_", " ").title()] = path.read_text(encoding="utf-8")
    return out


def extract_text_from_upload(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader  # local import: optional dependency
        except ImportError:
            st.error("PDF support requires `pypdf`. Run: pip install pypdf")
            return ""
        reader = PdfReader(uploaded_file)
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    # text / markdown
    return uploaded_file.read().decode("utf-8", errors="ignore")


def build_zip(artifacts: dict) -> bytes:
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
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
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

examples = load_examples()
input_tab1, input_tab2, input_tab3 = st.tabs(["Paste text", "Upload file", "Examples"])

prd_text = ""
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
            st.text(prd_text[:2000] + ("..." if len(prd_text) > 2000 else ""))

with input_tab3:
    if not examples:
        st.info("No examples found in `examples/` folder.")
    else:
        choice = st.selectbox("Pick an example PRD", list(examples.keys()))
        prd_text = examples[choice]
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
        st.stop()

    progress = st.progress(0, text="Starting...")
    status = st.empty()

    step_weights = {
        "Generating system design...": 10,
        "Generating code...": 40,
        "Generating test cases...": 75,
        "Done.": 100,
    }

    def on_step(msg: str) -> None:
        pct = step_weights.get(msg, 50)
        progress.progress(pct, text=msg)
        status.info(msg)

    try:
        artifacts = generate_all(prd=prd_text, stack=stack, on_step=on_step)
        st.session_state["artifacts"] = artifacts
        progress.progress(100, text="Done.")
        status.success("Generation complete.")
    except Exception as e:
        progress.empty()
        status.error(f"Generation failed: {e}")
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
