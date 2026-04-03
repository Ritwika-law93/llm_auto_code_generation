#### PRODUCT REQUIREMENT DOCUMENT PROMPT
PRD = """
Build a task management system with:
- User authentication
- Create, update, delete tasks
- Task status tracking
- REST API
"""


#### SYSTEM DESIGN PROMPT
SYSTEM_DESIGN_PROMPT= """
You are a principal software architect.P

Given the following PRD:
{prd}

Produce:
1. System architecture (Node.js + Express)
2. Folder structure
3. Database schema
4. API contracts (REST)
5. Key design decisions
6. Edge cases
7. Scalability considerations

Be precise and production-ready.
"""



#### CODE GENERATION PROMPT
CODE_GEN_PROMPT = """
You are a senior backend engineer.

Given this system design:
{design}

Generate production-grade Node.js (Express) code:
- Routes
- Controllers
- Services
- Models
- Middleware

Requirements:
- Clean architecture
- Proper error handling
- Input validation
- Security best practices

Output code in structured sections.
"""


#### TEST CASE GENERATION PROMPT
TEST_GEN_PROMPT = """
You are a senior QA engineer.

Given this backend code:
{code}

Generate:
1. Jest + Supertest test cases
2. Unit + integration tests
3. Edge cases
4. Failure scenarios

Ensure high coverage.
"""




