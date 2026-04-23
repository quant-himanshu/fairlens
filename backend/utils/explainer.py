import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def explain_bias_with_gemini(metric_name, value):
    prompt = f"Explain the AI bias metric '{metric_name}' with value {value}. Two simple sentences for a non-technical user."
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Explanation unavailable: {str(e)}"
