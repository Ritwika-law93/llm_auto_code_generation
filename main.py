from dotenv import load_dotenv

from openai import OpenAI
from config import MODEL, TEMPERATURE
from prompts import PRD, SYSTEM_DESIGN_PROMPT, CODE_GEN_PROMPT, TEST_GEN_PROMPT  
import os

load_dotenv()   

api_key = os.getenv('OPENROUTER_API_KEY')
client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

def call_llm(prompt, model=MODEL, temperature=TEMPERATURE):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a senior backend architect and developer."},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )
    return response.choices[0].message.content

# Framing system design prompt with the provided PRD
prompt = SYSTEM_DESIGN_PROMPT.format(prd=PRD)
design = call_llm(prompt)
# print(design)

#Framing code generation prompt with the system design output 
prompt = CODE_GEN_PROMPT.format(design=design)
code = call_llm(prompt)

#Framing code generation prompt with the system design output 
prompt = TEST_GEN_PROMPT.format(code=code)
test_case_code = call_llm(prompt)
#print(test_case_code)

# Using a context manager ensures the file is automatically closed
with open("output_documentation.txt", "w", encoding="utf-8") as file:
    file.write("------------------------------------ SYSTEM DESIGN ----------------------------------------\n")
    file.write(design + "\n\n")
    file.write("------------------------------------ GENERATED CODE ---------------------------------------\n")
    file.write(code + "\n\n")
    file.write("------------------------------------ TEST CASES -------------------------------------------\n")
    file.write(test_case_code + "\n")
