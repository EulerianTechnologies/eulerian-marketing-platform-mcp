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

## Changelog

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
