# Design: chrome-agent-mcp-light

Status: draft. Input: [docs/intent.md](./intent.md).

## 1. Current-state assessment

A snapshot of the repository as evaluated. Treat this as the gap analysis the design must close.

| Area | Current state | Assessment |
| --- | --- | --- |
| Server | `server.py` defines 6 tools + 1 prompt via `MCPServer` | Core logic present |
| SDK import | `from mcp.server.mcpserver import MCPServer, Context` (`server.py:5`) | **Non-standard API.** The MCP SDK exposes `FastMCP` from `mcp.server.fastmcp`; `mcp.server.mcpserver.MCPServer` is not a known module/class. Server likely fails to import. |
| Package entry point | `pyproject.toml:16` → `chrome_agent_mcp_light:main` | **Broken wiring.** `main()` in `src/chrome_agent_mcp_light/__init__.py` only prints `Hello from chrome-agent-mcp-light!`. The real server lives in root `server.py`, outside the package, so `uv build`/the console script never start it. |
| `chrome-agent/` | Empty directory tracked as gitlink `160000`, no `.gitmodules` | **Broken submodule ref.** `git submodule status` errors: "no submodule mapping found". |
| Tests | none | No verification path (violates the single-command loop). |
| `requires-python` | `>=3.14` | Very new; narrows install base. |
| Error handling | `result.stdout or result.stderr`; no `returncode` check, no timeout | Silent failures; hangs possible. |
| Security | Fixed-argv `subprocess` (no `shell=True`) — good | But HTTP transport has no auth; CDP tools are RCE-by-design. |

## 2. Target architecture

```
MCP client (agent)
      │  streamable HTTP
      ▼
┌────────────────────────────────────────────┐
│ chrome-agent-mcp-light (MCP server)        │
│                                            │
│  prompt: chrome_agent_skill ──► SKILL.md   │
│                                            │
│  tools:                                    │
│    launch_browser    ─┐                    │
│    stop_browser       │                    │
│    get_browser_status │   subprocess(argv) │
│    navigate_to_url    ├──► chrome-agent    │
│    evaluate_javascript│   CLI              │
│    send_cdp_command  ─┘                    │
└────────────────────────────────────────────┘
      │
      ▼
 native Chrome/Chromium (CDP, navigator.webdriver === false)
```

**Design principle:** the server is a thin, stateless adapter. All browser state
lives in Chrome and is discovered via `chrome-agent status`; the server holds no
session registry. Instance identity is passed by the caller on every tool call.

## 3. Components

### 3.1 MCP server surface
- **Prompt `chrome_agent_skill`** — reads `SKILL.md` from the server root and returns
  it verbatim; degrades to an error string if missing.
- **Lifecycle tools** — `launch_browser(headless)`, `get_browser_status()`,
  `stop_browser(instance)`.
- **Interaction tools** — `navigate_to_url(instance, url)`,
  `evaluate_javascript(instance, expression)`,
  `send_cdp_command(instance, domain_method, params_json)`.

### 3.2 CLI adapter (recommended refactor)
Extract a single internal helper, e.g. `run_chrome_agent(*argv) -> ToolResult`, that:
1. enforces a timeout,
2. captures `returncode`, `stdout`, `stderr`,
3. returns a structured result (JSON) rather than `stdout or stderr`,
4. surfaces non-zero exit as an MCP tool error.

All tools then call this helper. This removes the current duplication across
`server.py:24-75`.

### 3.3 Packaging
- Move server construction into `src/chrome_agent_mcp_light/server.py`.
- `__init__.py:main()` should import and run the server (or delegate to a `cli` module).
- Keep the console script `chrome-agent-mcp-light = "chrome_agent_mcp_light:main"`.
- Ship `SKILL.md` as package data so the prompt works after install (today it reads a
  repo-relative path resolved from `__file__`).

### 3.4 Skill/prompt asset
`SKILL.md` documents the **Locate → Act → Verify** loop and CDP payload examples. It
is the agent-facing contract and should be versioned with the code.

## 4. Key design decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Abstraction layer | None; raw CDP via CLI | Preserves native fingerprint, full protocol surface. |
| State model | Stateless server; Chrome is source of truth | Simplicity; no session desync. |
| Tool granularity | Coarse lifecycle + one generic `send_cdp_command` | Covers 95% use with few tools; generic escape hatch. |
| `navigate_to_url` | **Inconsistent** — duplicates `send_cdp_command` instead of wrapping it | Should delegate to `Page.navigate` for one code path. |
| Transport | streamable HTTP | Remote-friendly; needs an auth story. |

## 5. Non-functional requirements

- **Latency:** each tool call is bounded by the CLI round-trip; add a configurable timeout.
- **Reliability:** no hanging subprocesses; deterministic errors on failure.
- **Security:** default bind to `127.0.0.1`; document the RCE trust boundary; no secrets
  in logs; short-lived credentials if ever run in CI.
- **Observability:** every tool call should be traceable (instance, method, exit code).
- **Portability:** Linux/macOS first; Chrome discovery delegated to `chrome-agent`.

## 6. Risks and open gaps

1. **Server does not start** (non-standard SDK import) — highest priority.
2. **Entry point never runs the server** — packaging bug.
3. **Broken `chrome-agent` gitlink** — clone/submodule reproducibility.
4. **No auth on HTTP transport** — network exposure for an RCE-capable service.
5. **No tests/evals** — no way to gate changes.

## 7. Governance

- **Human gates:** production-impacting CDP actions and any change to the trust
  boundary (adding `shell=True`, auth removal) require a code-owner approval.
- **Advisory vs. deterministic:** `SKILL.md` is advisory guidance to the agent. Hard
  requirements (e.g. block `send_cdp_command` for a denylisted domain in shared
  environments) must be enforced by a PreToolUse hook or explicit permission rule —
  not by prose.
- **Separation of duties:** the agent never approves its own PR; a human merges.
