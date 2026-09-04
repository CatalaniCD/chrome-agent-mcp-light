
import os
import subprocess
import json
from mcp.server.mcpserver import MCPServer, Context

# Initialize FastMCP Server
mcp = MCPServer("Chrome Agent MCP")

@mcp.prompt()
def chrome_agent_skill(ctx: Context) -> str:
    """Provides the procedural guidelines and constraints for managing Chrome via CDP."""
    # Locate the SKILL.md file in the project directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    skill_path = os.path.join(base_dir, "SKILL.md")
    
    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: SKILL.md documentation file not found on the server root."

@mcp.tool()
def launch_browser(headless: bool = False) -> str:
    """Launches a Chrome browser instance with CDP enabled."""
    cmd = ["chrome-agent", "launch"]
    if headless:
        cmd.append("--headless")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout or result.stderr

@mcp.tool()
def get_browser_status() -> str:
    """Lists running Chrome instances and their active tabs."""
    result = subprocess.run(["chrome-agent", "status"], capture_output=True, text=True)
    return result.stdout or "No active instances found."

@mcp.tool()
def navigate_to_url(instance: str, url: str) -> str:
    """Navigates a specific browser instance to a URL."""
    params = json.dumps({"url": url})
    result = subprocess.run(
        ["chrome-agent", instance, "Page.navigate", params], 
        capture_output=True, text=True
    )
    return result.stdout or result.stderr

@mcp.tool()
def evaluate_javascript(instance: str, expression: str) -> str:
    """Executes JavaScript on the active page and returns the result."""
    params = json.dumps({"expression": expression, "returnByValue": True})
    result = subprocess.run(
        ["chrome-agent", instance, "Runtime.evaluate", params], 
        capture_output=True, text=True
    )
    return result.stdout or result.stderr

@mcp.tool()
def stop_browser(instance: str) -> str:
    """Gracefully shuts down a specific browser instance."""
    result = subprocess.run(["chrome-agent", "stop", instance], capture_output=True, text=True)
    return result.stdout or result.stderr

@mcp.tool()
def send_cdp_command(instance: str, domain_method: str, params_json: str = "{}") -> str:
    """
    Sends any raw Chrome DevTools Protocol command to a running instance.
    Example: domain_method="Page.captureScreenshot", params_json='{"format": "png"}'
    """
    result = subprocess.run(
        ["chrome-agent", instance, domain_method, params_json], 
        capture_output=True, text=True
    )
    return result.stdout or result.stderr


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
