import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List


LOG_DIR = Path("logs")
REPORT_DIR = Path("report")
LEGACY_RETAIL_DEMO_MARKERS = {
    "iphone",
    "winner",
    "calculate_total",
    "get_product_price",
    "check_stock",
    "airpods",
    "macbook",
}


def read_events() -> List[Dict[str, Any]]:
    events = []
    if not LOG_DIR.exists():
        return events

    for path in sorted(LOG_DIR.glob("*.log")):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if _is_legacy_retail_demo_event(event):
                continue
            events.append(event)
    return events


def summarize(events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    events = list(events)
    metrics = [event["data"] for event in events if event.get("event") == "LLM_METRIC"]
    tool_calls = [event for event in events if event.get("event") == "TOOL_CALL"]
    agent_end = [event for event in events if event.get("event") == "AGENT_END"]
    agent_v1_end = [event for event in events if event.get("event") == "AGENT_V1_END"]
    parser_errors = [event for event in events if event.get("event") == "PARSER_ERROR"]
    unknown_tools = [event for event in events if event.get("event") == "UNKNOWN_TOOL"]
    agent_v1_unknown_tools = [
        event for event in events if event.get("event") == "AGENT_V1_UNKNOWN_TOOL"
    ]
    tool_errors = [event for event in events if event.get("event") == "TOOL_ERROR"]
    timeouts = [
        event
        for event in agent_end
        if event.get("data", {}).get("status") == "max_steps_exceeded"
    ]

    successful_runs = [
        event for event in agent_end if event.get("data", {}).get("status") == "success"
    ]
    successful_v1_runs = [
        event for event in agent_v1_end if event.get("data", {}).get("status") == "success"
    ]
    failed_v1_runs = [
        event for event in agent_v1_end if event.get("data", {}).get("status") != "success"
    ]
    total_runs = len(agent_end)
    reliability = (len(successful_runs) / total_runs) if total_runs else 0.0
    total_v1_runs = len(agent_v1_end)
    v1_reliability = (len(successful_v1_runs) / total_v1_runs) if total_v1_runs else 0.0

    return {
        "total_events": len(events),
        "agent_v1_runs": total_v1_runs,
        "successful_agent_v1_runs": len(successful_v1_runs),
        "failed_agent_v1_runs": len(failed_v1_runs),
        "agent_v1_reliability": round(v1_reliability, 4),
        "agent_v2_runs": total_runs,
        "successful_agent_v2_runs": len(successful_runs),
        "agent_v2_reliability": round(reliability, 4),
        "llm_requests": len(metrics),
        "total_tokens": sum(metric.get("total_tokens", 0) for metric in metrics),
        "total_cost_estimate": round(sum(metric.get("cost_estimate", 0.0) for metric in metrics), 6),
        "average_latency_ms": round(mean([m.get("latency_ms", 0) for m in metrics]), 2) if metrics else 0,
        "average_completion_to_prompt_ratio": round(
            mean([m.get("completion_to_prompt_ratio", 0.0) for m in metrics]), 4
        ) if metrics else 0,
        "tool_calls": len(tool_calls),
        "parser_errors": len(parser_errors),
        "unknown_tool_errors": len(unknown_tools),
        "agent_v1_unknown_tool_errors": len(agent_v1_unknown_tools),
        "tool_errors": len(tool_errors),
        "timeouts": len(timeouts),
    }


def write_report(summary: Dict[str, Any]) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    lines = [
        "# Log Analysis",
        "",
        "| Metric | Value |",
        "| :--- | ---: |",
    ]
    for key, value in summary.items():
        lines.append(f"| `{key}` | {value} |")
    lines.append("")
    (REPORT_DIR / "log_analysis.md").write_text("\n".join(lines), encoding="utf-8")
    (REPORT_DIR / "log_analysis.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )


def _is_legacy_retail_demo_event(event: Dict[str, Any]) -> bool:
    serialized = json.dumps(event, ensure_ascii=False).lower()
    return any(marker in serialized for marker in LEGACY_RETAIL_DEMO_MARKERS)


def main():
    summary = summarize(read_events())
    write_report(summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
