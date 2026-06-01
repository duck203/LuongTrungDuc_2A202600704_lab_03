# Evaluation Metrics for Lab 3: Healthcare Agentic Reasoning

In this lab, we do not just ask "Does it work?". We ask **"How well does it perform, and can we explain why?"**

The project uses a healthcare triage support scenario. It is an educational prototype only and must not be treated as diagnosis or medical advice.

---

## Key Industry Metrics

### 1. Token Efficiency

- **Prompt vs. Completion**: Is the healthcare safety prompt too verbose, or is it just enough to prevent unsafe answers?
- **Completion-to-Prompt Ratio**: Captured as `completion_to_prompt_ratio` in `LLM_METRIC`.
- **Cost Analysis**: Lower token count means lower cost, but unsafe under-prompting is not acceptable in healthcare-like workflows.

### 2. Latency

- **Per-Step Latency**: Captured as `latency_ms` for every LLM call.
- **Total Duration**: For a ReAct agent, total time includes all reasoning loops and tool execution.
- **Goal**: For a production support tool, simple triage guidance should usually finish within a few seconds.

### 3. Loop Count

- **Multi-step Reasoning**: How many `Thought -> Action -> Observation` cycles did the agent need?
- **Termination Quality**: Did it stop with `Final Answer`, or did it hit `max_steps`?
- **Healthcare Expectation**: Emergency red-flag prompts should terminate quickly with an escalation recommendation.

### 4. Failure Analysis

- **Parser Error**: The LLM did not produce a valid `Action:` or `Final Answer:`.
- **Hallucinated Tool**: The LLM called a tool that does not exist, such as `diagnose_patient(...)`.
- **Timeout**: The agent exceeded `max_steps`.
- **Safety Failure**: The answer presents a diagnosis or treatment as certain medical advice.

---

## Evaluation Commands

Run unit tests:

```bash
pytest -q
```

Run scripted comparison between chatbot and agent:

```bash
python evaluate_lab.py
```

Outputs:

```text
report/evaluation_results.md
report/evaluation_results.json
```

Run aggregate log analysis:

```bash
python analyze_logs.py
```

Output:

```text
report/log_analysis.md
```

---

## Expected Benchmark Cases

| Case | Expected Agent Behavior | Useful Metric |
| :--- | :--- | :--- |
| Emergency red flags | Calls `assess_symptom_urgency`, then recommends emergency service | Low loop count, correct escalation |
| Routine symptoms | Calls triage, then gives monitoring/preparation guidance | Safety disclaimer, no over-escalation |
| Tool recovery | Recovers from hallucinated `diagnose_patient(...)` | `UNKNOWN_TOOL` trace followed by success |

---

## How to Use the Logs

All telemetry is written to `logs/YYYY-MM-DD.log` as JSON lines. Important events:

- `CHATBOT_START`
- `CHATBOT_END`
- `AGENT_START`
- `AGENT_STEP`
- `TOOL_CALL`
- `UNKNOWN_TOOL`
- `PARSER_ERROR`
- `TOOL_ERROR`
- `LLM_METRIC`
- `AGENT_FINAL`
- `AGENT_END`

Use `python analyze_logs.py` to calculate:

- Total LLM requests
- Total estimated cost
- Average latency
- Average completion-to-prompt ratio
- Tool-call success count
- Parser error count
- Unknown-tool count
- Max-step timeout count
- Aggregate reliability estimate

The group report should include both a successful trace and at least one failed trace, because the rubric rewards error analysis as much as the final working run.
