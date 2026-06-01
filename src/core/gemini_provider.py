import time
from typing import Any, Dict, Generator, Optional

from google import genai
from google.genai import errors

from src.core.llm_provider import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        self.client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )
        except errors.ServerError as exc:
            raise RuntimeError(
                f"Gemini API is temporarily unavailable or overloaded ({self._format_api_error(exc)}). "
                "Try again later, use --demo for the lab demo, or switch to another available Gemini model."
            ) from exc
        except errors.ClientError as exc:
            raise RuntimeError(
                f"Gemini API request failed ({self._format_api_error(exc)}). "
                "Check your API key, quota, and DEFAULT_MODEL in .env."
            ) from exc

        latency_ms = int((time.time() - start_time) * 1000)
        usage = self._extract_usage(response)

        return {
            "content": getattr(response, "text", "").strip(),
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "gemini",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

        response = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=full_prompt,
        )
        for chunk in response:
            text = getattr(chunk, "text", "")
            if text:
                yield text

    def _extract_usage(self, response: Any) -> Dict[str, int]:
        metadata = getattr(response, "usage_metadata", None)
        prompt_tokens = int(getattr(metadata, "prompt_token_count", 0) or 0)
        completion_tokens = int(getattr(metadata, "candidates_token_count", 0) or 0)
        total_tokens = int(getattr(metadata, "total_token_count", 0) or 0)

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    def _format_api_error(self, exc: Exception) -> str:
        status_code = getattr(exc, "status_code", None)
        response_json = getattr(exc, "response_json", None)
        message = None

        if isinstance(response_json, dict):
            error = response_json.get("error", {})
            if isinstance(error, dict):
                message = error.get("message") or error.get("status")

        if not message:
            message = str(exc)

        message = " ".join(str(message).split())
        if len(message) > 220:
            message = f"{message[:217]}..."
        if status_code:
            return f"{status_code}: {message}"
        return message
