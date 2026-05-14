"""Reusable LLM pipeline: PRD -> System Design -> Code -> Tests.

Used by both the CLI entrypoint (main.py) and the Streamlit UI (app.py).
"""
from __future__ import annotations

import os
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

load_dotenv()


def _make_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY in .env"
        )
    return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")


def call_llm(
    prompt: str,
    model: str = MODEL,
    temperature: float = TEMPERATURE,
    system: str = "You are a senior backend architect and developer.",
    client: Optional[OpenAI] = None,
) -> str:
    client = client or _make_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content


def generate_all(
    prd: str,
    stack: str = DEFAULT_STACK,
    on_step: Optional[Callable[[str], None]] = None,
    model: str = MODEL,
    temperature: float = TEMPERATURE,
) -> dict:
    """Run the full pipeline and return a dict of artifacts.

    `on_step` is an optional callback that receives status strings — useful for
    Streamlit progress updates.
    """
    client = _make_client()

    def notify(msg: str) -> None:
        if on_step:
            on_step(msg)

    notify("Generating system design...")
    design = call_llm(
        build_design_prompt(prd, stack), model=model, temperature=temperature, client=client
    )

    notify("Generating code...")
    code = call_llm(
        build_code_prompt(design, stack), model=model, temperature=temperature, client=client
    )

    notify("Generating test cases...")
    tests = call_llm(
        build_test_prompt(code, stack), model=model, temperature=temperature, client=client
    )

    notify("Done.")
    return {"design": design, "code": code, "tests": tests, "stack": stack, "prd": prd}


def write_documentation(artifacts: dict, path: str = "output_documentation.txt") -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("------------------------------------ SYSTEM DESIGN ----------------------------------------\n")
        f.write(artifacts["design"] + "\n\n")
        f.write("------------------------------------ GENERATED CODE ---------------------------------------\n")
        f.write(artifacts["code"] + "\n\n")
        f.write("------------------------------------ TEST CASES -------------------------------------------\n")
        f.write(artifacts["tests"] + "\n")
