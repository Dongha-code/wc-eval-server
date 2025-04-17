# GPT 기반 자동 평가 대화 흐름 (Flask API 연동 포함)

import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import requests
import random

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
WEBHOOK_URL = os.getenv("GOOGLE_SHEETS_WEBHOOK")

# STEP별 context 사전 로딩
step_contexts = {}
for i in range(1, 10):
    with open(f"step_{i}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        step_contexts[f"STEP {i}"] = data["context"]

# 문제 시퀀스 생성 (30문제)
def generate_step_sequence():
    base = [f"STEP {i}" for i in range(1, 10)]
    sequence = []
    while len(sequence) < 30:
        random.shuffle(base)
        sequence.extend(base)
    return sequence[:30]

# 사용자 세션
session = {
    "name": None,
    "email": None,
    "current": 0,
    "step_sequence": generate_step_sequence(),
    "answers": [],
    "questions": []
}

def generate_next_question():
    step = session["step_sequence"][session["current"]]
    context = step_contexts[step]

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "너는 WiseCollector 진단 문제 출제자야. 반드시 한국어로 문제를 만들어야 해."},
            {"role": "user", "content": f"{step} 학습 내용을 기반으로 실무형 문제를 생성해줘:\n\n{context}"}
        ],
        functions=[{
            "name": "generate_quiz_question",
            "parameters": {
                "type": "object",
                "properties": {
                    "step": {"type": "string"},
                    "context": {"type": "string"},
                    "question": {"type": "string"}
                },
                "required": ["step", "context", "question"]
            }
        }],
        function_call={"name": "generate_quiz_question"},
        timeout=20
    )

    args = json.loads(response.choices[0].message.function_call.arguments)
    question = {
        "step": step,
        "question": args["question"]
    }
    session["questions"].append(question)
    return question

def evaluate_answer(question, answer, step):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "넌 교육 평가자야. 반드시 한국어로 평가하고 피드백을 줘."},
            {"role": "user", "content": f"문제: {question}\n답변: {answer}"}
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
        function_call={"name": "submit_answer"},
        timeout=20
    )

    return json.loads(response.choices[0].message.function_call.arguments)

def generate_report(name, email, answers):
    messages = [
        {"role": "system", "content": "넌 진단 결과 리포트를 생성하는 GPT야. 반드시 한국어로 작성해."},
        {"role": "user", "content": f"다음은 {name}({email})의 진단 응답이야. 요약해줘.\n\n{json.dumps(answers, ensure_ascii=False)}"}
    ]
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        functions=[{
            "name": "generate_diagnostic_report",
            "parameters": {}
        }],
        function_call={"name": "generate_diagnostic_report"},
        timeout=20
    )
    return json.loads(response.choices[0].message.function_call.arguments)
