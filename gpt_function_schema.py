functions = [
    {
        "name": "evaluate_answer",
        "description": "사용자의 서술형 답변을 평가하여 점수, 피드백, 추천 레벨을 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "score": {
                    "type": "integer",
                    "description": "답변의 평가 점수 (1~100점 기준)"
                },
                "feedback": {
                    "type": "string",
                    "description": "학습자에게 제공할 피드백. 개선점, 보완해야 할 점, 칭찬 등을 포함"
                },
                "recommendation": {
                    "type": "string",
                    "description": "학습자의 수준에 따라 추천하는 다음 학습 방향 또는 참고할 내용"
                },
                "level": {
                    "type": "string",
                    "enum": ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"],
                    "description": "학습자의 현재 이해도 수준을 구분한 등급. Level 1은 초급, Level 5는 고급"
                }
            },
            "required": ["score", "feedback", "recommendation", "level"]
        }
    }
]
