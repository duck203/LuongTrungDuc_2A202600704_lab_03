import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socket import socket
from typing import Any, Dict, Tuple

from run_agent import DemoProvider, build_provider, load_dotenv
from src.agent.agent import ReActAgent
from src.agent.agent_v1 import ReActAgentV1
from src.agent.chatbot import BaselineChatbot
from src.tools.healthcare_tools import get_tools


DEFAULT_QUESTION = "Tôi đang bị đầu óc không tỉnh táo"


HTML = r"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Lab 3 Agent Console</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fb;
      --panel: #ffffff;
      --ink: #20242c;
      --muted: #667085;
      --line: #d9dee8;
      --accent: #176b5b;
      --accent-strong: #0f4f43;
      --danger: #b42318;
      --code: #111827;
      --code-bg: #eef2f6;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .shell {
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      min-height: 100vh;
    }

    aside {
      border-right: 1px solid var(--line);
      background: #f1f4f8;
      padding: 22px;
    }

    main {
      padding: 24px;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      gap: 18px;
    }

    h1 {
      margin: 0 0 4px;
      font-size: 22px;
      line-height: 1.2;
      letter-spacing: 0;
    }

    h2 {
      margin: 0 0 10px;
      font-size: 15px;
      letter-spacing: 0;
    }

    .muted {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }

    .field {
      display: grid;
      gap: 7px;
      margin-top: 18px;
    }

    label {
      color: #344054;
      font-weight: 650;
      font-size: 13px;
    }

    select,
    textarea,
    input {
      width: 100%;
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--ink);
      border-radius: 7px;
      padding: 10px 11px;
      font: inherit;
      min-height: 42px;
    }

    textarea {
      min-height: 128px;
      resize: vertical;
      line-height: 1.45;
    }

    button {
      width: 100%;
      border: 0;
      border-radius: 7px;
      background: var(--accent);
      color: white;
      min-height: 44px;
      font-weight: 750;
      cursor: pointer;
      margin-top: 18px;
    }

    button:hover { background: var(--accent-strong); }
    button:disabled { opacity: 0.65; cursor: progress; }

    .quick {
      display: grid;
      gap: 8px;
      margin-top: 18px;
    }

    .quick button {
      margin: 0;
      background: #ffffff;
      color: #1d2939;
      border: 1px solid var(--line);
      text-align: left;
      padding: 9px 10px;
      min-height: 38px;
      font-weight: 600;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
    }

    .status {
      min-width: 180px;
      text-align: right;
      color: var(--muted);
      font-size: 13px;
    }

    .workspace {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      gap: 18px;
      min-height: 0;
    }

    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      min-width: 0;
    }

    .answer {
      min-height: 180px;
      white-space: pre-wrap;
      line-height: 1.55;
      font-size: 16px;
    }

    .trace {
      display: grid;
      gap: 10px;
      max-height: calc(100vh - 180px);
      overflow: auto;
      padding-right: 2px;
    }

    .trace-item {
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 10px;
      background: #fbfcfe;
    }

    .trace-role {
      font-size: 12px;
      color: var(--muted);
      font-weight: 750;
      margin-bottom: 6px;
      text-transform: uppercase;
    }

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--code);
      background: var(--code-bg);
      border-radius: 6px;
      padding: 10px;
      font-size: 12px;
      line-height: 1.45;
    }

    .error {
      color: var(--danger);
      font-weight: 650;
    }

    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }

    .pill {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 9px;
      color: #344054;
      background: #fbfcfe;
      font-size: 12px;
    }

    @media (max-width: 900px) {
      .shell { grid-template-columns: 1fr; }
      aside { border-right: 0; border-bottom: 1px solid var(--line); }
      .workspace { grid-template-columns: 1fr; }
      .topbar { display: block; }
      .status { text-align: left; margin-top: 8px; }
      .trace { max-height: none; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <h1>Lab 3 Agent Console</h1>
      <div class="muted">Chạy chatbot baseline, Agent v1 hoặc Agent v2 qua cùng một giao diện.</div>

      <div class="field">
        <label for="mode">Chế độ</label>
        <select id="mode">
          <option value="agent-v2">Agent v2 improved</option>
          <option value="agent-v1">Agent v1 basic</option>
          <option value="chatbot">Chatbot baseline</option>
        </select>
      </div>

      <div class="field">
        <label for="provider">Provider</label>
        <select id="provider">
          <option value="demo">Demo offline</option>
          <option value="env">Gemini/OpenAI từ .env</option>
        </select>
      </div>

      <div class="field">
        <label for="maxSteps">Max steps</label>
        <input id="maxSteps" type="number" min="1" max="10" value="5" />
      </div>

      <div class="field">
        <label for="question">Câu hỏi</label>
        <textarea id="question"></textarea>
      </div>

      <button id="sendBtn" type="button">Run</button>

      <div class="quick">
        <button type="button" data-question="Tôi đang bị đầu óc không tỉnh táo">Không tỉnh táo</button>
        <button type="button" data-question="Tôi bị đau ngực và khó thở 2 tiếng, tôi nên đi khám ở đâu?">Đau ngực khó thở</button>
        <button type="button" data-question="Tôi bị ho nhẹ 1 ngày, không khó thở">Ho nhẹ</button>
      </div>
    </aside>

    <main>
      <div class="topbar">
        <div>
          <h2>Answer</h2>
          <div class="muted">Kết quả cuối cùng nằm trong khung answer; trace nằm bên phải.</div>
        </div>
        <div id="status" class="status">Ready</div>
      </div>

      <div class="workspace">
        <section>
          <div id="answer" class="answer muted">Nhập câu hỏi rồi bấm Run.</div>
          <div id="meta" class="meta"></div>
        </section>

        <section>
          <h2>Trace</h2>
          <div id="trace" class="trace">
            <div class="muted">Trace sẽ hiển thị Thought, Action và Observation sau khi chạy.</div>
          </div>
        </section>
      </div>
    </main>
  </div>

  <script>
    const questionEl = document.querySelector("#question");
    const modeEl = document.querySelector("#mode");
    const providerEl = document.querySelector("#provider");
    const maxStepsEl = document.querySelector("#maxSteps");
    const sendBtn = document.querySelector("#sendBtn");
    const answerEl = document.querySelector("#answer");
    const traceEl = document.querySelector("#trace");
    const statusEl = document.querySelector("#status");
    const metaEl = document.querySelector("#meta");

    questionEl.value = "Tôi đang bị đầu óc không tỉnh táo";

    document.querySelectorAll("[data-question]").forEach((button) => {
      button.addEventListener("click", () => {
        questionEl.value = button.dataset.question;
        questionEl.focus();
      });
    });

    sendBtn.addEventListener("click", async () => {
      const question = questionEl.value.trim();
      if (!question) {
        answerEl.textContent = "Vui lòng nhập câu hỏi.";
        answerEl.className = "answer error";
        return;
      }

      sendBtn.disabled = true;
      statusEl.textContent = "Running...";
      answerEl.textContent = "";
      answerEl.className = "answer muted";
      traceEl.innerHTML = "<div class='muted'>Đang chạy agent...</div>";
      metaEl.innerHTML = "";

      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question,
            mode: modeEl.value,
            provider: providerEl.value,
            max_steps: Number(maxStepsEl.value || 5),
          }),
        });
        const data = await response.json();
        renderResult(data);
      } catch (error) {
        renderResult({ ok: false, error: String(error), trace: [] });
      } finally {
        sendBtn.disabled = false;
      }
    });

    function renderResult(data) {
      statusEl.textContent = data.ok ? "Completed" : "Error";
      answerEl.className = data.ok ? "answer" : "answer error";
      answerEl.textContent = data.ok ? data.answer : data.error;

      metaEl.innerHTML = "";
      [
        ["mode", data.mode],
        ["provider", data.provider],
        ["model", data.model],
        ["steps", data.steps],
      ].forEach(([key, value]) => {
        if (value === undefined || value === null || value === "") return;
        const pill = document.createElement("span");
        pill.className = "pill";
        pill.textContent = `${key}: ${value}`;
        metaEl.appendChild(pill);
      });

      const trace = Array.isArray(data.trace) ? data.trace : [];
      if (!trace.length) {
        traceEl.innerHTML = "<div class='muted'>Không có trace cho lượt này.</div>";
        return;
      }

      traceEl.innerHTML = "";
      trace.forEach((item, index) => {
        const box = document.createElement("div");
        box.className = "trace-item";

        const role = document.createElement("div");
        role.className = "trace-role";
        role.textContent = `${index + 1}. ${item.role || "step"}`;

        const pre = document.createElement("pre");
        pre.textContent = item.content || "";

        box.appendChild(role);
        box.appendChild(pre);
        traceEl.appendChild(box);
      });
    }
  </script>
</body>
</html>
"""


class LabWebHandler(BaseHTTPRequestHandler):
    server_version = "LabAgentWeb/1.0"

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self._send_html(HTML)
            return
        self.send_error(404, "Not found")

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self.send_error(404, "Not found")
            return

        try:
            payload = self._read_json()
            result = run_chat(payload)
            self._send_json(result)
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc), "trace": []}, status=500)

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def _send_html(self, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def run_chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    load_dotenv(override=True)

    question = str(payload.get("question") or DEFAULT_QUESTION).strip()
    mode = str(payload.get("mode") or "agent-v2").strip()
    provider_choice = str(payload.get("provider") or "demo").strip()
    max_steps = int(payload.get("max_steps") or 5)

    llm = DemoProvider() if provider_choice == "demo" else build_provider()

    if mode == "chatbot":
        app = BaselineChatbot(llm)
        label = "chatbot"
    elif mode == "agent-v1":
        app = ReActAgentV1(llm, get_tools(), max_steps=max_steps)
        label = "react-agent-v1"
    else:
        app = ReActAgent(llm, get_tools(), max_steps=max_steps)
        label = "react-agent-v2"

    try:
        answer = app.run(question)
        ok = True
        error = ""
    except RuntimeError as exc:
        answer = ""
        ok = False
        error = str(exc)

    trace = getattr(app, "history", [])
    return {
        "ok": ok,
        "answer": answer,
        "error": error,
        "trace": trace,
        "mode": label,
        "provider": "demo" if provider_choice == "demo" else os.getenv("DEFAULT_PROVIDER", "env"),
        "model": getattr(llm, "model_name", "unknown"),
        "steps": getattr(llm, "calls", None),
    }


def find_port(preferred_port: int) -> int:
    with socket() as probe:
        try:
            probe.bind(("127.0.0.1", preferred_port))
            return preferred_port
        except OSError:
            pass

    with socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Lab 3 web interface.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    port = find_port(args.port)
    server = ThreadingHTTPServer((args.host, port), LabWebHandler)
    print(f"Lab Agent web UI: http://{args.host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
