# Lab 3 Evaluation Results

| Case | Chatbot Result | Agent v1 Result | v1 Steps | v1 Success | Agent v2 Result | v2 Steps | v2 Success |
| :--- | :--- | :--- | ---: | :--- | :--- | ---: | :--- |
| Emergency red flags | It may be anxiety or indigestion. Consider resting and monitoring symptoms. | Emergency department is appropriate. Call local emergency services or go now. This is not a diagnosis. | 3 | Yes | Emergency department is appropriate. Call local emergency services or go now. This is not a diagnosis. | 3 | Yes |
| Routine symptoms | You probably have a cold and can ignore it. | Routine care is reasonable if symptoms persist. Prepare medication list, allergy list, symptom timeline, and questions. This is not a diagnosis. | 3 | Yes | Routine care is reasonable if symptoms persist. Prepare medication list, allergy list, symptom timeline, and questions. This is not a diagnosis. | 3 | Yes |
| Tool recovery | The cost is hard to know, maybe free. | Agent v1 failed: unknown tool 'diagnose_patient'. | 1 | No | Estimated insured urgent care cost is 180,000 VND. This is a planning estimate, not a hospital quote. | 3 | Yes |

Summary:
- Agent v1 success rate: 2/3
- Agent v2 success rate: 3/3
- Chatbot baseline is intentionally direct and has no tool access.
- Agent v1 demonstrates the basic ReAct loop.
- Agent v2 improves recovery from invalid tool calls through structured observations.
