# Lab 3: Chatbot vs ReAct Agent (Industry Edition)

Welcome to Phase 3 of the Agentic AI course! This lab focuses on moving from a simple LLM Chatbot to a sophisticated **ReAct Agent** with industry-standard monitoring.

## 🚀 Getting Started

### 1. Setup Environment
Copy the `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Directory Structure
- `src/tools/`: Extension point for your custom tools.
- `src/agent/agent.py`: Completed ReAct agent loop with Thought/Action/Observation execution.
- `src/agent/chatbot.py`: Baseline no-tool chatbot for comparison.
- `src/tools/healthcare_tools.py`: Healthcare triage support tools for multi-step reasoning tasks.
- `tests/test_agent.py`: Unit tests that validate the agent without requiring external API keys.

### 4. Run Tests
```bash
pytest -q
```

Expected local result:
```text
5 passed
```

### 5. Run Scripted Evaluation
```bash
python evaluate_lab.py
```

This writes:
- `report/evaluation_results.md`
- `report/evaluation_results.json`

### 6. Analyze Logs
```bash
python analyze_logs.py
```

This writes:
- `report/log_analysis.md`
- `report/log_analysis.json`

### 7. Example Tool Task
Ask the agent:
```text
A 62-year-old patient in Hanoi has chest pain and shortness of breath for 2 hours. What level of care is appropriate?
```
The ReAct agent should call healthcare triage tools, recommend an appropriate care level, and include a safety disclaimer. This project is for educational triage workflow simulation only and does not provide medical diagnosis.

## 🏠 Running with Local Models (CPU)

If you don't want to use OpenAI or Gemini, you can run open-source models (like Phi-3) directly on your CPU using `llama-cpp-python`.

### 1. Download the Model
Download the **Phi-3-mini-4k-instruct-q4.gguf** (approx 2.2GB) from Hugging Face:
- [Phi-3-mini-4k-instruct-GGUF](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)
- Direct Download: [phi-3-mini-4k-instruct-q4.gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf)

### 2. Place Model in Project
Create a `models/` folder in the root and move the downloaded `.gguf` file there.

### 3. Update `.env`
Change your `DEFAULT_PROVIDER` and set the path:
```env
DEFAULT_PROVIDER=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

## 🎯 Lab Objectives

1.  **Baseline Chatbot**: Observe the limitations of a standard LLM when faced with multi-step reasoning.
2.  **ReAct Loop**: Implement the `Thought-Action-Observation` cycle in `src/agent/agent.py`.
3.  **Provider Switching**: Swap between OpenAI and Gemini seamlessly using the `LLMProvider` interface.
4.  **Failure Analysis**: Use the structured logs in `logs/` to identify why the agent fails (hallucinations, parsing errors).
5.  **Grading & Bonus**: Follow the [SCORING.md](file:///Users/tindt/personal/ai-thuc-chien/day03-lab-agent/SCORING.md) to maximize your points and explore bonus metrics.

## 🏥 Healthcare Scenario

This submission uses a healthcare triage assistant scenario. The tools can:
- Assess whether symptoms contain emergency red flags.
- Recommend emergency, urgent, or routine care services.
- Estimate planning-level visit cost in VND.
- List documents and information to prepare for a visit.

Safety note: the system is not a medical device and does not diagnose. It is a lab prototype for studying ReAct agents, tool calls, telemetry, and failure handling.

## ✅ Rubric Coverage

- **Chatbot Baseline**: `src/agent/chatbot.py`
- **Agent v1/v2**: documented in `report/Lab3__Healthcare_ReAct_Agent.md`
- **2+ Tools**: `src/tools/healthcare_tools.py`
- **Trace Quality**: JSON logs plus successful/failed trace sections in reports
- **Evaluation & Analysis**: `evaluate_lab.py` and `report/evaluation_results.md`
- **Flowchart & Insight**: report flowchart section
- **Extra Monitoring**: latency, token count, cost estimate, token ratio
- **Failure Handling**: parser errors, unknown tools, max-step guardrail

## 🛠️ How to Use This Baseline
The code is designed as a **Production Prototype**. It includes:
- **Telemetry**: Every action is logged in JSON format for later analysis.
- **Robust Provider Pattern**: Easily extendable to any LLM API.
- **Clean Skeletons**: Focus on the logic that matters—the agent's reasoning process.

---

*Happy Coding! Let's build agents that actually work.*
