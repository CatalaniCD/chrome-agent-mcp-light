# Test: chrome-agent-mcp-light

Input: [docs/design.md](./design.md), [docs/plan.md](./plan.md).
Status: draft. Goal: give every session a single-command verification path and
close the loop with continuous evals.

## 1. Test strategy

| Level | What it verifies | Speed | Frequency |
| --- | --- | --- | --- |
| Unit | CLI adapter (`run_chrome_agent`), input validation, error mapping | ms | every commit |
| Integration | Tools against a real headless Chrome via `chrome-agent` | seconds | every PR |
| Prompt/Skill | `chrome_agent_skill` returns `SKILL.md` content | ms | every PR |
| Evals | Real agent tasks end-to-end (non-interactive) | minutes | config change + schedule |
| Smoke (manual) | Human-in-the-loop visual debugging | — | release |

**Single-command verification (to document in CLAUDE.md/README):**
```bash
uv run pytest            # unit + integration + prompt
```
Add a `make test` wrapper if preferred.

## 2. Unit tests

### 2.1 CLI adapter
- `run_chrome_agent` passes argv through verbatim (list, no shell).
- Non-zero `returncode` produces a structured error, not stdout fallback.
- Timeout is enforced (simulate a slow/fake binary).
- `stdout`/`stderr` are both captured.

### 2.2 Input validation
- `send_cdp_command` rejects malformed `params_json` (e.g. `"{not json"`).
- `domain_method` must match `Domain.method` (reject `navigate`, `Page.`).
- `navigate_to_url` percent/quoting of URLs is safe.

### 2.3 Prompt
- `chrome_agent_skill` returns file contents when `SKILL.md` exists.
- Returns the documented error string when it is missing.

### 2.4 Import/API regression
- `import server` (or the packaged module) succeeds — this is the P0 blocker guard.

## 3. Integration tests

Run against a disposable headless Chrome. Skip with a marker if no browser is present.

| # | Scenario | Expected |
| --- | --- | --- |
| I1 | `launch_browser(headless=True)` then `get_browser_status` | instance appears in status output |
| I2 | `navigate_to_url(instance, "about:blank")` | navigation succeeds; status shows URL |
| I3 | `evaluate_javascript(instance, "1+1")` | returns `2` |
| I4 | `send_cdp_command(instance, "Runtime.evaluate", '{"expression":"document.title","returnByValue":true}')` | returns a title value |
| I5 | `send_cdp_command(instance, "Page.captureScreenshot", '{"format":"png"}')` | base64 string returned |
| I6 | `navigate_to_url` to an invalid URL | structured error, no hang |
| I7 | `stop_browser(instance)` | instance removed from status |
| I8 | full lifecycle launch→navigate→evaluate→stop | all steps succeed; no leaked process |

**Native-environment assertion (design-critical):**
- After `launch_browser`, evaluate `navigator.webdriver` and assert it is `false`.
  This is the core value proposition and must be a test, not an assumption.

**Locate → Act → Verify (from SKILL.md):**
- Load a page with a button, compute coords via `Runtime.evaluate`, dispatch
  `Input.dispatchMouseEvent` press+release, then assert the DOM mutated.

## 4. Continuous evals

The loop that keeps agent behavior stable as `SKILL.md`/tools/hooks change.

- **Corpus:** 20–50 real, non-interactive tasks (navigate to a known page and extract
  a value; click through a flow; capture a screenshot; recover from a stale selector).
- **Runner:** execute each task with a fixed model/config in CI; record pass/fail.
- **Gating:** a config/`SKILL.md`/tool change must not drop pass rate below baseline.
- **Ratchet:** every production incident (e.g. agent hung the browser, wrong element
  clicked) becomes a permanent eval case.
- **Backoff coverage:** include a task where the selector is initially absent to test
  the documented retry-with-backoff guidance in `SKILL.md`.

## 5. CI

- On PR: `uv run pytest` + eval suite (sandboxed, disposable Chrome, short-lived creds).
- Block merge on test or eval failure.
- Branch protection: code-owner approval required; agent does not self-approve.
- Upload test/eval output as the committed evidence for the change.

## 6. Measurement

| Leading | Lagging |
| --- | --- |
| first-pass CI success for agent changes | review time; change failure rate |
| eval pass rate | regressions reaching main |
| % tool calls with a matching test | escaped defects |

## 7. Definition of Done
- `uv run pytest` green with no browser installed (unit/prompt tiers).
- Integration tier passes locally and in CI with Chrome available.
- `navigator.webdriver === false` assertion present.
- Eval suite runs and gates merges; baseline recorded.
- Every unresolved incident opens an eval case.
