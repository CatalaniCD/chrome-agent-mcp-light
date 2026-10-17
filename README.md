# chrome-agent-mcp-light

A lightweight [MCP](https://modelcontextprotocol.io) server that gives AI agents control over a live, native Google Chrome / Chromium browser via the raw [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/) (CDP).

Rather than wrapping an automation framework, this server drives `chrome-agent` directly. This preserves a native browser environment (`navigator.webdriver === false`) and exposes the full CDP surface, so any DOMAIN.method command is available.

## Features

- Launch and stop Chrome instances with CDP enabled
- Inspect active instances, tabs, URLs, and titles
- Navigate, execute JavaScript, and capture screenshots
- Dispatch raw CDP commands (native input events, network, rendering, etc.)
- Exposes a `chrome_agent_skill` prompt that injects procedural guidance to the agent

## Requirements

- Python >= 3.14
- [`uv`](https://docs.astral.sh/uv/) (recommended)
- Google Chrome or Chromium installed

## Installation

```bash
uv sync
```

## Usage

Run the MCP server over streamable HTTP:

```bash
uv run server.py
```

### MCP client configuration

Add the server to your MCP client (Claude Desktop, Cursor, etc.). Example:

```json
{
  "mcpServers": {
    "chrome-agent-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/chrome-agent-mcp-light", "server.py"]
    }
  }
}
```

## Tools

| Tool | Description |
| --- | --- |
| `launch_browser(headless=False)` | Launches a Chrome instance with CDP enabled. |
| `get_browser_status()` | Lists running instances and their active tabs. |
| `navigate_to_url(instance, url)` | Navigates a specific instance to a URL. |
| `evaluate_javascript(instance, expression)` | Executes JavaScript on the active page. |
| `send_cdp_command(instance, domain_method, params_json)` | Sends any raw CDP command. |
| `stop_browser(instance)` | Gracefully shuts down an instance. |

### Prompt

- `chrome_agent_skill` — returns the contents of `SKILL.md`, which documents the recommended **Locate → Act → Verify** workflow and CDP guardrails.

## Example workflow

1. `launch_browser` and capture the instance name from the response.
2. `send_cdp_command` with `Page.navigate` to load a URL.
3. Use `Runtime.evaluate` to locate elements, then `Input.dispatchMouseEvent` to click.
4. `stop_browser` when finished.

See [`SKILL.md`](./SKILL.md) for the full procedural guide.

## License

See repository for license details.
