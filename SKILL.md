

---
name: chrome-agent-mcp
description: Controls an active, native Google Chrome browser via raw Chrome DevTools Protocol (CDP) commands. Allows launching instances, navigating, executing JavaScript, capturing screenshots, and dispatching real hardware-level input events without an abstraction layer.
---

# Procedural Guide: chrome-agent-mcp
Execute this skill to control, observe, and interact with a live Chrome or Chromium browser using raw Chrome DevTools Protocol (CDP) primitives.

## 1. Operational Lifecycle
You must manage the browser lifecycle explicitly. Do not leave headless browser processes hanging after completing a task.

### Launching an Instance* Call `launch_browser` at the beginning of a workflow if no active instance exists.
* **Input parameter:** `headless` (boolean, defaults to `true`). Set to `false` only if visual human-in-the-loop debugging is required.
* **Output:** Capture the generated instance name (e.g., `myproject-01`) from the JSON response. You will need this name for all subsequent commands.

### Verifying State* Call `get_browser_status` to audit active instances, open tabs, current URLs, and page titles if context is lost or if matching against a pre-existing target.

### Terminating the Session* Call `stop_browser` with the exact `instance` name immediately after your final assertion or data extraction is complete.

---

## 2. Interaction Model: Locate-Act-Verify
Do not guess coordinates or attempt to interact blindly. You must strictly execute the **Locate, Act, Verify** loop for every element interaction.

[ Locate ] ──> Evaluate JS to extract DOM coordinates (x, y)
    │
[ Act ] ──> Dispatch native mouse/keyboard CDP events at (x, y)
    │
[ Verify ] ──> Query the DOM or page state to confirm state mutation


### Step 1: Locate
Execute `send_cdp_command` with the `Runtime.evaluate` method to calculate the exact viewport midpoint coordinates of the target element.

* **Command payload formatting:**
  ```json
  {
    "instance": "<instance-name>",
    "domain_method": "Runtime.evaluate",
    "params_json": "{\"expression\": \"(() => { const r = document.querySelector('<css-selector>').getBoundingClientRect(); return {x: r.x + r.width/2, y: r.y + r.height/2}; })()\", \"returnByValue\": true}"
  }
  ```

### Step 2: Act
Using the precise `x` and `y` coordinates returned from the Locate step, dispatch sequential hardware-level input events using `Input.dispatchMouseEvent`. You must send both a press and a release to register a complete click.

* **Mouse Press Action:**
  ```json
  {
    "instance": "<instance-name>",
    "domain_method": "Input.dispatchMouseEvent",
    "params_json": "{\"type\": \"mousePressed\", \"x\": <x_coord>, \"y\": <y_coord>, \"button\": \"left\", \"clickCount\": 1}"
  }
  ```

* **Mouse Release Action:** Execute immediately following the press event:
  ```json
  {
    "instance": "<instance-name>",
    "domain_method": "Input.dispatchMouseEvent",
    "params_json": "{\"type\": \"mouseReleased\", \"x\": <x_coord>, \"y\": <y_coord>, \"button\": \"left\", \"clickCount\": 1}"
  }
  ```

### Step 3: Verify
Execute a fast validation check via `Runtime.evaluate` (e.g., assessing `document.title`, URL changes, or checking for the presence/absence of specific DOM nodes) to confirm the action succeeded before proceeding to the next step.

---

## 3. Core CDP Command Reference

Use these standard payloads for common browsing workflows via `send_cdp_command`:

### Browser Navigation
* **Method:** `Page.navigate`
* **Payload:** `{"url": "https://example.com"}`

### Visual Capture (Screenshot)
* **Method:** `Page.captureScreenshot`
* **Payload:** `{"format": "png"}` *(Returns base64 encoded string data)*

### Extracting Text or Attributes
* **Method:** `Runtime.evaluate`
* **Payload:** `{"expression": "document.querySelector('h1').innerText", "returnByValue": true}`

---

## 4. Execution Guardrails & Constraints

* **JSON String Escaping:** The `params_json` tool parameter accepts a stringified JSON object. You must double-escape all interior quotation marks (e.g., `"{\"url\": \"https://target.com\"}"`). 
* **Native Environment Shape:** Do not manually inject scripts to mask or modify `navigator.webdriver`. A pure CDP connection naturally leaves `navigator.webdriver === false` intact. Standard automation-detection suites pass natively as long as the runtime environment is left un-mutated.
* **Asynchronous Page State:** If a `Runtime.evaluate` call returns `null` or throws a target selector error, the DOM may still be rendering. Implement a retry loop with an incremental backing-off delay before failing.
