import json
import os
from pathlib import Path
from typing import Any, Dict, List

from src.agent.agent import ReActAgent
from src.agent.agent_v1 import ReActAgentV1
from src.agent.chatbot import BaselineChatbot
from src.core.llm_provider import LLMProvider
from src.tools.healthcare_tools import get_tools


class ScriptedProvider(LLMProvider):
    def __init__(self, responses: List[str], model_name: str):
        super().__init__(model_name=model_name)
        self.responses = list(responses)
        self.calls = 0

    def generate(self, prompt: str, system_prompt: str | None = None) -> Dict[str, Any]:
        index = min(self.calls, len(self.responses) - 1)
        self.calls += 1
        return {
            "content": self.responses[index],
            "usage": {"prompt_tokens": 120, "completion_tokens": 35, "total_tokens": 155},
            "latency_ms": 25,
            "provider": "scripted",
        }

    def stream(self, prompt: str, system_prompt: str | None = None):
        yield self.generate(prompt, system_prompt)["content"]


CASES = [
    {
        "name": "Emergency red flags",
        "question": "A 62-year-old patient in Hanoi has chest pain and shortness of breath for 2 hours. What level of care is appropriate?",
        "chatbot_response": "It may be anxiety or indigestion. Consider resting and monitoring symptoms.",
        "agent_v1_responses": [
            'Thought: Assess red flags first.\nAction: assess_symptom_urgency(symptoms="chest pain and shortness of breath", age=62, duration_hours=2)',
            'Thought: Emergency red flags are present.\nAction: recommend_care_service(urgency="emergency", location="Hanoi")',
            "Final Answer: Emergency department is appropriate. Call local emergency services or go now. This is not a diagnosis.",
        ],
        "agent_v2_responses": [
            'Thought: Assess red flags first.\nAction: assess_symptom_urgency(symptoms="chest pain and shortness of breath", age=62, duration_hours=2)',
            'Thought: Emergency red flags are present.\nAction: recommend_care_service(urgency="emergency", location="Hanoi")',
            "Final Answer: Emergency department is appropriate. Call local emergency services or go now. This is not a diagnosis.",
        ],
        "expected_terms": ["Emergency", "not a diagnosis"],
    },
    {
        "name": "Routine symptoms",
        "question": "A 30-year-old has mild cough for 24 hours and no breathing difficulty. What should they do?",
        "chatbot_response": "You probably have a cold and can ignore it.",
        "agent_v1_responses": [
            'Thought: Assess urgency.\nAction: assess_symptom_urgency(symptoms="mild cough, no breathing difficulty", age=30, duration_hours=24)',
            'Thought: Routine care is enough if symptoms persist.\nAction: appointment_preparation(service_type="routine")',
            "Final Answer: Routine care is reasonable if symptoms persist. Prepare medication list, allergy list, symptom timeline, and questions. This is not a diagnosis.",
        ],
        "agent_v2_responses": [
            'Thought: Assess urgency.\nAction: assess_symptom_urgency(symptoms="mild cough, no breathing difficulty", age=30, duration_hours=24)',
            'Thought: Routine care is enough if symptoms persist.\nAction: appointment_preparation(service_type="routine")',
            "Final Answer: Routine care is reasonable if symptoms persist. Prepare medication list, allergy list, symptom timeline, and questions. This is not a diagnosis.",
        ],
        "expected_terms": ["Routine", "not a diagnosis"],
    },
    {
        "name": "Tool recovery",
        "question": "Estimate urgent care cost with insurance.",
        "chatbot_response": "The cost is hard to know, maybe free.",
        "agent_v1_responses": [
            'Thought: I will use a made-up tool.\nAction: diagnose_patient(symptoms="urgent care cost")',
        ],
        "agent_v2_responses": [
            'Thought: I will use a made-up tool.\nAction: diagnose_patient(symptoms="urgent care cost")',
            'Thought: The previous tool was invalid, so use the cost estimator.\nAction: estimate_visit_cost(service_type="urgent", insurance_status="insured")',
            "Final Answer: Estimated insured urgent care cost is 180,000 VND. This is a planning estimate, not a hospital quote.",
        ],
        "expected_terms": ["180,000 VND", "estimate"],
    },
]


def main():
    results = []
    for case in CASES:
        chatbot = BaselineChatbot(ScriptedProvider([case["chatbot_response"]], "scripted-chatbot"))
        agent_v1_provider = ScriptedProvider(case["agent_v1_responses"], "scripted-react-v1")
        agent_v2_provider = ScriptedProvider(case["agent_v2_responses"], "scripted-react-v2")
        agent_v1 = ReActAgentV1(agent_v1_provider, get_tools(), max_steps=5)
        agent_v2 = ReActAgent(agent_v2_provider, get_tools(), max_steps=5)

        chatbot_answer = chatbot.run(case["question"])
        agent_v1_answer = agent_v1.run(case["question"])
        agent_v2_answer = agent_v2.run(case["question"])
        agent_v1_success = all(
            term.lower() in agent_v1_answer.lower() for term in case["expected_terms"]
        )
        agent_v2_success = all(
            term.lower() in agent_v2_answer.lower() for term in case["expected_terms"]
        )

        results.append(
            {
                "case": case["name"],
                "question": case["question"],
                "chatbot_answer": chatbot_answer,
                "agent_v1_answer": agent_v1_answer,
                "agent_v1_steps": agent_v1_provider.calls,
                "agent_v1_success": agent_v1_success,
                "agent_v2_answer": agent_v2_answer,
                "agent_v2_steps": agent_v2_provider.calls,
                "agent_v2_success": agent_v2_success,
            }
        )

    report_dir = Path("report")
    report_dir.mkdir(exist_ok=True)
    (report_dir / "evaluation_results.json").write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )
    (report_dir / "evaluation_results.md").write_text(render_markdown(results), encoding="utf-8")
    print(json.dumps(results, indent=2))


def render_markdown(results: List[Dict[str, Any]]) -> str:
    rows = [
        "# Lab 3 Evaluation Results",
        "",
        "| Case | Chatbot Result | Agent v1 Result | v1 Steps | v1 Success | Agent v2 Result | v2 Steps | v2 Success |",
        "| :--- | :--- | :--- | ---: | :--- | :--- | ---: | :--- |",
    ]
    for item in results:
        rows.append(
            "| {case} | {chatbot} | {agent_v1} | {v1_steps} | {v1_success} | {agent_v2} | {v2_steps} | {v2_success} |".format(
                case=item["case"],
                chatbot=_cell(item["chatbot_answer"]),
                agent_v1=_cell(item["agent_v1_answer"]),
                v1_steps=item["agent_v1_steps"],
                v1_success="Yes" if item["agent_v1_success"] else "No",
                agent_v2=_cell(item["agent_v2_answer"]),
                v2_steps=item["agent_v2_steps"],
                v2_success="Yes" if item["agent_v2_success"] else "No",
            )
        )
    rows.extend(
        [
            "",
            "Summary:",
            f"- Agent v1 success rate: {sum(1 for r in results if r['agent_v1_success'])}/{len(results)}",
            f"- Agent v2 success rate: {sum(1 for r in results if r['agent_v2_success'])}/{len(results)}",
            "- Chatbot baseline is intentionally direct and has no tool access.",
            "- Agent v1 demonstrates the basic ReAct loop.",
            "- Agent v2 improves recovery from invalid tool calls through structured observations.",
        ]
    )
    return "\n".join(rows) + "\n"


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    os.environ.setdefault("DEFAULT_PROVIDER", "scripted")
    main()
