# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Enter real name before submission
- **Student ID**: Enter student ID before submission
- **Date**: 2026-06-01

---

## I. Technical Contribution

- **Modules Implemented**:
  - `src/agent/agent.py`: completed the ReAct loop.
  - `src/agent/chatbot.py`: added a direct chatbot baseline.
  - `src/tools/healthcare_tools.py`: added deterministic healthcare triage support tools.
  - `tests/test_agent.py`: added unit tests with a fake LLM provider.

- **Code Highlights**:
  - The agent supports both `Action: tool(arg=value)` and JSON action formats.
  - Tool execution uses a registry and function signatures rather than hard-coded if/else branches.
  - Invalid tool names, parser failures, tool errors, token usage, latency, and loop count are logged.

- **Documentation**:
  - The ReAct agent receives a system prompt containing tool descriptions and strict output rules.
  - Every observation is appended back into the prompt, allowing the model to correct mistakes on the next step.

---

## II. Debugging Case Study

- **Problem Description**: The agent may hallucinate a tool, for example `Action: diagnose_patient(symptoms="cough")`.
- **Log Source**: `UNKNOWN_TOOL` event in `logs/YYYY-MM-DD.log`.
- **Diagnosis**: The model did not follow the available tool list. Without validation, the agent could crash or fabricate an answer.
- **Solution**: `_execute_tool` now checks the tool registry and returns a clear observation listing available tools. The loop then feeds this observation back to the LLM so it can choose a valid tool.

Another handled failure is malformed output. If the model does not return an `Action:` or `Final Answer:`, the agent logs `PARSER_ERROR` and asks for the exact expected format through the next observation.

---

## III. Personal Insights: Chatbot vs ReAct

1. **Reasoning**: A chatbot answers from model memory and prompt context only. The ReAct agent separates reasoning from acting, so it can decide which external function is needed before answering.
2. **Reliability**: The agent can be worse than a chatbot for simple questions because it adds latency, token cost, and possible parser/tool-call errors.
3. **Observation**: Observations are the key difference. They turn a single-shot answer into an iterative process where the model can use real tool output instead of guessing.

---

## IV. Future Improvements

- **Scalability**: Add async tool execution and a formal tool registry with schemas.
- **Safety**: Add a supervisor step to approve risky tool calls before execution.
- **Performance**: Cache repeated tool results and use smaller prompts after the first step.
- **RAG Extension**: Add retrieval tools backed by a vector database for product manuals, FAQs, or policy documents.
- **Healthcare Safety**: Add clinician-reviewed knowledge, stronger disclaimers, and escalation rules for red-flag symptoms.
- **Evaluation**: Build a benchmark table comparing chatbot vs agent across simple, multi-step, and adversarial prompts.
