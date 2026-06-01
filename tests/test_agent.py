import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.agent.agent_v1 import ReActAgentV1
from src.agent.chatbot import BaselineChatbot
from src.core.llm_provider import LLMProvider
from src.tools.healthcare_tools import get_tools


class FakeProvider(LLMProvider):
    def __init__(self, responses):
        super().__init__(model_name="fake-react-model")
        self.responses = list(responses)
        self.calls = 0

    def generate(self, prompt, system_prompt=None):
        response = self.responses[self.calls]
        self.calls += 1
        return {
            "content": response,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "latency_ms": 1,
            "provider": "fake",
        }

    def stream(self, prompt, system_prompt=None):
        yield self.generate(prompt, system_prompt)["content"]


def test_react_agent_executes_tool_and_finishes():
    llm = FakeProvider(
        [
            'Thought: Need to assess red flags.\nAction: assess_symptom_urgency(symptoms="chest pain and shortness of breath", age=62, duration_hours=2)',
            "Thought: Emergency red flags are present.\nFinal Answer: Emergency care is appropriate; call local emergency services or go to the emergency department.",
        ]
    )
    agent = ReActAgent(llm=llm, tools=get_tools(), max_steps=3)

    answer = agent.run("A 62-year-old has chest pain and shortness of breath. What should they do?")

    assert "Emergency care" in answer
    assert llm.calls == 2
    assert any(entry["role"] == "observation" and "Urgency: emergency" in entry["content"] for entry in agent.history)


def test_react_agent_handles_unknown_tool_then_recovers():
    llm = FakeProvider(
        [
            'Thought: I need a made up tool.\nAction: diagnose_patient(symptoms="cough")',
            'Thought: Use the real triage tool instead.\nAction: assess_symptom_urgency(symptoms="cough", age=30, duration_hours=24)',
            "Final Answer: Routine care is reasonable if symptoms persist, but this is not a diagnosis.",
        ]
    )
    agent = ReActAgent(llm=llm, tools=get_tools(), max_steps=4)

    answer = agent.run("I have a cough. What should I do?")

    assert "Routine care" in answer
    assert any("unknown tool" in entry["content"] for entry in agent.history)


def test_react_agent_parses_json_action():
    llm = FakeProvider(
        [
            'Thought: Estimate cost.\nAction: {"tool": "estimate_visit_cost", "args": {"service_type": "urgent", "insurance_status": "insured"}}',
            "Final Answer: The estimated insured urgent care cost is 180,000 VND.",
        ]
    )
    agent = ReActAgent(llm=llm, tools=get_tools(), max_steps=3)

    answer = agent.run("Estimate urgent care cost with insurance.")

    assert "180,000 VND" in answer
    assert any("Estimated patient cost" in entry["content"] for entry in agent.history)


def test_baseline_chatbot_returns_direct_answer():
    llm = FakeProvider(["A chatbot answers directly without external tools."])
    chatbot = BaselineChatbot(llm=llm)

    answer = chatbot.run("What is a chatbot?")

    assert answer == "A chatbot answers directly without external tools."


def test_react_agent_v1_stops_on_unknown_tool():
    llm = FakeProvider(['Thought: Try a fake tool.\nAction: diagnose_patient(symptoms="cough")'])
    agent = ReActAgentV1(llm=llm, tools=get_tools(), max_steps=3)

    answer = agent.run("I have a cough. What should I do?")

    assert "unknown tool" in answer
