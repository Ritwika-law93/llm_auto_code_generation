# llm_auto_code_generation

From a one-paragraph PRD to a documented, tested codebase — using LLMs.

## What it does

A 4-stage pipeline:
1. **PRD** — a one-paragraph product spec (pasted, uploaded, or picked from examples)
2. **System Design** — architecture, folder structure, DB schema, REST API contracts
3. **Code** — production-grade scaffolding in the chosen stack
4. **Tests** — unit + integration + edge cases for the generated code

Each stage's output feeds the next, keeping the model grounded.

## Project structure

```
app.py                  # Streamlit UI (demo)
main.py                 # CLI: runs the pipeline with the default PRD
generator.py            # Reusable LLM pipeline (used by both)
prompts.py              # Stack-aware prompt templates
config.py               # Model + temperature
make_ppt.py             # Generates AI_Code_Generator_Demo.pptx
examples/               # Sample PRDs (task manager, e-commerce, URL shortener)
requirements.txt
.env                    # OPENROUTER_API_KEY=... (or OPENAI_API_KEY=...)
```

## Setup

```powershell
python -m pip install -r requirements.txt
```

Create a `.env` file with your API key:

```
OPENROUTER_API_KEY=sk-...
```

The code uses OpenRouter by default; an `OPENAI_API_KEY` env var also works.

## Run

**Streamlit UI (the demo):**
```powershell
streamlit run app.py
```
Opens at http://localhost:8501.

**CLI (writes `output_documentation.txt`):**
```powershell
python main.py
```

**Generate / regenerate the demo deck:**
```powershell
python make_ppt.py
```
Produces `AI_Code_Generator_Demo.pptx` — open and rebrand in PowerPoint as needed.

## Supported target stacks

- Node.js + Express  •  Tests: Jest + Supertest
- Java + Spring Boot  •  Tests: JUnit 5 + Mockito
- Python + FastAPI    •  Tests: pytest + httpx

Pick the stack in the Streamlit sidebar. Stack-specific prompt variations live in `prompts.py`.

## Demo flow (for the forum)

1. Open the Streamlit app.
2. Pick the **Task Manager** example PRD.
3. Pick **Node.js + Express** as the target stack.
4. Click **Generate** — watch the 4-stage progress bar.
5. Switch tabs: System Design → Generated Code → Test Cases.
6. Download the artifacts as a `.zip`.
7. *(Bonus)* Re-run with the same PRD but a different stack to show stack-agnostic generation.
