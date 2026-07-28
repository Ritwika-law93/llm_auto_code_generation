"""Prompt templates and stack definitions for the auto code generation pipeline."""

# ---------------------------------------------------------------------------
# Supported target stacks
# ---------------------------------------------------------------------------
# Each entry drives all three prompt templates — language/framework set the
# code style, test_framework targets the right test runner, and code_label
# is the fenced-code-block identifier used in the code generation prompt
# (e.g. ```javascript ... ```) so syntax highlighting works in the output.
STACKS = {
    "Node.js + Express": {
        "language": "JavaScript (Node.js)",
        "framework": "Express",
        "test_framework": "Jest + Supertest",
        "code_label": "javascript",
    },
    "Java + Spring Boot": {
        "language": "Java",
        "framework": "Spring Boot",
        "test_framework": "JUnit 5 + Mockito",
        "code_label": "java",
    },
    "Python + FastAPI": {
        "language": "Python",
        "framework": "FastAPI",
        "test_framework": "pytest + httpx",
        "code_label": "python",
    },
}

DEFAULT_STACK = "Node.js + Express"


# ---------------------------------------------------------------------------
# Default PRD (kept for backwards compatibility with main.py)
# ---------------------------------------------------------------------------
PRD = """
Build a task management system with:
- User authentication
- Create, update, delete tasks
- Task status tracking
- REST API
"""


# ---------------------------------------------------------------------------
# Prompt templates (stack-aware)
# ---------------------------------------------------------------------------
# All three prompts use a domain-specific system role to anchor output style.
# Enumerating required sections explicitly prevents the model from skipping
# less obvious areas (edge cases, scalability) under token pressure.
SYSTEM_DESIGN_PROMPT = """
You are a principal software architect.

Given the following PRD:
{prd}

Produce a production-ready system design targeting **{language} + {framework}**:
1. System architecture
2. Folder structure
3. Database schema
4. API contracts (REST)
5. Key design decisions
6. Edge cases
7. Scalability considerations

Be precise and production-ready. Use clear headings.
"""


CODE_GEN_PROMPT = """
You are a senior backend engineer.

Given this system design:
{design}

Generate production-grade **{language} ({framework})** code:
- Routes / Controllers
- Services
- Models
- Middleware (auth, validation, error handling)

Requirements:
- Clean architecture
- Proper error handling
- Input validation
- Security best practices

Output each file as a fenced code block prefixed with the file path as a comment,
for example:
```{code_label}
// path: src/routes/tasks.js
...code...
```
"""


TEST_GEN_PROMPT = """
You are a senior QA engineer.

Given this backend code:
{code}

Generate **{test_framework}** tests:
1. Unit tests
2. Integration tests
3. Edge cases
4. Failure scenarios

Ensure high coverage and output each test file as a fenced code block with a
file path comment header.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# Each builder injects the previous stage's output so the model stays grounded:
#   PRD -> design -> code -> tests (each call receives the prior output as context).
def build_design_prompt(prd: str, stack: str = DEFAULT_STACK) -> str:
    s = STACKS[stack]
    return SYSTEM_DESIGN_PROMPT.format(
        prd=prd, language=s["language"], framework=s["framework"]
    )


def build_code_prompt(design: str, stack: str = DEFAULT_STACK) -> str:
    s = STACKS[stack]
    return CODE_GEN_PROMPT.format(
        design=design,
        language=s["language"],
        framework=s["framework"],
        code_label=s["code_label"],
    )


def build_test_prompt(code: str, stack: str = DEFAULT_STACK) -> str:
    s = STACKS[stack]
    return TEST_GEN_PROMPT.format(code=code, test_framework=s["test_framework"])
