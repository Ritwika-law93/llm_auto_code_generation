"""Reusable LLM pipeline: PRD -> System Design -> Code -> Tests.

Used by both the CLI entrypoint (main.py) and the Streamlit UI (app.py).
"""
from __future__ import annotations

import logging
import os
import time
from typing import Callable, Optional

from dotenv import load_dotenv
from openai import OpenAI

from config import MODEL, TEMPERATURE
from prompts import (
    DEFAULT_STACK,
    build_code_prompt,
    build_design_prompt,
    build_test_prompt,
)

# Load .env before any os.getenv call so env vars are available at import time.
load_dotenv()

logger = logging.getLogger(__name__)


def _make_client(api_key: Optional[str] = None) -> OpenAI:
    # UI-supplied key takes priority over environment variables.
    key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "No API key found. Enter your key in the sidebar or set OPENROUTER_API_KEY in .env"
        )
    source = "argument" if api_key else "environment"
    logger.debug("Building OpenAI client (key source: %s)", source)
    return OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")


def call_llm(
    prompt: str,
    model: str = MODEL,
    temperature: float = TEMPERATURE,
    system: str = "You are a senior backend architect and developer.",
    client: Optional[OpenAI] = None,
    api_key: Optional[str] = None,
) -> str:
    client = client or _make_client(api_key=api_key)

    logger.info(
        "LLM call — model=%s temperature=%.1f prompt_chars=%d",
        model, temperature, len(prompt),
    )
    t0 = time.perf_counter()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )

    elapsed = time.perf_counter() - t0
    content = response.choices[0].message.content
    logger.info(
        "LLM call complete — elapsed=%.2fs response_chars=%d",
        elapsed, len(content),
    )
    return content


def generate_all(
    prd: str,
    stack: str = DEFAULT_STACK,
    on_step: Optional[Callable[[str], None]] = None,
    model: str = MODEL,
    temperature: float = TEMPERATURE,
    api_key: Optional[str] = None,
) -> dict:
    """Run the full pipeline and return a dict of artifacts.

    `on_step` is an optional callback that receives status strings — useful for
    Streamlit progress updates.
    """
    logger.info("Pipeline start — stack=%r model=%s prd_chars=%d", stack, model, len(prd))
    pipeline_start = time.perf_counter()

    # Reuse one client across all three calls to avoid repeated auth overhead.
    client = _make_client(api_key=api_key)

    # Inner helper keeps notify calls one-liners throughout the function.
    def notify(msg: str) -> None:
        if on_step:
            on_step(msg)

    # Stage 1: system design — gives the code stage a concrete architecture to follow.
    notify("Generating system design...")
    logger.info("Stage 1/3: system design")
    design = call_llm(
        build_design_prompt(prd, stack), model=model, temperature=temperature, client=client
    )
    logger.debug("System design length: %d chars", len(design))

    # Stage 2: code generation — receives the full design so output matches the agreed architecture.
    notify("Generating code...")
    logger.info("Stage 2/3: code generation")
    code = call_llm(
        build_code_prompt(design, stack), model=model, temperature=temperature, client=client
    )
    logger.debug("Generated code length: %d chars", len(code))

    # Stage 3: test generation — uses the actual generated code, not the design,
    # so tests target the real implementation rather than the intended one.
    notify("Generating test cases...")
    logger.info("Stage 3/3: test generation")
    tests = call_llm(
        build_test_prompt(code, stack), model=model, temperature=temperature, client=client
    )
    logger.debug("Test cases length: %d chars", len(tests))

    total = time.perf_counter() - pipeline_start
    logger.info("Pipeline complete — total_elapsed=%.2fs", total)
    notify("Done.")

    return {"design": design, "code": code, "tests": tests, "stack": stack, "prd": prd}


def write_documentation(artifacts: dict, path: str = "output_documentation.txt") -> None:
    logger.info("Writing documentation to %s", path)
    with open(path, "w", encoding="utf-8") as f:
        f.write("------------------------------------ SYSTEM DESIGN ----------------------------------------\n")
        f.write(artifacts["design"] + "\n\n")
        f.write("------------------------------------ GENERATED CODE ---------------------------------------\n")
        f.write(artifacts["code"] + "\n\n")
        f.write("------------------------------------ TEST CASES -------------------------------------------\n")
        f.write(artifacts["tests"] + "\n")
    logger.info("Documentation written (%d chars)", sum(len(v) for v in artifacts.values() if isinstance(v, str)))
