# Intent: chrome-agent-mcp-light

Author: [unassigned]. Status: draft.

## Problem
AI coding agents cannot drive a real, native browser. Existing automation stacks
(Puppeteer/Playwright/Selenium) change the runtime environment — setting
`navigator.webdriver`, injecting overlays, and adding an abstraction layer that
hides the real Chrome DevTools Protocol (CDP). This breaks detection-sensitive
workflows and prevents agents from issuing arbitrary CDP commands.

There is no lightweight, protocol-faithful bridge that lets an MCP-speaking agent
launch native Chrome, navigate, evaluate JS, dispatch hardware-level input, and
send any raw CDP primitive — without an abstraction layer in the way.

## Proposed outcome
A small MCP server (`chrome-agent-mcp-light`) that wraps the `chrome-agent` CLI
and exposes it to agents as a stable set of MCP tools plus a procedural prompt.
Agents can:
- launch / stop native Chrome instances with CDP enabled,
- inspect instance and tab state,
- navigate, evaluate JavaScript, and capture screenshots,
- dispatch raw `DOMAIN.method` CDP commands (including `Input.dispatchMouseEvent`).

The runtime environment stays native (`navigator.webdriver === false`) because no
automation framework is injected.

## Affected users and systems
- **Primary users:** AI agents (via MCP clients: Claude Desktop, Cursor, etc.) acting
  on behalf of a developer/operator.
- **Secondary users:** developers building browser-automation workflows and the
  operators who run the MCP server.
- **Systems:** the `chrome-agent` CLI, local Chrome/Chromium, and the MCP client
  transport (streamable HTTP).

## Constraints
- **Language/runtime:** Python `>=3.14` (uv-managed; see `pyproject.toml`).
- **No abstraction layer:** must shell out to `chrome-agent` and preserve a native
  browser fingerprint.
- **Trust boundary:** `evaluate_javascript` and `send_cdp_command` are arbitrary
  code execution against the browser by design; the server is a privileged component.
- **Transport:** currently streamable HTTP; no authentication layer defined.
- **Out of scope:** cross-browser support, cloud browser fleets, recording/replay.

## Open questions
- Who is the accountable owner, and which repository hosts `intent.md` / `docs/`?
- What is the supported MCP client(s) and the intended deployment surface
  (localhost only vs. shared host)?
- Should `requires-python = ">=3.14"` be relaxed to widen adoption, or is 3.14 required?
- Is `chrome-agent/` intended to be a vendored submodule? It is currently a broken
  gitlink with no `.gitmodules` mapping.
- Which CDP domains/methods are considered safety-critical and require an explicit
  human gate (e.g. `Page.navigate` to production, `Browser.close`)?
