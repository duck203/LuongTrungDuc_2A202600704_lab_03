import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socket import socket
from typing import Any, Dict

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
  <title>Vinmec Agent Chat</title>
  <style>
    :root {
      --app-bg: #f4f6f8;
      --sidebar: #f8fafc;
      --panel: #ffffff;
      --text: #1f2937;
      --muted: #667085;
      --line: #d0d7e2;
      --user: #1f6f5b;
      --assistant: #ffffff;
      --chip: #eef3f1;
      --danger: #b42318;
      --shadow: 0 10px 32px rgba(15, 23, 42, 0.08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      height: 100vh;
      overflow: hidden;
      background: var(--app-bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .app {
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr) 340px;
      height: 100vh;
      min-height: 0;
    }

    .sidebar {
      background: var(--sidebar);
      border-right: 1px solid var(--line);
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      min-width: 0;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 4px 2px 10px;
    }

    .mark {
      width: 34px;
      height: 34px;
      border-radius: 8px;
      background: var(--user);
      color: white;
      display: grid;
      place-items: center;
      font-weight: 800;
    }

    h1 {
      margin: 0;
      font-size: 16px;
      line-height: 1.25;
      letter-spacing: 0;
    }

    .sub {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.4;
      margin-top: 2px;
    }

    .control {
      display: grid;
      gap: 6px;
    }

    .new-chat {
      width: 100%;
      height: 40px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: white;
      color: #344054;
      cursor: pointer;
      font: inherit;
      font-weight: 700;
      text-align: left;
      padding: 0 10px;
    }

    .new-chat:hover { background: #f1f5f9; }

    label {
      color: #344054;
      font-size: 12px;
      font-weight: 700;
    }

    select,
    input {
      width: 100%;
      height: 40px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0 10px;
      background: white;
      color: var(--text);
      font: inherit;
    }

    .examples {
      display: grid;
      gap: 8px;
      margin-top: 4px;
    }

    .example {
      border: 1px solid var(--line);
      background: white;
      color: #344054;
      border-radius: 8px;
      padding: 10px;
      text-align: left;
      cursor: pointer;
      font: inherit;
      font-size: 13px;
      line-height: 1.35;
    }

    .example:hover { background: #f1f5f9; }

    .sidebar-note {
      margin-top: auto;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
      border-top: 1px solid var(--line);
      padding-top: 14px;
    }

    .chat {
      display: grid;
      grid-template-rows: 58px minmax(0, 1fr) auto;
      min-width: 0;
      min-height: 0;
      background: #ffffff;
    }

    .chat-header {
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 22px;
      gap: 14px;
    }

    .chat-title {
      font-weight: 750;
      font-size: 15px;
    }

    .status {
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }

    .messages {
      overflow-y: auto;
      padding: 28px 22px;
      scroll-behavior: smooth;
      min-height: 0;
      overscroll-behavior: contain;
    }

    .message {
      max-width: 820px;
      margin: 0 auto 20px;
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr);
      gap: 12px;
      align-items: start;
    }

    .avatar {
      width: 34px;
      height: 34px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      font-weight: 800;
      font-size: 13px;
      background: #e8eef5;
      color: #344054;
    }

    .message.user .avatar {
      background: var(--user);
      color: white;
    }

    .bubble {
      background: var(--assistant);
      border: 1px solid transparent;
      border-radius: 10px;
      padding: 7px 0;
      white-space: pre-wrap;
      line-height: 1.58;
      font-size: 15px;
    }

    .message.user .bubble {
      justify-self: start;
      background: var(--chip);
      border-color: #dbe7e2;
      padding: 10px 12px;
      max-width: 680px;
    }

    .message.error .bubble {
      color: var(--danger);
      font-weight: 650;
    }

    .composer-wrap {
      border-top: 1px solid var(--line);
      padding: 14px 22px 18px;
      background: linear-gradient(180deg, rgba(255,255,255,0.78), white 24%);
    }

    .composer {
      max-width: 820px;
      margin: 0 auto;
      background: white;
      border: 1px solid var(--line);
      border-radius: 14px;
      box-shadow: var(--shadow);
      padding: 10px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 44px;
      gap: 8px;
      align-items: end;
    }

    textarea {
      border: 0;
      outline: 0;
      resize: none;
      min-height: 44px;
      max-height: 160px;
      padding: 11px 8px;
      color: var(--text);
      font: inherit;
      line-height: 1.45;
    }

    .send {
      width: 44px;
      height: 44px;
      border: 0;
      border-radius: 10px;
      background: var(--user);
      color: white;
      cursor: pointer;
      font-size: 20px;
      line-height: 1;
    }

    .send:disabled {
      opacity: 0.6;
      cursor: progress;
    }

    .hint {
      max-width: 820px;
      margin: 9px auto 0;
      color: var(--muted);
      font-size: 12px;
      text-align: center;
    }

    .trace-panel {
      background: #fbfcfe;
      border-left: 1px solid var(--line);
      display: grid;
      grid-template-rows: 58px auto minmax(0, 1fr);
      min-width: 0;
      min-height: 0;
    }

    .trace-head {
      border-bottom: 1px solid var(--line);
      padding: 0 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .trace-title {
      font-size: 14px;
      font-weight: 750;
    }

    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 12px 16px 0;
    }

    .pill {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 8px;
      background: white;
      color: #344054;
      font-size: 11px;
    }

    .trace {
      overflow: auto;
      padding: 12px 16px 16px;
      display: grid;
      align-content: start;
      gap: 10px;
      min-height: 0;
      overscroll-behavior: contain;
    }

    .trace-card {
      border: 1px solid var(--line);
      background: white;
      border-radius: 8px;
      padding: 10px;
    }

    .trace-role {
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      margin-bottom: 7px;
    }

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font: 12px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      color: #111827;
    }

    @media (max-width: 1050px) {
      .app { grid-template-columns: 250px minmax(0, 1fr); }
      .trace-panel { display: none; }
    }

    @media (max-width: 760px) {
      body { overflow: auto; }
      .app { display: block; height: auto; min-height: 100vh; }
      .sidebar { border-right: 0; border-bottom: 1px solid var(--line); }
      .chat { min-height: 72vh; }
      .messages { padding: 20px 14px; max-height: 58vh; }
      .composer-wrap { padding: 12px 14px 16px; }
      .message { grid-template-columns: 30px minmax(0, 1fr); }
      .avatar { width: 30px; height: 30px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <div class="mark">V</div>
        <div>
          <h1>Vinmec Agent Chat</h1>
          <div class="sub">Lab 3 Chatbot vs ReAct Agent</div>
        </div>
      </div>

      <button id="newChatBtn" class="new-chat" type="button">+ New chat</button>

      <div class="control">
        <label for="mode">Chế độ</label>
        <select id="mode">
          <option value="agent-v2">Agent v2 improved</option>
          <option value="agent-v1">Agent v1 basic</option>
          <option value="chatbot">Chatbot baseline</option>
        </select>
      </div>

      <div class="control">
        <label for="provider">Provider</label>
        <select id="provider">
          <option value="demo">Demo offline</option>
          <option value="env">Gemini/OpenAI từ .env</option>
        </select>
      </div>

      <div class="control">
        <label for="maxSteps">Max steps</label>
        <input id="maxSteps" type="number" min="1" max="10" value="5" />
      </div>

      <div class="examples">
        <button class="example" type="button" data-question="Tôi đang bị đầu óc không tỉnh táo">Tôi đang bị đầu óc không tỉnh táo</button>
        <button class="example" type="button" data-question="Tôi bị đau ngực và khó thở 2 tiếng, tôi nên đi khám ở đâu?">Tôi bị đau ngực và khó thở 2 tiếng</button>
        <button class="example" type="button" data-question="Tôi bị ho nhẹ 1 ngày, không khó thở">Tôi bị ho nhẹ 1 ngày, không khó thở</button>
      </div>

      <div class="sidebar-note">
        Dữ liệu Vinmec trong bài là dữ liệu mô phỏng học thuật, không phải hệ thống đặt lịch chính thức.
      </div>
    </aside>

    <main class="chat">
      <div class="chat-header">
        <div>
          <div class="chat-title">Cuộc trò chuyện</div>
          <div class="sub">Chọn mode ở sidebar rồi nhập câu hỏi.</div>
        </div>
        <div id="status" class="status">Ready</div>
      </div>

      <div id="messages" class="messages"></div>

      <div class="composer-wrap">
        <div class="composer">
          <textarea id="question" rows="1" placeholder="Nhập câu hỏi cho agent..."></textarea>
          <button id="sendBtn" class="send" type="button" aria-label="Send">↑</button>
        </div>
        <div class="hint">Enter để gửi, Shift + Enter để xuống dòng.</div>
      </div>
    </main>

    <aside class="trace-panel">
      <div class="trace-head">
        <div class="trace-title">Trace</div>
        <div id="traceStatus" class="sub">No run</div>
      </div>
      <div id="meta" class="meta"></div>
      <div id="trace" class="trace">
        <div class="sub">Thought, Action và Observation sẽ xuất hiện ở đây.</div>
      </div>
    </aside>
  </div>

  <script>
    const messagesEl = document.querySelector("#messages");
    const questionEl = document.querySelector("#question");
    const modeEl = document.querySelector("#mode");
    const providerEl = document.querySelector("#provider");
    const maxStepsEl = document.querySelector("#maxSteps");
    const sendBtn = document.querySelector("#sendBtn");
    const newChatBtn = document.querySelector("#newChatBtn");
    const statusEl = document.querySelector("#status");
    const traceStatusEl = document.querySelector("#traceStatus");
    const traceEl = document.querySelector("#trace");
    const metaEl = document.querySelector("#meta");
    const conversation = [];

    resetChat();
    questionEl.value = "Tôi đang bị đầu óc không tỉnh táo";

    document.querySelectorAll("[data-question]").forEach((button) => {
      button.addEventListener("click", () => {
        questionEl.value = button.dataset.question;
        questionEl.focus();
      });
    });

    questionEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        send();
      }
    });

    questionEl.addEventListener("input", () => {
      questionEl.style.height = "auto";
      questionEl.style.height = Math.min(questionEl.scrollHeight, 160) + "px";
    });

    sendBtn.addEventListener("click", send);
    newChatBtn.addEventListener("click", resetChat);

    async function send() {
      const question = questionEl.value.trim();
      if (!question || sendBtn.disabled) return;

      addMessage("user", question);
      conversation.push({ role: "user", content: question });
      questionEl.value = "";
      questionEl.style.height = "auto";
      sendBtn.disabled = true;
      statusEl.textContent = "Running...";
      traceStatusEl.textContent = "Running";
      traceEl.innerHTML = "<div class='sub'>Đang chạy agent...</div>";
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
            history: conversation.slice(-10),
          }),
        });
        const data = await response.json();
        renderResult(data);
      } catch (error) {
        renderResult({ ok: false, error: String(error), trace: [] });
      } finally {
        sendBtn.disabled = false;
        questionEl.focus();
      }
    }

    function renderResult(data) {
      statusEl.textContent = data.ok ? "Completed" : "Error";
      traceStatusEl.textContent = data.ok ? "Completed" : "Error";
      const reply = data.ok ? data.answer : data.error;
      addMessage(data.ok ? "assistant" : "assistant error", reply);
      conversation.push({ role: "assistant", content: reply });
      renderMeta(data);
      renderTrace(data.trace);
    }

    function addMessage(role, content) {
      const message = document.createElement("div");
      message.className = `message ${role}`;

      const avatar = document.createElement("div");
      avatar.className = "avatar";
      avatar.textContent = role.startsWith("user") ? "U" : "A";

      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = content;

      message.appendChild(avatar);
      message.appendChild(bubble);
      messagesEl.appendChild(message);
      requestAnimationFrame(() => {
        messagesEl.scrollTop = messagesEl.scrollHeight;
      });
    }

    function resetChat() {
      conversation.length = 0;
      messagesEl.innerHTML = "";
      addMessage("assistant", "Xin chào. Tôi là giao diện Lab 3 theo phong cách chat. Bạn có thể hỏi liên tục về điều hướng khám Vinmec hoặc so sánh Chatbot, Agent v1, Agent v2.");
      statusEl.textContent = "Ready";
      traceStatusEl.textContent = "No run";
      traceEl.innerHTML = "<div class='sub'>Thought, Action và Observation sẽ xuất hiện ở đây.</div>";
      metaEl.innerHTML = "";
      questionEl.focus();
    }

    function renderMeta(data) {
      metaEl.innerHTML = "";
      [
        ["mode", data.mode],
        ["provider", data.provider],
        ["model", data.model],
        ["steps", data.steps],
        ["turns", data.turns],
      ].forEach(([key, value]) => {
        if (value === undefined || value === null || value === "") return;
        const pill = document.createElement("span");
        pill.className = "pill";
        pill.textContent = `${key}: ${value}`;
        metaEl.appendChild(pill);
      });
    }

    function renderTrace(trace) {
      const items = Array.isArray(trace) ? trace : [];
      if (!items.length) {
        traceEl.innerHTML = "<div class='sub'>Không có ReAct trace cho lượt này. Chatbot baseline trả lời trực tiếp nên không có Thought/Action/Observation.</div>";
        return;
      }

      traceEl.innerHTML = "";
      items.forEach((item, index) => {
        const card = document.createElement("div");
        card.className = "trace-card";

        const role = document.createElement("div");
        role.className = "trace-role";
        role.textContent = `${index + 1}. ${item.role || "step"}`;

        const pre = document.createElement("pre");
        pre.textContent = item.content || "";

        card.appendChild(role);
        card.appendChild(pre);
        traceEl.appendChild(card);
      });
      requestAnimationFrame(() => {
        traceEl.scrollTop = traceEl.scrollHeight;
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
    history = payload.get("history") or []

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
        "turns": len(history),
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
