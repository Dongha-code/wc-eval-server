import random
import json
import openai
from openai import OpenAI
from gpt_function_schema import functions

client = OpenAI()

# 사용자 세션 저장소
user_sessions = {}

# STEP 시퀀스 생성 (중복 없이 섞어서 총 30개)
def generate_step_sequence():
    steps = [f"STEP {i}" for i in range(1, 10)]
    full_sequence = []
    while len(full_sequence) < 30:
        random.shuffle(steps)
        full_sequence.extend(steps)
    return full_sequence[:30]

# 사용자 세션 초기화
def init_user_session(name, email):
    user_sessions[email] = {
        "name": name,
        "email": email,
        "step_sequence": generate_step_sequence(),
        "current_index": 0,
        "answers": [],
        "next_question": None
    }

# 현재 STEP 추출
def get_current_step(email):
    user = user_sessions.get(email)
    if not user:
        return None
    idx = user["current_index"]
    if idx >= len(user["step_sequence"]):
        return None
    return user["step_sequence"][idx]

# STEP context 불러오기
def load_step_context(step_label):
    filename = f"{step_label.lower().replace(' ', '_')}.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)["context"]
    except:
        return None

# 문제 생성 (혼합형 중 택일)
def generate_quiz_question(step, context):
    system_prompt = f"""
너는 WiseCollector 2.0 운영 평가용 GPT 출제자입니다.

다음 조건을 따라 한 문항을 생성하세요:
- 하나의 유형만 생성 (선택형 또는 서술형 중 택일)
- 선택형일 경우 (A)(B)(C)(D) 형식으로 4개 보기 제시
- 절대로 정답을 포함하지 마세요
- 마크다운이나 주석(###, **정답**, **서술**) 없이 순수 질문만 생성
- 질문은 한국어로 생성

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

# 다음 문제 생성 및 캐시
def get_next_question(user):
    email = user["email"]
    step = get_current_step(email)
    context = load_step_context(step)
    question = generate_quiz_question(step, context)

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
        "total": 30,
        "complete": is_quiz_complete(email)
    }

# 답안 평가
def evaluate_answer(email, answer):
    user = user_sessions.get(email)
    if not user:
        return {"error": "세션 없음"}

    idx = user["current_index"] - 1
    question = user["answers"][idx]["question"]
    step = user["answers"][idx]["step"]

    prompt = f"""
다음은 {step}에 대한 학습자의 서술형 답변입니다. 다음 기준에 따라 평가하세요:
- 실무 적용 가능성
- 구체성
- 핵심 개념 포함 여부
- 개선 피드백 및 추천 방향 포함
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

        user["answers"][idx]["feedback"] = args

        return {
            "complete": is_quiz_complete(email),
            "step": step,
            "feedback": args
        }

    except Exception as e:
        return {"error": str(e)}

# 제출 답안을 저장하는 함수 (submit_user_answer)
def submit_user_answer(email, answer):
    user = user_sessions.get(email)
    if not user:
        return
    idx = user["current_index"] - 1
    if 0 <= idx < len(user["answers"]):
        user["answers"][idx]["answer"] = answer

# 완료 여부
def is_quiz_complete(email):
    return user_sessions[email]["current_index"] >= 30

# 결과 요약
def generate_report(email):
    user = user_sessions.get(email)
    if not user:
        return {"error": "세션 없음"}
    return {
        "name": user["name"],
        "email": user["email"],
        "answers": user["answers"]
    }
