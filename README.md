# Eulerian Marketing Platform MCP Server

A Model Context Protocol (MCP) **proxy server** that bridges AI assistants (Claude Desktop, Gemini CLI, etc ...) to a remote Eulerian Marketing Platform MCP server. This proxy handles authentication, request forwarding, and provides a local MCP interface to your remote Eulerian instance.

## How It Works

This server acts as a **transparent proxy** between local MCP clients and your remote Eulerian Marketing Platform server:

```
┌─────────────┐        ┌──────────────────┐        ┌────────────────┐
│   Claude    │ ◄─────►│  This MCP Proxy  │◄─────► │ Remote Eulerian│
│   Desktop   │  stdio │  (Local)         │  HTTP  │  MCP Server    │
└─────────────┘        └──────────────────┘        └────────────────┘
```

The proxy:
- 🔐 Handles authentication with your remote Eulerian server
- 📡 Forwards MCP requests via HTTP with Bearer token
- 🛠️ Exposes remote tools and resources to AI assistants
- 📝 Provides comprehensive logging for debugging
- ⚡ Uses async HTTP for better performance

## Features

- **🔌 Proxy Architecture**: Bridges local MCP clients to remote Eulerian MCP server via HTTP
- **🔐 Secure Authentication**: Uses Bearer token authentication for remote server access
- **🌐 Cross-platform support**: Works on Windows, Linux, and macOS
- **🤖 Multiple AI clients**: Compatible with Claude Desktop and Gemini CLI
- **📝 Comprehensive Logging**: Logs all requests/responses for debugging
- **⚡ Async HTTP**: Non-blocking requests using httpx for better performance
- **🛠️ Tool Discovery**: Automatically discovers and exposes remote tools
- **⏱️ Configurable Timeouts**: Adjustable request timeouts

## Prerequisites

- Python 3.10 or higher
- Access to a remote Eulerian Marketing Platform MCP server (HTTP endpoint)
- Valid authentication token for the remote server
- One of the following AI clients:
  - Claude Desktop (Windows, macOS, Linux)
  - Gemini CLI
  - Codex CLI (macOS, Linux)
  - Claude Code (macOS, Linux)
  - Cursor (Windows, macOS, Linux)
  - VS Code with GitHub Copilot (Windows, macOS, Linux)

## Available Tools

All API Endpoints supported by the [Eulerian API](https://doc.api.eulerian.com) can be queried through the current MCP.

## Installation

### Quick Start (Recommended)

The easiest way to use this MCP server is with `pip`.

### Install via pip

If you prefer to install the package globally:

```bash
pip install eulerian-marketing-platform
```

### Alternative: Install from source

```bash
git clone https://github.com/EulerianTechnologies/eulerian-marketing-platform-mcp.git
cd eulerian-marketing-platform-mcp
pip install -e .
```

## Configuration

### Required Environment Variables

- `EMP_API_ENDPOINT`: Your remote Eulerian Marketing Platform MCP server URL (HTTP endpoint)
  - Example: `https://dem.api.eulerian.com/mcp`
- `EMP_API_TOKEN`: Your authentication token for the remote server, it is the one linked to your Eulerian account.

### Optional Environment Variables

- `EMP_LOG_FILE`: Log file location (default: `/tmp/eulerian-mcp-proxy.log`)
- `EMP_TIMEOUT`: Request timeout in seconds (default: `300`)

### Example `.env` file

Create a `.env.example` file in your project:

```bash
# Required
EMP_API_ENDPOINT=https://your-eulerian-instance.com/mcp
EMP_API_TOKEN=your_authentication_token_here

# Optional
EMP_LOG_FILE=/var/log/eulerian-mcp-proxy.log
EMP_TIMEOUT=600
```

## Setup Instructions by Client

### 1. Claude Desktop

Claude Desktop supports local MCP servers via stdio transport.

#### Configuration File Locations

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Setup Steps

1. **Open Claude Desktop**
2. **Access configuration**:
   - Click `Claude` menu → `Settings` → `Developer` → `Edit Config`
   - Or manually edit the JSON file at the location above

3. **Add the server configuration**:

```json
{
  "mcpServers": {
    "eulerian-marketing-platform": {
      "command": "python",
      "args": ["-m", "eulerian_marketing_platform.server"],
      "env": {
        "EMP_API_ENDPOINT": "https://your-eulerian-instance.com/mcp",
        "EMP_API_TOKEN": "your_authentication_token_here"
      }
    }
  }
}
```

4. **Restart Claude Desktop**

5. **Verify the connection**:
   - Look for a hammer/tools icon (🔨) in the bottom-right corner
   - Click it to see available Eulerian tools
   - Ask Claude: "What Eulerian Marketing Platform tools do you have access to?"

#### Platform-Specific Notes

**Windows**:
- Use the Run dialog (`Win + R`) and enter `%APPDATA%\Claude` to quickly navigate to the config directory
- If using a local installation, ensure Python is in your PATH

**Linux**:
- The config directory may not exist initially - create it with: `mkdir -p ~/.config/Claude`

**macOS**:
- Access the config via Finder: `Cmd + Shift + G` → `~/Library/Application Support/Claude/`

---

### 2. Gemini CLI

Gemini CLI supports MCP servers through its configuration file.

#### Prerequisites

Install Gemini CLI if you haven't already:

```bash
npm install -g @google/gemini-cli
```

#### Configuration File Location

`~/.gemini/settings.json`

#### Setup Steps

1. **Create or edit the settings file**:

```bash
# Create the directory if it doesn't exist
mkdir -p ~/.gemini

# Edit the settings file
nano ~/.gemini/settings.json
```

2. **Add the MCP server configuration**:

```json
{
  "mcpServers": {
    "eulerian-marketing-platform": {
      "command": "python",
      "args": ["-m", "eulerian_marketing_platform.server"],
      "env": {
        "EMP_API_ENDPOINT": "https://your-eulerian-instance.com/mcp",
        "EMP_API_TOKEN": "your_authentication_token_here"
      }
    }
  }
}
```

3. **Start Gemini CLI**:

```bash
gemini
```

4. **Verify the connection**:
   - Use the `/mcp` command to see connected servers
   - Ask Gemini: "What tools are available from the Eulerian Marketing Platform?"

#### Platform-Specific Notes

**Windows**:
- Settings file location: `%USERPROFILE%\.gemini\settings.json`
- Create directory: `mkdir %USERPROFILE%\.gemini`

**Linux/macOS**:
- Standard location: `~/.gemini/settings.json`

---

### 3. Codex CLI

Codex CLI supports MCP servers configured in `~/.codex/config.toml`. The configuration is shared between the CLI and the Codex IDE extension (VS Code).

#### Prerequisites

- Node.js 18+ and npm
- Codex CLI installed: `npm install -g @openai/codex`
- Python 3.10+ with this package installed (`pip install eulerian-marketing-platform`)
- A ChatGPT Plus, Pro, Team, Edu, or Enterprise subscription (or an OpenAI API key)

#### Option A: Using the `codex mcp add` command (easiest)

Run the following command to register the Eulerian MCP server:

```bash
codex mcp add eulerian-marketing-platform \
  --env EMP_API_ENDPOINT=https://your-eulerian-instance.com/mcp \
  --env EMP_API_TOKEN=your_authentication_token_here \
  -- python -m eulerian_marketing_platform.server
```

That's it — Codex will update `~/.codex/config.toml` for you.

#### Option B: Edit `config.toml` manually

Open (or create) `~/.codex/config.toml` and add the following:

```toml
[mcp_servers.eulerian-marketing-platform]
command = "python"
args = ["-m", "eulerian_marketing_platform.server"]
tool_timeout_sec = 300

[mcp_servers.eulerian-marketing-platform.env]
EMP_API_ENDPOINT = "https://your-eulerian-instance.com/mcp"
EMP_API_TOKEN = "your_authentication_token_here"
```

> **Note:** The section name **must** use `mcp_servers` (with an underscore). Using `mcp-servers` or any other variant will silently fail.

#### Option C: Project-scoped configuration

To limit the MCP server to a specific project, create a `.codex/config.toml` file at the root of that project with the same content as above. The project must be marked as trusted by Codex.

#### Verify the connection

1. Launch Codex in your terminal:
   ```bash
   codex
   ```
2. Type `/mcp` in the interactive TUI to see all connected MCP servers.
3. Confirm that `eulerian-marketing-platform` appears in the list with its available tools.
4. Try asking:
   ```
   What Eulerian Marketing Platform tools do you have access to?
   ```

#### Managing the server

```bash
# List all configured MCP servers
codex mcp

# Remove the server
codex mcp remove eulerian-marketing-platform
```

#### Troubleshooting (Codex CLI)

- **Server not appearing in `/mcp`**: Verify that the `[mcp_servers.eulerian-marketing-platform]` section is present in `~/.codex/config.toml` and that the TOML syntax is valid.
- **Timeout errors**: Increase `tool_timeout_sec` in config.toml (default is 60 seconds). Eulerian queries can take longer, so `300` is recommended.
- **Authentication errors**: Double-check that `EMP_API_ENDPOINT` and `EMP_API_TOKEN` are correct.
- **Python not found**: Ensure the `python` command resolves to Python 3.10+. You may need to use `python3` instead:
  ```toml
  command = "python3"
  ```
- **Package not found**: Make sure `eulerian-marketing-platform` is installed in the Python environment that Codex will invoke. Run `python -m eulerian_marketing_platform.server` manually to confirm it works.
- **Check logs**: Monitor the proxy logs for detailed error information:
  ```bash
  tail -f /tmp/eulerian-mcp-proxy.log
  ```

---

### 4. Claude Code

Claude Code is Anthropic's terminal-based coding agent. It supports MCP servers configured via the `claude mcp` CLI command or by editing `~/.claude.json`.

#### Prerequisites

- Node.js 18+ and npm
- Claude Code installed: `npm install -g @anthropic-ai/claude-code`
- Python 3.10+ with this package installed (`pip install eulerian-marketing-platform`)
- An Anthropic API key or Claude subscription

#### Option A: Using the `claude mcp add` command (easiest)

```bash
claude mcp add eulerian-marketing-platform \
  -e EMP_API_ENDPOINT=https://your-eulerian-instance.com/mcp \
  -e EMP_API_TOKEN=your_authentication_token_here \
  -- python -m eulerian_marketing_platform.server
```

By default this adds the server with **local** scope (current project only). To make it available in all projects, add the `-s user` flag:

```bash
claude mcp add -s user eulerian-marketing-platform \
  -e EMP_API_ENDPOINT=https://your-eulerian-instance.com/mcp \
  -e EMP_API_TOKEN=your_authentication_token_here \
  -- python -m eulerian_marketing_platform.server
```

#### Option B: Edit `~/.claude.json` manually

Open `~/.claude.json` and add the server under the `mcpServers` key:

```json
{
  "mcpServers": {
    "eulerian-marketing-platform": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "eulerian_marketing_platform.server"],
      "env": {
        "EMP_API_ENDPOINT": "https://your-eulerian-instance.com/mcp",
        "EMP_API_TOKEN": "your_authentication_token_here"
      }
    }
  }
}
```

#### Verify the connection

1. Launch Claude Code:
   ```bash
   claude
   ```
2. Type `/mcp` to see the status of all connected MCP servers.
3. Confirm that `eulerian-marketing-platform` appears and shows as **connected**.
4. Try asking:
   ```
   What Eulerian Marketing Platform tools do you have access to?
   ```

#### Managing the server

```bash
# List all configured MCP servers
claude mcp list

# Get details for a specific server
claude mcp get eulerian-marketing-platform

# Remove the server
claude mcp remove eulerian-marketing-platform
```

#### Troubleshooting (Claude Code)

- **Server not appearing in `/mcp`**: Run `claude mcp list` to confirm it is registered. Check `~/.claude.json` for JSON syntax errors.
- **Python not found**: Ensure the `python` command resolves to Python 3.10+. You may need to use `python3` instead.
- **Package not found**: Make sure `eulerian-marketing-platform` is installed in the Python environment that Claude Code will invoke.
- **Debug mode**: Launch Claude Code with verbose MCP logging:
  ```bash
  claude --mcp-debug
  ```
- **Check logs**: Monitor the proxy logs for detailed error information:
  ```bash
  tail -f /tmp/eulerian-mcp-proxy.log
  ```

---

### 5. Cursor

Cursor is an AI-powered code editor with built-in MCP support.

#### Prerequisites

- Cursor installed (download from [cursor.com](https://www.cursor.com))
- Python 3.10+ with this package installed (`pip install eulerian-marketing-platform`)

#### Configuration File Location

- **Global**: `~/.cursor/mcp.json`
- **Project-scoped**: `.cursor/mcp.json` in your project root

#### Setup Steps

1. **Open (or create) the configuration file**:

```bash
# Global configuration
mkdir -p ~/.cursor
nano ~/.cursor/mcp.json
```

2. **Add the MCP server configuration**:

```json
{
  "mcpServers": {
    "eulerian-marketing-platform": {
      "command": "python",
      "args": ["-m", "eulerian_marketing_platform.server"],
      "env": {
        "EMP_API_ENDPOINT": "https://your-eulerian-instance.com/mcp",
        "EMP_API_TOKEN": "your_authentication_token_here"
      }
    }
  }
}
```

3. **Restart Cursor** to load the new configuration.

4. **Verify the connection**:
   - Open Cursor Settings → **Tools & Integrations** → **MCP Servers**
   - Confirm that `eulerian-marketing-platform` appears and shows a green status
   - Switch to **Agent mode** in the Copilot pane
   - Ask: "What Eulerian Marketing Platform tools do you have access to?"

#### Platform-Specific Notes

**Windows**:
- Global config file: `%USERPROFILE%\.cursor\mcp.json`
- If `python` is not in your PATH, use the full path to the Python executable in the `command` field.

**macOS/Linux**:
- Standard location: `~/.cursor/mcp.json`

#### Troubleshooting (Cursor)

- **Server not appearing**: Verify that `~/.cursor/mcp.json` contains valid JSON. Restart Cursor after any config change.
- **Tools not available**: Make sure you are in **Agent mode** (not Ask mode) in the Cursor chat panel.
- **Python not found**: Ensure the `python` command resolves to Python 3.10+. You may need to use `python3` or a full path.
- **Check logs**: Monitor the proxy logs:
  ```bash
  tail -f /tmp/eulerian-mcp-proxy.log
  ```

---

### 6. VS Code / GitHub Copilot

Visual Studio Code supports MCP servers through GitHub Copilot's Agent mode. MCP requires VS Code 1.101 or later.

#### Prerequisites

- VS Code 1.101+ with the GitHub Copilot extension
- Python 3.10+ with this package installed (`pip install eulerian-marketing-platform`)
- A GitHub Copilot subscription

#### Configuration File Locations

- **Workspace**: `.vscode/mcp.json` in your project root (recommended)
- **User/Global**: accessible via the command `MCP: Open User Configuration`

> **Note:** VS Code uses a `"servers"` key (not `"mcpServers"`) inside `mcp.json`.

#### Setup Steps

1. **Create the workspace configuration file**:

```bash
mkdir -p .vscode
nano .vscode/mcp.json
```

2. **Add the MCP server configuration**:

```json
{
  "servers": {
    "eulerian-marketing-platform": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "eulerian_marketing_platform.server"],
      "env": {
        "EMP_API_ENDPOINT": "https://your-eulerian-instance.com/mcp",
        "EMP_API_TOKEN": "your_authentication_token_here"
      }
    }
  }
}
```

Alternatively, to make the server available globally across all workspaces, add the configuration to your **User Settings (JSON)** (`Ctrl+Shift+P` → `Preferences: Open User Settings (JSON)`):

```json
{
  "mcp": {
    "servers": {
      "eulerian-marketing-platform": {
        "type": "stdio",
        "command": "python",
        "args": ["-m", "eulerian_marketing_platform.server"],
        "env": {
          "EMP_API_ENDPOINT": "https://your-eulerian-instance.com/mcp",
          "EMP_API_TOKEN": "your_authentication_token_here"
        }
      }
    }
  }
}
```

3. **Start the MCP server**:
   - Open the `.vscode/mcp.json` file in the editor
   - Click the **Start** button that appears above the server definition (code lens)
   - Or use the Command Palette: `MCP: List Servers` → select the server → Start

4. **Verify the connection**:
   - Switch to **Agent mode** in the GitHub Copilot Chat panel (toggle located near the chat input)
   - Click the **Tools** button (🔧) in the Copilot pane to see available Eulerian tools
   - Ask: "What Eulerian Marketing Platform tools do you have access to?"

#### Using input variables for secrets

To avoid hardcoding your token, you can use VS Code input variables:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "empToken",
      "description": "Eulerian Marketing Platform API Token",
      "password": true
    }
  ],
  "servers": {
    "eulerian-marketing-platform": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "eulerian_marketing_platform.server"],
      "env": {
        "EMP_API_ENDPOINT": "https://your-eulerian-instance.com/mcp",
        "EMP_API_TOKEN": "${input:empToken}"
      }
    }
  }
}
```

VS Code will prompt you for the token when the server starts.

#### Troubleshooting (VS Code)

- **MCP not available**: Ensure you are running VS Code **1.101 or later** and have the GitHub Copilot extension installed and enabled.
- **Tools not appearing**: MCP tools only work in **Agent mode**. Toggle to Agent mode in the Copilot Chat panel.
- **Start button not showing**: The code lens (Start button) only appears if the `.vscode` folder is at the root of your workspace.
- **Python not found**: Ensure the `python` command resolves to Python 3.10+. You may need to use `python3` or a full path.
- **Check logs**: Monitor the proxy logs:
  ```bash
  tail -f /tmp/eulerian-mcp-proxy.log
  ```


---

## Usage Examples

Once configured with any client, you can interact with your remote Eulerian Marketing Platform:

```
User: "What tools are available from Eulerian?"
→ Proxy calls list_remote_tools() and returns all available tools

User: "Call the update_goal tool"
→ Proxy forwards to remote server and update goal settings

User: "Show me campaign details for CAMP-12345"
→ Claude uses call_eulerian_tool() to fetch specific campaign

User: "What resources are available?"
→ Proxy lists all available data sources
```

The AI assistant will automatically use the appropriate proxy tools to fulfill your requests.

### Viewing Logs

Monitor proxy activity in real-time:

```bash
# Default log location
tail -f /tmp/eulerian-mcp-proxy.log

# Custom log location
tail -f /var/log/eulerian-mcp-proxy.log
```

You'll see detailed logging of:
- Requests to the remote server
- HTTP responses and status codes
- Tool calls and results
- Errors and warnings

## Troubleshooting

### Common Issues

#### "EMP_API_ENDPOINT environment variable is required"
- **Solution**: Ensure you've set the `EMP_API_ENDPOINT` in your configuration
- Check that there are no typos in the environment variable name

#### "EMP_API_TOKEN environment variable is required"
- **Solution**: Ensure you've set the `EMP_API_TOKEN` in your configuration
- Verify your token is valid and hasn't expired

#### Server not appearing in Claude Desktop
- **Solution**: 
  - Restart Claude Desktop completely
  - Check the configuration file for JSON syntax errors
  - Verify the file path in your config is correct
  - Look at logs: 
    - macOS: `~/Library/Logs/Claude/mcp-server-*.log`
    - Windows: `%APPDATA%\Claude\logs\`

#### Tools not showing in Gemini CLI
- **Solution**:
  - Use `/mcp` command to check server status
  - Verify the settings.json is valid JSON
  - Restart Gemini CLI

### Debug Mode

For detailed debugging:

```bash
# Run with MCP Inspector
npx @modelcontextprotocol/inspector uvx eulerian-marketing-platform

# Or with environment variables
EMP_API_ENDPOINT=your_endpoint EMP_API_TOKEN=your_token uvx eulerian-marketing-platform
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=eulerian_marketing_platform
```

### Building from Source

```bash
# Clone the repository
git clone https://github.com/EulerianTechnologies/eulerian-marketing-platform-mcp.git
cd eulerian-marketing-platform-mcp

# Install in development mode
pip install -e .

# Build distribution
pip install build
python -m build

# This creates:
# dist/eulerian_marketing_platform-0.1.0.tar.gz
# dist/eulerian_marketing_platform-0.1.0-py3-none-any.whl
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: https://github.com/EulerianTechnologies/eulerian-marketing-platform-mcp/issues
- **Documentation**: https://github.com/EulerianTechnologies/eulerian-marketing-platform-mcp#readme
- **Eulerian Technologies**: https://www.eulerian.com

## MCP server for MCP Registry

mcp-name: io.github.matjmat/eulerian-marketing-platform-mcp

## Changelog

### 0.2.8
- fixes for proxy disconnection
- remove unnecessary logging

### 0.2.3
- fixes disconnection issue with notifications

### 0.2.0
- Move to full Proxy mode
- Remove instructions for uvx deployment
- Remove instructions for Mistral integration (too complex)

### 0.1.0 (Initial Release)
- Initial MCP server implementation
- Support for Claude Desktop, Gemini CLI
- Cross-platform support (Windows, Linux, macOS)
- Environment-based configuration

---

**Note**: Replace all placeholder URLs and tokens with your actual Eulerian Marketing Platform credentials before use.
