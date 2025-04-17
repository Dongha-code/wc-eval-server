import random
import json
import openai
from openai import OpenAI

client = OpenAI()

# 사용자별 상태 저장 (메모리)
user_sessions = {}

def initialize_step_sequence():
    step_labels = [f"STEP {i}" for i in range(1, 10)]
    sequence = []
    while len(sequence) < 30:
        random.shuffle(step_labels)
        sequence.extend(step_labels)
    return sequence[:30]

def generate_next_step(email, current_index):
    if email not in user_sessions:
        user_sessions[email] = {
            "step_sequence": initialize_step_sequence()
        }

    sequence = user_sessions[email]["step_sequence"]
    if current_index >= len(sequence):
        return None  # 범위 초과 방지

    return sequence[current_index]

def load_step_context(step_label):
    filename = f"{step_label.lower().replace(' ', '_')}.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["context"]
    except Exception:
        return None

def generate_next_question(prompt_template, context):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception:
        return None
