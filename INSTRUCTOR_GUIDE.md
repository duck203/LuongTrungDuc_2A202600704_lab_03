# Instructor Guide: Lab 3 - From Chatbot to Healthcare ReAct Agent

This guide supports a 240-minute lab session. The goal is to move students from "writing code that runs" to engineering an observable agent that can reason, call tools, recover from failures, and explain its behavior through traces.

Safety note: this lab uses a healthcare triage support scenario for educational purposes only. The agent must not diagnose, prescribe treatment, or replace a clinician.

---

## 🎯 Core Learning Objectives

1. **ReAct Mechanics**: Understand the cycle of `Thought -> Action -> Observation -> Final Answer`.
2. **Industry Observability**: Debug an LLM-driven workflow using structured JSON logs.
3. **Iterative Refinement**: Improve agent v1 into agent v2 by diagnosing failure traces.
4. **Healthcare Guardrails**: Separate educational triage support from medical diagnosis.

---

## ⏱️ Timeline & Flow

### 01. The Hook: Why Agents? (15m)

- **Demo**: Show a simple chatbot failing a healthcare triage workflow, for example: "A 62-year-old patient has chest pain and shortness of breath. What level of care is appropriate?"
- **Key Insight**: Chatbots are good at talking; agents are better at acting through auditable tools.
- **Safety Discussion**: In healthcare-like domains, every recommendation should be tied to explicit rules or trusted data.

### 02. Phase 1: Tool Design (30m)

- **Activity**: Students inspect or extend `src/tools/healthcare_tools.py`.
- **Teaching Point**: Tool descriptions are part of the agent interface. A vague tool causes vague or unsafe actions.
- **Example**:
  - Vague: "Checks symptoms."
  - Better: "Educational triage helper that classifies symptoms as emergency, urgent, or routine. It does not diagnose."

### 03. Phase 2: Chatbot Baseline (30m)

- **Activity**: Run `BaselineChatbot` against healthcare prompts.
- **Observe**: The chatbot may answer fluently but without verifiable tool evidence.
- **Discussion**: Why can fluent unsupported advice be risky in healthcare workflows?

### 04. Phase 3: Building Agent v1 (60m)

- **Activity**: Study `src/agent/agent.py` and run the ReAct loop.
- **Instructor's Role**: Emphasize parsing, tool-name validation, observations, and termination.
- **Key Point**: The `Observation` must be fed back into the prompt so the model can continue reasoning from tool output.

### 05. Phase 4: Failure Analysis (45m)

- **Activity**: Open `logs/YYYY-MM-DD.log` and inspect events such as `AGENT_STEP`, `TOOL_CALL`, `UNKNOWN_TOOL`, `PARSER_ERROR`, and `LLM_METRIC`.
- **Teaching Case**: The agent hallucinates `diagnose_patient(...)`, which does not exist.
- **Fix**: Agent v2 validates tool names and returns an observation listing available tools instead of crashing or inventing an answer.

### 06. Phase 5: Group Evaluation (30m)

- **Activity**:
  - Run `pytest -q`.
  - Run `python evaluate_lab.py`.
  - Run `python analyze_logs.py`.
- **Discussion**:
  - Why did the ReAct agent beat the chatbot in emergency red-flag and cost-estimation cases?
  - Why might a chatbot still be better for very simple questions?

---

## 💡 Teaching Tips & Examples

### 🏥 Recommended Scenario: "Healthcare Triage Support Assistant"

- **Tool 1**: `assess_symptom_urgency(symptoms, age, duration_hours)` -> Returns emergency, urgent, or routine care level.
- **Tool 2**: `recommend_care_service(urgency, location)` -> Recommends emergency department, urgent care, or primary care.
- **Tool 3**: `estimate_visit_cost(service_type, insurance_status)` -> Returns a planning-level cost estimate in VND.
- **Tool 4**: `appointment_preparation(service_type)` -> Lists documents and information to prepare.

### Example Test Case

```text
A 62-year-old patient in Hanoi has chest pain and shortness of breath for 2 hours. What level of care is appropriate?
```

Expected agent behavior:

```text
Thought -> assess_symptom_urgency(...)
Observation -> Urgency: emergency
Thought -> recommend_care_service(...)
Observation -> Emergency department
Final Answer -> Emergency care recommendation with "not a diagnosis" disclaimer
```

### ⚠️ Common Pitfalls to Watch For

1. **Unsafe Medical Framing**: The agent says "you have disease X".
   - *Fix*: Add safety prompt rules and tool outputs that say "not a diagnosis."
2. **Infinite Loops**: The agent repeats the same thought/action forever.
   - *Fix*: Check `max_steps` and final-answer detection.
3. **Parser Errors**: The LLM outputs markdown fences or malformed actions.
   - *Fix*: Use robust extraction and parser error observations.
4. **Hallucinated Tools**: The LLM calls `diagnose_patient(...)`.
   - *Fix*: Validate against registered tool names and return an `UNKNOWN_TOOL` observation.
5. **Empty Observations**: A tool returns too little information.
   - *Fix*: Improve the tool output and description so the next step is obvious.

---

## 📈 Success Metrics for the Instructor

The lab is successful if students can show:

- A successful trace with `AGENT_STEP -> TOOL_CALL -> AGENT_FINAL`.
- A failed trace such as `UNKNOWN_TOOL` or `PARSER_ERROR` and explain how v2 handles it.
- Provider switching with Gemini or demo mode.
- Evaluation results from `report/evaluation_results.md`.
- Aggregate metrics from `python analyze_logs.py`.
- A combined report file named like `Lab3__Healthcare_ReAct_Agent.md` containing both group and personal sections.

---

*"In the world of AI, the trace is the truth. Teach them to read the logs."*
