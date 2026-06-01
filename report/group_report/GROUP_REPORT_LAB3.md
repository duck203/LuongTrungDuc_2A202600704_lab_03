# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Lab 3 Team
- **Team Members**: Enter real team members, student IDs, GitHub usernames, and commit links before submission
- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

This project compares a direct LLM chatbot baseline with a ReAct agent that can reason, call tools, observe results, and refine the next step in a healthcare triage support scenario. The final implementation includes a no-tool chatbot, a ReAct loop, healthcare tools, structured telemetry, parser guardrails, and automated tests.

- **Success Rate**: 100% on the local unit test suite (`5 passed`).
- **Key Outcome**: The agent can identify emergency red flags, recommend an appropriate care service, and avoid presenting the result as a diagnosis.
- **Evaluation Result**: Agent success rate was `3/3` in `report/evaluation_results.md`.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

Flow:

```text
User Question
  -> LLM Thought/Action
  -> Parse Action
  -> Execute Tool
  -> Append Observation
  -> Repeat
  -> Final Answer
```

The loop is implemented in `src/agent/agent.py`. It stops when the LLM emits `Final Answer:` or when `max_steps` is reached. Each step records LLM output, tool calls, parser failures, unknown tools, latency, and token metrics.

### 2.2 Agent v1 vs Agent v2

| Version | Behavior | Failure Observed | Improvement |
| :--- | :--- | :--- | :--- |
| Agent v1 | Basic parser and tool execution | Weak recovery from malformed actions and hallucinated tools | Added error observations and tool-name validation |
| Agent v2 | Parser guardrails, max-step stop, telemetry, healthcare safety prompt | Still requires model format compliance | Logs failures and gives the LLM a chance to repair |

### 2.3 Tool Definitions

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `assess_symptom_urgency` | `assess_symptom_urgency(symptoms="chest pain and shortness of breath", age=62, duration_hours=2)` | Classify emergency, urgent, or routine care level. |
| `recommend_care_service` | `recommend_care_service(urgency="emergency", location="Hanoi")` | Recommend the appropriate care service. |
| `estimate_visit_cost` | `estimate_visit_cost(service_type="urgent", insurance_status="insured")` | Estimate planning-level visit cost in VND. |
| `appointment_preparation` | `appointment_preparation(service_type="routine")` | List documents and information to prepare. |

### 2.4 LLM Providers Used

- **Primary**: Any `LLMProvider` implementation, such as OpenAI.
- **Secondary**: Gemini or local GGUF model through the same provider interface.
- **Testing Provider**: `FakeProvider` in `tests/test_agent.py`, used to validate logic without API keys.

---

## 3. Telemetry & Performance Dashboard

Telemetry is written by `src/telemetry/logger.py` and `src/telemetry/metrics.py`.

- **Latency**: captured per LLM request as `latency_ms`.
- **Token Usage**: captured as `prompt_tokens`, `completion_tokens`, and `total_tokens`.
- **Cost Estimate**: calculated from total tokens in `PerformanceTracker`.
- **Completion-to-Prompt Ratio**: recorded as `completion_to_prompt_ratio`.
- **Loop Count**: captured in `AGENT_STEP` and `AGENT_END` events.
- **Failure Codes**: `PARSER_ERROR`, `UNKNOWN_TOOL`, `TOOL_ERROR`, and `max_steps_exceeded`.

Local test run:

```text
5 passed in 0.10s
```

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Hallucinated Tool Name

- **Input**: "I have a cough. What should I do?"
- **Failure**: The LLM emitted `Action: diagnose_patient(symptoms="cough")`.
- **Observation**: The agent returned `Tool error: unknown tool 'diagnose_patient'`.
- **Root Cause**: The model selected a tool name outside the registered tool inventory.
- **Fix**: The system prompt explicitly lists allowed tools, `_execute_tool` validates tool names, and the observation is fed back so the LLM can recover with a valid action.

### Case Study: Parser Error

- **Failure**: LLM output without `Action:` or `Final Answer:`.
- **Observation**: The agent emits a parser observation explaining the required format.
- **Fix**: The ReAct loop continues instead of crashing, giving the model a chance to repair the format.

### Case Study: Successful Trace

- **Input**: "A 62-year-old patient in Hanoi has chest pain and shortness of breath for 2 hours."
- **Trace**:
  - `AGENT_STEP`: `assess_symptom_urgency(...)`
  - `TOOL_CALL`: returned `Urgency: emergency`
  - `AGENT_STEP`: `recommend_care_service(...)`
  - `TOOL_CALL`: returned `Emergency department`
  - `AGENT_FINAL`: final answer with safety disclaimer

---

## 5. Ablation Studies & Experiments

### Experiment 1: Chatbot vs Agent

| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple definition | Direct answer | Direct answer after possible reasoning | Draw |
| Healthcare triage workflow | May provide unsupported advice | Calls triage and care recommendation tools | Agent |
| Unknown tool recovery | Not applicable | Receives observation and retries | Agent |

Scripted benchmark result:

```text
Agent success rate: 3/3
Average loop count: 3 steps
```

### Experiment 2: Prompt v1 vs Prompt v2

- **Prompt v1**: Basic Thought/Action/Observation format.
- **Prompt v2**: Adds strict tool inventory, exact action format, stop condition, and warning against repeated failing actions.
- **Result**: v2 improves parser reliability and makes the agent recover from invalid tool calls.

### Flowchart

```text
Question -> LLM Thought/Action -> Parser -> Tool -> Observation -> Next step -> Final Answer
                 |                  |
                 |                  +-> Parser/tool error observation -> retry
                 |
                 +-> Final Answer -> stop
```

---

## 6. Production Readiness Review

- **Security**: Tool arguments are parsed with `ast`/`json`, not raw `eval`.
- **Guardrails**: `max_steps` prevents infinite loops and unexpected cost growth.
- **Observability**: JSON logs support trace review, aggregate metrics, and failure analysis.
- **Healthcare Safety**: The prototype is educational triage support only and does not provide diagnosis or treatment.
- **Scalability**: The current dictionary-based tools can later be replaced by tool registries, RAG tools, async execution, or LangGraph-style state machines.

---

## 7. Implemented Files

- `src/agent/agent.py`
- `src/agent/chatbot.py`
- `src/tools/healthcare_tools.py`
- `src/tools/__init__.py`
- `tests/test_agent.py`
- `src/core/local_provider.py`
- `src/telemetry/logger.py`
