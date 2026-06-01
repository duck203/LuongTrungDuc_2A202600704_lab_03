# Individual Report: Lab 3 Chatbot vs ReAct Agent

## 1. Technical Contribution

My main contribution was implementing and validating the ReAct agent workflow for the healthcare triage scenario.

Specific work:

- Built the baseline chatbot flow in `src/agent/chatbot.py`.
- Implemented the first ReAct loop in `src/agent/agent_v1.py`.
- Implemented the improved ReAct loop in `src/agent/agent.py`.
- Added healthcare tools in `src/tools/healthcare_tools.py`.
- Added action parsing for function-call style actions such as `tool_name(arg="value")`.
- Added JSON action parsing for structured tool calls.
- Added failure handling for parser errors, unknown tools, tool exceptions, and max-step stopping.
- Added telemetry through `src/telemetry/logger.py` and `src/telemetry/metrics.py`.
- Created scripted evaluation cases in `evaluate_lab.py`.
- Compared chatbot, Agent v1, and Agent v2 outputs on emergency, routine, and failure-recovery cases.

## 2. Debugging Case Study

Bug:

The agent sometimes called a tool that did not exist, for example:

```text
Action: diagnose_patient(symptoms="urgent care cost")
```

Cause:

The LLM generated a plausible tool name instead of selecting from the available tool list. A simple implementation could crash or stop at this point.

How I detected it:

I used a scripted evaluation case in `evaluate_lab.py` where the first agent response intentionally calls `diagnose_patient`. The telemetry log records an `UNKNOWN_TOOL` event.

Fix:

I changed the agent behavior so unknown tools return a structured observation:

```text
Tool error: unknown tool 'diagnose_patient'. Available tools: assess_symptom_urgency, recommend_care_service, estimate_visit_cost, appointment_preparation.
```

Result:

The agent can recover in the next step by selecting the correct tool:

```text
Action: estimate_visit_cost(service_type="urgent", insurance_status="insured")
```

This turns a failed run into a successful final answer.

## 3. Personal Insights

The baseline chatbot is useful because it is simple, fast, and easy to test. However, it answers directly from the model and can be unsafe when the task requires checking facts or applying rules.

The ReAct agent is stronger because it separates reasoning from action. It can inspect symptoms with a tool, observe the result, and then produce a more grounded answer. This makes it better for tasks such as healthcare triage, cost estimation, and workflow support.

The tradeoff is complexity. A ReAct agent can fail at parsing, choose the wrong tool, repeat actions, or spend more tokens. Because of that, the agent needs max-step limits, clear tool descriptions, structured observations, and telemetry.

The most important lesson is that agent quality is not only about the model. It depends heavily on tool design, prompt constraints, error recovery, and evaluation.

## 4. Future Improvements

- Add more test cases for emergency, urgent, and routine symptoms.
- Add final-answer validation to check for healthcare safety disclaimers.
- Add RAG over trusted clinical guidance documents.
- Add memory so the agent can use previous conversation context safely.
- Add a dashboard to visualize logs, tool calls, token usage, and failure rates.
- Run ablation experiments comparing chatbot only, agent without recovery, and improved agent with recovery.
