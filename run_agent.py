import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(override: bool = False) -> None:
        """Small fallback so --demo can run before dependencies are installed."""
        env_path = Path(".env")
        if not env_path.exists():
            return

        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if override or key not in os.environ:
                os.environ[key] = value

from src.agent.agent import ReActAgent
from src.agent.agent_v1 import ReActAgentV1
from src.agent.chatbot import BaselineChatbot
from src.core.llm_provider import LLMProvider
from src.tools.healthcare_tools import get_tools


class DemoProvider(LLMProvider):
    """Deterministic provider for running the lab without external API quota."""

    def __init__(self):
        super().__init__(model_name="demo-react-provider")
        self.calls = 0

    def generate(self, prompt: str, system_prompt: str | None = None) -> Dict[str, Any]:
        self.calls += 1
        prompt_lower = prompt.lower()
        system_prompt_lower = (system_prompt or "").lower()
        question = self._extract_question(prompt)
        quoted_question = json.dumps(question, ensure_ascii=False)

        if "without using external tools" in system_prompt_lower:
            content = self._direct_chatbot_answer(question)
        elif "observation:" not in prompt_lower:
            content = (
                "Thought: I should first assess whether the symptoms contain emergency red flags.\n"
                f"Action: assess_symptom_urgency(symptoms={quoted_question}, age=0, duration_hours=0)"
            )
        elif "urgency: emergency" in prompt_lower and "recommended service" not in prompt_lower:
            content = (
                "Thought: The urgency is emergency, so I should recommend the right care service.\n"
                'Action: recommend_care_service(urgency="emergency", location="Hanoi")'
            )
        elif "urgency: routine" in prompt_lower and "preparation:" not in prompt_lower:
            content = (
                "Thought: No emergency red flag was detected, so I should give routine preparation guidance.\n"
                'Action: appointment_preparation(service_type="routine")'
            )
        elif "recommended service" in prompt_lower:
            latest_observation = prompt.split("Observation:")[-1].strip()
            content = (
                "Thought: I have the triage and service recommendation.\n"
                f"Final Answer: {latest_observation} This is not a diagnosis; seek professional medical care."
            )
        elif "preparation:" in prompt_lower:
            latest_observation = prompt.split("Observation:")[-1].strip()
            content = (
                "Thought: I have routine care guidance and preparation details.\n"
                f"Final Answer: Routine care is reasonable if symptoms persist or worsen. {latest_observation} "
                "This is not a diagnosis."
            )
        else:
            content = "Final Answer: I could not find enough tool data to answer."

        return {
            "content": content,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "latency_ms": 0,
            "provider": "demo",
        }

    def stream(self, prompt: str, system_prompt: str | None = None):
        yield self.generate(prompt, system_prompt)["content"]

    def _extract_question(self, prompt: str) -> str:
        marker = "Question:"
        if marker not in prompt:
            return prompt.strip()
        question = prompt.split(marker, 1)[1].split("\n\nBegin.", 1)[0]
        return question.strip()

    def _direct_chatbot_answer(self, question: str) -> str:
        text = question.lower()
        red_flags = [
            "đau ngực",
            "khó thở",
            "không tỉnh táo",
            "ngất",
            "co giật",
            "đột quỵ",
            "bất tỉnh",
        ]
        if any(flag in text for flag in red_flags):
            return (
                "Bạn nên đi cấp cứu hoặc gọi dịch vụ khẩn cấp ngay, vì đây có thể là dấu hiệu nguy hiểm. "
                "Đây không phải là chẩn đoán y khoa."
            )
        return (
            "Bạn nên theo dõi triệu chứng và đặt lịch khám nếu tình trạng kéo dài hoặc nặng hơn. "
            "Đây không phải là chẩn đoán y khoa."
        )


def build_provider():
    provider = os.getenv("DEFAULT_PROVIDER", "openai").strip().lower()
    model = os.getenv("DEFAULT_MODEL", "").strip()

    if provider == "demo":
        return DemoProvider()

    if provider == "openai":
        from src.core.openai_provider import OpenAIProvider

        return OpenAIProvider(
            model_name=model or "gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    if provider in {"google", "gemini"}:
        from src.core.gemini_provider import GeminiProvider

        return GeminiProvider(
            model_name=model or "gemini-2.5-flash",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

    if provider == "local":
        from src.core.local_provider import LocalProvider

        return LocalProvider(model_path=os.getenv("LOCAL_MODEL_PATH", ""))

    raise ValueError(
        f"Unsupported DEFAULT_PROVIDER={provider}. Use demo, openai, google/gemini, or local."
    )


def main():
    load_dotenv(override=True)

    parser = argparse.ArgumentParser(description="Run Lab 3 chatbot or ReAct agent.")
    parser.add_argument(
        "question",
        nargs="*",
        help="Question/task for the agent. If omitted, an example task is used.",
    )
    parser.add_argument(
        "--chatbot",
        action="store_true",
        help="Run baseline chatbot instead of the ReAct agent.",
    )
    parser.add_argument(
        "--agent-v1",
        action="store_true",
        help="Run the first ReAct agent version instead of the improved v2 agent.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=5,
        help="Maximum ReAct steps before stopping.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with a deterministic offline provider instead of an API provider.",
    )
    args = parser.parse_args()

    if args.demo:
        os.environ["DEFAULT_PROVIDER"] = "demo"

    question = " ".join(args.question).strip() or (
        "A 62-year-old patient in Hanoi has chest pain and shortness of breath for 2 hours. "
        "What level of care is appropriate?"
    )

    llm = build_provider()
    if args.chatbot:
        app = BaselineChatbot(llm)
        mode = "chatbot"
    elif args.agent_v1:
        app = ReActAgentV1(llm, get_tools(), args.max_steps)
        mode = "react-agent-v1"
    else:
        app = ReActAgent(llm, get_tools(), args.max_steps)
        mode = "react-agent-v2"

    print(f"Question: {question}")
    print(f"Provider: {os.getenv('DEFAULT_PROVIDER', 'openai')}")
    print(f"Model: {getattr(llm, 'model_name', 'unknown')}")
    print("Mode:", mode)
    print("Answer:")
    try:
        print(app.run(question))
    except RuntimeError as exc:
        print(f"Provider error: {exc}")
        print("Tip: for a guaranteed offline lab run, use: python run_agent.py --demo \"your question\"")


if __name__ == "__main__":
    main()
