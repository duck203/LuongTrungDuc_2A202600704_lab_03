# Individual Report: Lab 3 - Healthcare ReAct Agent

- **Student Name**: Lương Trung Đức
- **Student ID**: 2A202600704
- **GitHub Username**: duck203
- **Commit Evidence**: Add this member's commit hash or GitHub commit URL
- **Date**: 2026-06-01

---

## I. Technical Contribution

Describe exact modules, tests, tools, reports, or debugging work contributed by this member.

Suggested evidence:

- `src/agent/agent.py`
- `src/tools/healthcare_tools.py`
- `run_agent.py`
- `evaluate_lab.py`
- `analyze_logs.py`
- `tests/test_agent.py`

---

## II. Debugging Case Study

Use one real trace from `logs/YYYY-MM-DD.log`.

Example:

- **Problem Description**: The model called an unavailable medical tool, `diagnose_patient(...)`.
- **Log Source**: `UNKNOWN_TOOL`
- **Diagnosis**: The model hallucinated a tool outside the registered tool inventory.
- **Solution**: Agent v2 returned an observation and recovered with a valid healthcare tool.

---

## III. Personal Insights: Chatbot vs ReAct

Discuss:

1. Why a direct chatbot can be fluent but hard to audit.
2. Why ReAct is better for healthcare-like workflows where each recommendation should be tied to tool output.
3. When the agent is worse than a chatbot, such as simple questions where tool overhead is unnecessary.

---

## IV. Future Improvements

Possible directions:

- RAG over clinician-reviewed guidelines.
- Local hospital/service directory retrieval.
- Stronger safety classifier for emergency red flags.
- Human-in-the-loop review for high-risk answers.
- Async tools and better caching for lower latency.
