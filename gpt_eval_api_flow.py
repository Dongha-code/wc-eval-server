import os, json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load step contexts
step_contexts = {}
for i in range(1, 10):
    with open(f"step_{i}.json", encoding="utf-8") as f:
        step_contexts[f"STEP {i}"] = json.load(f)

def create_step_sequence(total_questions=30):
    import random
    steps = [f"STEP {i}" for i in range(1, 10)]
    full_sequence = []
    while len(full_sequence) < total_questions:
        batch = steps.copy()
        random.shuffle(batch)
        full_sequence.extend(batch)
    return full_sequence[:total_questions]

def generate_question(step):
    context = step_contexts[step]["context"]
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "너는 한국어 문제를 출제하는 평가 시스템이야."},
            {"role": "user", "content": context}
        ],
        functions=[{
            "name": "generate_quiz_question",
            "parameters": {
                "type": "object",
                "properties": {
                    "step": {"type": "string"},
                    "context": {"type": "string"}
                },
                "required": ["step", "context"]
            }
        }],
        function_call={"name": "generate_quiz_question"}
    )
    args = json.loads(response.choices[0].message.function_call.arguments)
    return {
        "step": step,
        "question": args["context"]
    }

def evaluate_answer(question, answer, step):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "넌 WiseCollector 평가자야. 반드시 한국어로 평가 피드백을 줘."},
            {"role": "user", "content": f"[{step} 문제]\n{question}\n\n[응답]\n{answer}"}
        ],
        functions=[{
            "name": "submit_answer",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                    "step": {"type": "string"}
                },
                "required": ["question", "answer", "step"]
            }
        }],
        function_call={"name": "submit_answer"}
    )
    return json.loads(response.choices[0].message.function_call.arguments)

def generate_report(name, email, answers):
    return {
        "이름": name,
        "이메일": email,
        "응답수": len(answers),
        "피드백": answers
    }
