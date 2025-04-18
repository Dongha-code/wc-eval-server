import random
import json
import openai
from openai import OpenAI
from gpt_function_schema import functions

client = OpenAI()

# 사용자 세션 상태 저장
user_sessions = {}

# STEP 시퀀스 생성
def generate_step_sequence():
    steps = [f"STEP {i}" for i in range(1, 10)]
    full_sequence = []
    while len(full_sequence) < 30:
        random.shuffle(steps)
        full_sequence.extend(steps)
    return full_sequence[:30]

# 사용자 초기화
def init_user_session(name, email):
    user_sessions[email] = {
        "name": name,
        "email": email,
        "step_sequence": generate_step_sequence(),
        "current_index": 0,
        "answers": []
    }

# 현재 STEP 반환
def get_current_step(email):
    user = user_sessions.get(email)
    if not user:
        return None
    idx = user["current_index"]
    if idx >= len(user["step_sequence"]):
        return None
    return user["step_sequence"][idx]

# STEP context 로딩
def load_step_context(step_label):
    filename = f"{step_label.lower().replace(' ', '_')}.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)["context"]
    except:
        return None

# 혼합형 문제 생성
def generate_mixed_quiz_question(step, context):
    system_prompt = f"""
너는 WiseCollector 2.0 운영 평가용 GPT 출제자입니다.

다음 조건에 따라 "혼합형 문제" 1세트를 생성하세요:
- 현실적인 시나리오를 간단히 제시
- [선택형] 보기 4개 제공, 1개 정답
- [서술형] 관련 개념 또는 상황에 대해 자유롭게 서술
- 내용은 모두 한국어로 생성

STEP: {step}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[GPT 오류] {e}"

# 다음 문제 반환
def get_next_question(email):
    user = user_sessions.get(email)
    if not user:
        return {"error": "세션이 없습니다."}

    step = get_current_step(email)
    context = load_step_context(step)
    question = generate_mixed_quiz_question(step, context)

    user["answers"].append({
        "step": step,
        "question": question,
        "answer": None,
        "feedback": None
    })

    user["current_index"] += 1

    return {
        "step": step,
        "question": question,
        "number": user["current_index"],
        "total": 30
    }

# GPT Function Calling 기반 평가
def evaluate_answer(email, answer):
    user = user_sessions.get(email)
    if not user:
        return {"error": "세션이 없습니다."}

    idx = user["current_index"] - 1
    question = user["answers"][idx]["question"]
    step = user["answers"][idx]["step"]

    prompt = f"""
다음은 {step}에 대한 학습자 서술형 답변입니다. 다음 기준에 따라 평가해주세요:
- 실무 적용 가능성
- 구체성
- 핵심 개념 포함 여부
- 개선 피드백과 추천 방향 포함
"""

    try:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"📘 질문: {question}\n\n✍️ 학습자 답변: {answer}"}
        ]

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=0.5,
            functions=functions,
            function_call={"name": "evaluate_answer"}
        )

        args = json.loads(response.choices[0].message.function_call.arguments)

        user["answers"][idx]["answer"] = answer
        user["answers"][idx]["feedback"] = args

        return {
            "complete": is_quiz_complete(email),
            "step": step,
            "feedback": args
        }

    except Exception as e:
        return {"error": str(e)}

# 완료 여부
def is_quiz_complete(email):
    return user_sessions[email]["current_index"] >= 30

# 리포트 반환
def generate_report(email):
    user = user_sessions.get(email)
    if not user:
        return {"error": "세션 없음"}
    
    return {
        "name": user["name"],
        "email": user["email"],
        "answers": user["answers"]
    }
