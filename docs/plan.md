# Plan: chrome-agent-mcp-light

Input: [docs/intent.md](./intent.md), [docs/design.md](./design.md).
Status: draft. Order follows the SDLC loop: make it run → make it correct →
make it safe → keep it correct.

## Phase 0 — Make it run (blockers)

**Goal:** a client can connect and list the tools.

- [ ] **P0-1 Fix the MCP server import/API.** Replace
  `from mcp.server.mcpserver import MCPServer, Context` with the real SDK API
  (e.g. `FastMCP` from `mcp.server.fastmcp`) or the exact API of the pinned
  `mcp>=2.1.1`. Confirm against the installed wheel.
  *Acceptance:* `uv run python -c "import server"` succeeds; `mcp list` shows 6 tools + 1 prompt.
- [ ] **P0-2 Wire the entry point.** Move server code into
  `src/chrome_agent_mcp_light/server.py`; make `__init__.py:main()` start it.
  *Acceptance:* `uv run chrome-agent-mcp-light` starts the server.
- [ ] **P0-3 Resolve the `chrome-agent/` gitlink.** Either add it as a real submodule
  (`.gitmodules`) or remove it and rely on the PyPI dependency.
  *Acceptance:* `git submodule status` is clean or the path is gone.
- [ ] **P0-4 Ship `SKILL.md` as package data** so the prompt resolves post-install.
  *Acceptance:* prompt returns skill text from an installed wheel.

## Phase 1 — Make it correct (robustness)

- [ ] **P1-1 Add `run_chrome_agent(*argv)` helper** returning structured
  `{returncode, stdout, stderr}`, with a configurable timeout. Refactor all tools
  (`server.py:24-75`) to use it.
- [ ] **P1-2 Validate inputs.** Parse `params_json` and reject malformed JSON;
  validate `domain_method` shape (`Domain.method`).
- [ ] **P1-3 De-duplicate navigation.** `navigate_to_url` should delegate to
  `Page.navigate` via the generic path.
- [ ] **P1-4 Structured errors.** Non-zero exit → MCP tool error with stderr, not
  the current `stdout or stderr` fallback.

## Phase 2 — Make it safe (security & governance)

- [ ] **P2-1 Bind to `127.0.0.1` by default**; document how to change it.
- [ ] **P2-2 Write a REVIEW.md** defining review passes (bugs, security, trust-boundary
  changes, spec match) and severity; agent reviews PRs, code owner approves.
- [ ] **P2-3 Trust-boundary doc.** State that `evaluate_javascript` / `send_cdp_command`
  are arbitrary execution against the browser and list defaults.
- [ ] **P2-4 Optional enforcement hook.** A PreToolUse hook / permission rule that
  blocks a denylist of CDP methods in shared environments. (Prose in `SKILL.md` is
  advisory only — enforce in code.)

## Phase 3 — Keep it correct (feedback loop & evals)

- [ ] **P3-1 Single-command verification** (`make test` or `uv run pytest`) documented
  in CLAUDE.md/README.
- [ ] **P3-2 Unit + integration tests** (see [docs/test.md](./test.md)).
- [ ] **P3-3 Continuous evals:** 20–50 real agent tasks run non-interactively against
  `SKILL.md`/tool changes; gate config merges on pass rate.
- [ ] **P3-4 CI:** run tests + evals on every PR; sandbox with a disposable headless
  Chrome and short-lived credentials.

## Phase 4 — Harden & observe (optional)

- [ ] **P4-1 Relax `requires-python`** to `>=3.11` if the SDK permits, widening adoption.
- [ ] **P4-2 Structured logging** of every tool call (instance, method, exit code).
- [ ] **P4-3 Incident→eval ratchet:** every production incident becomes a permanent eval.

## Recommended sequence & rationale
`P0 → P1 → P3-1 → P2 → P3-2/3`. Get the server running and correct first
(the loop can't start otherwise), then establish the test path, then layer security
and governance, then automate gates. Do not automate CI before the manual loop works.

## Measurement

| Stage | Leading indicator | Lagging indicator |
| --- | --- | --- |
| P0 | server starts + lists tools | client can complete a launch→navigate→stop round-trip |
| P1 | unit coverage of `run_chrome_agent` | tool call failure rate |
| P2 | % of trust-boundary actions gated | security findings reaching main |
| P3 | first-pass CI success on agent changes | rework rate; review time |

## Definition of Done (program-level)
- `chrome-agent-mcp-light` installs and starts from a wheel.
- All 6 tools have passing unit tests and at least one integration test.
- Defaults are localhost-only and the trust boundary is documented.
- CI runs tests + evals and blocks merges on failure.
- A human code owner is required to merge.
