# Lab 3: Healthcare ReAct Agent Summary

This project implements a comparison between a direct chatbot baseline and a ReAct agent.

## Implemented Components

| Requirement | Implementation |
| :--- | :--- |
| Chatbot baseline | `src/agent/chatbot.py` |
| Agent v1 | `src/agent/agent_v1.py` |
| Agent v2 | `src/agent/agent.py` |
| 2+ tools | `src/tools/healthcare_tools.py` |
| Successful trace | `report/group_report/TEMPLATE_GROUP_REPORT.md` |
| Failed trace | `report/group_report/TEMPLATE_GROUP_REPORT.md` |
| Evaluation | `evaluate_lab.py` |
| Monitoring | `src/telemetry/`, `analyze_logs.py` |
| Individual report | `report/individual_reports/individual_report.md` |

## Demo Commands

Run offline demo:

```powershell
python run_agent.py --demo
```

Run scripted evaluation:

```powershell
python evaluate_lab.py
```

Analyze logs:

```powershell
python analyze_logs.py
```

Run tests:

```powershell
python -m pytest -q
```

## Expected Submission Files

- `report/group_report/TEMPLATE_GROUP_REPORT.md`
- `report/individual_reports/individual_report.md`
- `report/evaluation_results.md`
- `report/evaluation_results.json`
- `report/log_analysis.md`
- `report/log_analysis.json`
