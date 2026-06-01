from typing import Any, Dict

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class BaselineChatbot:
    """
    Minimal no-tool chatbot baseline. It is useful for comparing direct LLM
    answers against the ReAct agent on multi-step tasks.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def run(self, user_input: str) -> str:
        logger.log_event(
            "CHATBOT_START",
            {"input": user_input, "model": getattr(self.llm, "model_name", "unknown")},
        )

        result: Dict[str, Any] = self.llm.generate(
            user_input,
            system_prompt=(
                "You are a helpful assistant. Answer directly without using external tools."
            ),
        )
        tracker.track_request(
            result.get("provider", self.llm.__class__.__name__),
            self.llm.model_name,
            result.get("usage", {}),
            result.get("latency_ms", 0),
        )

        answer = result.get("content", "").strip()
        logger.log_event("CHATBOT_END", {"answer": answer})
        return answer
