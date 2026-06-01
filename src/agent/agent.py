import ast
import inspect
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgent:
    """
    ReAct-style agent that repeatedly asks an LLM for a Thought/Action,
    executes the requested tool, feeds the Observation back, then stops on
    Final Answer or max_steps.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: List[Dict[str, Any]] = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [
                (
                    f"- {tool['name']}: {tool.get('description', '')}\n"
                    f"  Input: {tool.get('args_schema', 'tool_name(arg=value, ...)')}"
                )
                for tool in self.tools
            ]
        )

        return f"""You are a careful ReAct agent. Solve the user task by reasoning and using tools.

Available tools:
{tool_descriptions}

Rules:
- Use tools when the answer depends on facts, calculations, or environment state.
- Use only tool names from the list above.
- For healthcare questions, do not diagnose or replace a clinician. Recommend emergency care when red flags are present.
- Use this exact format:
Thought: brief reasoning about the next step.
Action: tool_name(arg1="value", arg2=123)
- After you receive an Observation, continue with another Thought/Action or finish.
- When you know the answer, write:
Final Answer: concise answer for the user.
- Do not invent observations. Do not call the same failing action repeatedly.
"""

    def run(self, user_input: str) -> str:
        logger.log_event(
            "AGENT_START",
            {"input": user_input, "model": getattr(self.llm, "model_name", "unknown")},
        )

        prompt = self._build_initial_prompt(user_input)
        final_answer: Optional[str] = None

        for step in range(1, self.max_steps + 1):
            result = self.llm.generate(prompt, system_prompt=self.get_system_prompt())
            content = result.get("content", "").strip()
            usage = result.get("usage", {})
            latency_ms = result.get("latency_ms", 0)
            provider = result.get("provider", self.llm.__class__.__name__)

            tracker.track_request(provider, self.llm.model_name, usage, latency_ms)
            logger.log_event(
                "AGENT_STEP",
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
                logger.log_event("AGENT_FINAL", {"steps": step, "answer": final_answer})
                logger.log_event("AGENT_END", {"steps": step, "status": "success"})
                return final_answer

            parsed_action = self._parse_action(content)
            if not parsed_action:
                observation = (
                    "Parser error: no valid Action found. Use exactly "
                    'Action: tool_name(arg="value") or Final Answer: ...'
                )
                logger.log_event("PARSER_ERROR", {"step": step, "content": content})
            else:
                tool_name, args, kwargs = parsed_action
                observation = self._execute_tool(tool_name, args=args, kwargs=kwargs)

            self.history.append({"role": "observation", "content": observation})
            prompt = self._append_observation(prompt, content, observation)

        timeout_answer = (
            "I could not complete the task within the allowed reasoning steps. "
            "Please try again with a narrower question."
        )
        logger.log_event(
            "AGENT_END",
            {"steps": self.max_steps, "status": "max_steps_exceeded"},
        )
        return timeout_answer

    def _execute_tool(
        self,
        tool_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> str:
        args = args or []
        kwargs = kwargs or {}

        tool = self._find_tool(tool_name)
        if not tool:
            message = f"Tool error: unknown tool '{tool_name}'. Available tools: {self._tool_names()}."
            logger.log_event("UNKNOWN_TOOL", {"tool": tool_name, "args": args, "kwargs": kwargs})
            return message

        func = tool.get("func") or tool.get("function") or tool.get("callable")
        if not callable(func):
            message = f"Tool error: tool '{tool_name}' has no callable function."
            logger.log_event("TOOL_ERROR", {"tool": tool_name, "error": message})
            return message

        try:
            call_kwargs = self._coerce_call_arguments(func, args, kwargs)
            result = func(**call_kwargs)
            observation = str(result)
            logger.log_event(
                "TOOL_CALL",
                {
                    "tool": tool_name,
                    "args": call_kwargs,
                    "observation": observation,
                    "status": "success",
                },
            )
            return observation
        except Exception as exc:
            message = f"Tool error in '{tool_name}': {exc}"
            logger.log_event(
                "TOOL_ERROR",
                {"tool": tool_name, "args": args, "kwargs": kwargs, "error": str(exc)},
            )
            return message

    def _build_initial_prompt(self, user_input: str) -> str:
        return f"Question: {user_input}\n\nBegin."

    def _append_observation(self, prompt: str, llm_output: str, observation: str) -> str:
        return f"{prompt}\n{llm_output}\nObservation: {observation}\n"

    def _extract_final_answer(self, content: str) -> Optional[str]:
        match = re.search(r"Final Answer\s*:\s*(.+)", content, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return match.group(1).strip()

    def _parse_action(self, content: str) -> Optional[Tuple[str, List[Any], Dict[str, Any]]]:
        cleaned = self._strip_code_fences(content)
        json_action = self._parse_json_action(cleaned)
        if json_action:
            return json_action

        match = re.search(
            r"Action\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*(?:\n|$)",
            cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return None

        tool_name = match.group(1).strip()
        raw_args = match.group(2).strip()
        args, kwargs = self._parse_function_args(raw_args)
        return tool_name, args, kwargs

    def _parse_json_action(self, content: str) -> Optional[Tuple[str, List[Any], Dict[str, Any]]]:
        match = re.search(r"Action\s*:\s*(\{.*\})", content, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None

        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

        tool_name = payload.get("tool") or payload.get("name") or payload.get("action")
        raw_args = payload.get("args", {})
        if not tool_name:
            return None
        if isinstance(raw_args, dict):
            return str(tool_name), [], raw_args
        if isinstance(raw_args, list):
            return str(tool_name), raw_args, {}
        return str(tool_name), [raw_args], {}

    def _parse_function_args(self, raw_args: str) -> Tuple[List[Any], Dict[str, Any]]:
        if not raw_args:
            return [], {}

        try:
            parsed = ast.parse(f"_tool_call({raw_args})", mode="eval")
            call = parsed.body
            if not isinstance(call, ast.Call):
                return [], {}

            args = [self._literal_or_name(arg) for arg in call.args]
            kwargs = {kw.arg: self._literal_or_name(kw.value) for kw in call.keywords if kw.arg}
            return args, kwargs
        except SyntaxError:
            return [raw_args.strip().strip("\"'")], {}

    def _literal_or_name(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Name):
            return node.id
        return ast.literal_eval(node)

    def _coerce_call_arguments(
        self,
        func: Any,
        args: List[Any],
        kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        signature = inspect.signature(func)
        bound = signature.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        missing = [
            name
            for name, param in signature.parameters.items()
            if name not in bound.arguments and param.default is inspect.Parameter.empty
        ]
        if missing:
            raise ValueError(f"missing required argument(s): {', '.join(missing)}")
        return dict(bound.arguments)

    def _find_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        normalized = tool_name.lower()
        for tool in self.tools:
            if tool.get("name", "").lower() == normalized:
                return tool
        return None

    def _tool_names(self) -> str:
        return ", ".join(tool.get("name", "<unnamed>") for tool in self.tools)

    def _strip_code_fences(self, content: str) -> str:
        return re.sub(r"```(?:json|python)?\s*|\s*```", "", content).strip()
