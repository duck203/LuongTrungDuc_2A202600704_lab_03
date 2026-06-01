import ast
import inspect
import re
from typing import Any, Dict, List, Optional, Tuple

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgentV1:
    """
    First working ReAct implementation for comparison.

    This version supports the basic Thought/Action/Observation loop, but it is
    intentionally less robust than Agent v2: it only parses function-call style
    actions and stops immediately on parser/tool errors.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: List[Dict[str, Any]] = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            f"- {tool['name']}: {tool.get('description', '')}" for tool in self.tools
        )
        return f"""You are a ReAct agent.

Available tools:
{tool_descriptions}

Use this format:
Thought: brief reasoning.
Action: tool_name(arg1="value", arg2=123)

When finished, write:
Final Answer: answer for the user.
"""

    def run(self, user_input: str) -> str:
        logger.log_event(
            "AGENT_V1_START",
            {"input": user_input, "model": getattr(self.llm, "model_name", "unknown")},
        )
        prompt = f"Question: {user_input}\n\nBegin."

        for step in range(1, self.max_steps + 1):
            result = self.llm.generate(prompt, system_prompt=self.get_system_prompt())
            content = result.get("content", "").strip()
            usage = result.get("usage", {})
            latency_ms = result.get("latency_ms", 0)
            provider = result.get("provider", self.llm.__class__.__name__)

            tracker.track_request(provider, self.llm.model_name, usage, latency_ms)
            logger.log_event(
                "AGENT_V1_STEP",
                {
                    "step": step,
                    "llm_output": content,
                    "latency_ms": latency_ms,
                    "usage": usage,
                },
            )
            self.history.append({"role": "assistant", "content": content})

            final_answer = self._extract_final_answer(content)
            if final_answer:
                logger.log_event("AGENT_V1_END", {"steps": step, "status": "success"})
                return final_answer

            parsed_action = self._parse_action(content)
            if not parsed_action:
                logger.log_event("AGENT_V1_PARSER_ERROR", {"step": step, "content": content})
                return "Agent v1 failed: could not parse a valid Action."

            tool_name, args, kwargs = parsed_action
            observation = self._execute_tool(tool_name, args, kwargs)
            if observation.startswith("Agent v1 failed:"):
                logger.log_event("AGENT_V1_END", {"steps": step, "status": "failed"})
                return observation

            self.history.append({"role": "observation", "content": observation})
            prompt = f"{prompt}\n{content}\nObservation: {observation}\n"

        logger.log_event("AGENT_V1_END", {"steps": self.max_steps, "status": "timeout"})
        return "Agent v1 failed: max steps exceeded."

    def _execute_tool(self, tool_name: str, args: List[Any], kwargs: Dict[str, Any]) -> str:
        tool = self._find_tool(tool_name)
        if not tool:
            logger.log_event("AGENT_V1_UNKNOWN_TOOL", {"tool": tool_name})
            return f"Agent v1 failed: unknown tool '{tool_name}'."

        func = tool.get("func") or tool.get("function") or tool.get("callable")
        if not callable(func):
            logger.log_event("AGENT_V1_TOOL_ERROR", {"tool": tool_name, "error": "not callable"})
            return f"Agent v1 failed: tool '{tool_name}' is not callable."

        try:
            call_kwargs = self._coerce_call_arguments(func, args, kwargs)
            observation = str(func(**call_kwargs))
            logger.log_event(
                "AGENT_V1_TOOL_CALL",
                {"tool": tool_name, "args": call_kwargs, "observation": observation},
            )
            return observation
        except Exception as exc:
            logger.log_event("AGENT_V1_TOOL_ERROR", {"tool": tool_name, "error": str(exc)})
            return f"Agent v1 failed: tool '{tool_name}' raised {exc}."

    def _parse_action(self, content: str) -> Optional[Tuple[str, List[Any], Dict[str, Any]]]:
        match = re.search(
            r"Action\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*(?:\n|$)",
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return None
        tool_name = match.group(1).strip()
        raw_args = match.group(2).strip()
        args, kwargs = self._parse_function_args(raw_args)
        return tool_name, args, kwargs

    def _parse_function_args(self, raw_args: str) -> Tuple[List[Any], Dict[str, Any]]:
        if not raw_args:
            return [], {}

        parsed = ast.parse(f"_tool_call({raw_args})", mode="eval")
        call = parsed.body
        if not isinstance(call, ast.Call):
            return [], {}

        args = [ast.literal_eval(arg) for arg in call.args]
        kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in call.keywords if kw.arg}
        return args, kwargs

    def _coerce_call_arguments(
        self,
        func: Any,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        signature = inspect.signature(func)
        bound = signature.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        return dict(bound.arguments)

    def _extract_final_answer(self, content: str) -> Optional[str]:
        match = re.search(r"Final Answer\s*:\s*(.+)", content, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return match.group(1).strip()

    def _find_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        normalized = tool_name.lower()
        for tool in self.tools:
            if tool.get("name", "").lower() == normalized:
                return tool
        return None

