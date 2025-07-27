import google.generativeai as genai
from flowchart_ai.config import GEMINI_API_KEY
import logging

logger = logging.getLogger('flowchart_llm')
genai.configure(api_key=GEMINI_API_KEY)

def generate_flowchart_from_code(code_content: str) -> str:
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""Analyze the following code and generate a Mermaid flowchart syntax that represents the main logic flow, including functions, conditional statements, loops, and significant operations. The output should be ONLY the Mermaid syntax, enclosed in a markdown code block (```mermaid ... ```). Do not include any other text or markdown outside this block.

Code:
'''
{code_content}
'''

Example Mermaid syntax:
```mermaid
graph TD
    A[Start] --> B{{Is it cold?}}
    B -- Yes --> C[Put on a jacket]
    B -- No --> D[Go outside]
    C --> E[End]
    D --> E
```
"""

    logger.info("Sending request to Gemini model.")
    logger.debug(f"Prompt: {prompt}")
    response = model.generate_content(prompt)
    logger.info("Received response from Gemini model.")
    logger.debug(f"Raw model output: {response.text}")

    # Extract the Mermaid code block
    mermaid_code = response.text.strip()
    if mermaid_code.startswith("```mermaid") and mermaid_code.endswith("```"):
        mermaid_code = mermaid_code[len("```mermaid\n"): -len("\n```")].strip()
    
    logger.info("Extracted Mermaid code.")
    logger.debug(f"Extracted Mermaid: {mermaid_code}")
    return mermaid_code

