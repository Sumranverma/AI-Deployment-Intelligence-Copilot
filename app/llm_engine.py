import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def generate_llm_response(question, context):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    client = OpenAI(api_key=api_key)

    prompt = f"""
You are an AI Deployment Operations Copilot.

Answer the user's deployment operations question using ONLY the
deployment information and operational knowledge provided below.

Be concise, professional, and operationally useful.

Structure the response using:

Status
Why is this happening?
Operational Impact
Key Findings
Recommended Actions

Deployment and operational context:
{context}

User question:
{question}
"""

    try:
        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt
        )

        return response.output_text

    except Exception:
        return None