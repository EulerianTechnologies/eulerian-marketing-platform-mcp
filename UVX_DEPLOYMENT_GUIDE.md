# UVX Deployment Guide

This guide ensures your MCP server is properly set up for deployment with `uvx`.

## What is uvx?

`uvx` is a tool that runs Python applications in isolated environments without requiring installation. It's part of the `uv` package manager by Astral (creators of ruff).

**Benefits:**
- ✅ No manual `pip install` needed
- ✅ Automatic dependency management
- ✅ Isolated environments (no conflicts)
- ✅ Always uses the correct Python version
- ✅ Faster than traditional pip

## Step 1: Check if uvx is Installed

### On Linux/macOS:
```bash
uvx --version
```

### On Windows (PowerShell):
```powershell
uvx --version
```

### Expected Output (if installed):
```
uvx 0.5.0
```

### If Not Installed:
Continue to Step 2.

---

## Step 2: Install uv (includes uvx)

Choose the method that works best for your system:

### **Method 1: Official Installer (Recommended)**

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell - Run as Administrator):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, **restart your terminal** to update your PATH.

---

### **Method 2: Via pip**

If you prefer using pip:

```bash
pip install uv
```

---

### **Method 3: Via pipx (Isolated)**

If you have pipx installed:

```bash
pipx install uv
```

---

### **Method 4: Via Homebrew (macOS only)**

```bash
brew install uv
```

---

## Step 3: Verify Installation

After installation, verify it works:

```bash
uvx --version
```

You should see something like:
```
uvx 0.5.0
```

Also verify `uv` itself:
```bash
uv --version
```

---

## Step 4: Test with Eulerian MCP Server

### **Option A: Test from PyPI (after publishing)**

Once you've published your package to PyPI:

```bash
# Test without installation
uvx eulerian-marketing-platform --help

# Run with environment variables
EMP_API_ENDPOINT=https://test.com/mcp \
EMP_API_TOKEN=test_token \
uvx eulerian-marketing-platform
```

---

### **Option B: Test Locally (before publishing)**

If you haven't published to PyPI yet, test from your local directory:

```bash
# From the project root directory
cd eulerian-marketing-platform-mcp

# Build the package first
pip install build
python -m build

# Test with uvx using the local wheel file
uvx --from ./dist/eulerian_marketing_platform-0.1.0-py3-none-any.whl eulerian-marketing-platform

# Or test with environment variables
EMP_API_ENDPOINT=https://test.com/mcp \
EMP_API_TOKEN=test_token \
uvx --from ./dist/eulerian_marketing_platform-0.1.0-py3-none-any.whl eulerian-marketing-platform
```

---

## Step 5: Configure AI Clients with uvx

### **Claude Desktop Configuration**

#### **Linux:**
Edit: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "eulerian-marketing-platform": {
      "command": "uvx",
      "args": ["eulerian-marketing-platform"],
      "env": {
        "EMP_API_ENDPOINT": "https://your-eulerian-instance.com/mcp",
        "EMP_API_TOKEN": "your_authentication_token_here"
      }
    }
  }
}
```

#### **macOS:**
Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

(Same JSON as above)

#### **Windows:**
Edit: `%APPDATA%\Claude\claude_desktop_config.json`

(Same JSON as above)

---

### **Gemini CLI Configuration**

#### **All Platforms:**
Edit: `~/.gemini/settings.json` (Windows: `%USERPROFILE%\.gemini\settings.json`)

```json
{
  "mcpServers": {
    "eulerian-marketing-platform": {
      "command": "uvx",
      "args": ["eulerian-marketing-platform"],
      "env": {
        "EMP_API_ENDPOINT": "https://your-eulerian-instance.com/mcp",
        "EMP_API_TOKEN": "your_authentication_token_here"
      }
    }
  }
}
```

---

## Step 6: Troubleshooting

### Issue: "uvx: command not found"

**Solution 1:** Restart your terminal after installation

**Solution 2:** Check if uv is in your PATH
```bash
# Linux/macOS
which uv
echo $PATH

# Windows (PowerShell)
where.exe uv
$env:PATH
```

**Solution 3:** Manually add to PATH

**Linux/macOS:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc  # or ~/.zshrc
```

**Windows (PowerShell - Run as Administrator):**
```powershell
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "User") + ";$env:LOCALAPPDATA\Programs\uv",
    "User"
)
```

---

### Issue: "Package not found: eulerian-marketing-platform"

This happens if the package isn't published to PyPI yet.

**Solution:** Test locally using the `--from` flag:
```bash
uvx --from ./dist/eulerian_marketing_platform-0.1.0-py3-none-any.whl eulerian-marketing-platform
```

Or install with pip first:
```bash
pip install eulerian-marketing-platform
```

Then use in Claude config:
```json
{
  "command": "python",
  "args": ["-m", "eulerian_marketing_platform.server"]
}
```

---

### Issue: "uvx is slow on first run"

**Explanation:** First run downloads and caches dependencies. Subsequent runs are fast.

**Solution:** This is normal. Wait for the first run to complete (~10-30 seconds).

---

### Issue: Environment variables not being read

**Solution:** Check that env variables are in the config file, not your shell:

**Correct (in claude_desktop_config.json):**
```json
{
  "env": {
    "EMP_API_ENDPOINT": "https://...",
    "EMP_API_TOKEN": "..."
  }
}
```

**Incorrect (don't set in terminal - won't work with Claude Desktop):**
```bash
export EMP_API_ENDPOINT=...  # This won't work for Claude Desktop
```

---

## Alternative: Without uvx

If you prefer not to use `uvx`, you can use standard Python:

### 1. Install the package:
```bash
pip install eulerian-marketing-platform
```

### 2. Update configuration to use Python:

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

---

## Deployment Checklist

Before deploying to users, verify:

- [ ] ✅ `uvx --version` works on your system
- [ ] ✅ Package builds successfully: `python -m build`
- [ ] ✅ Local test works: `uvx --from ./dist/*.whl eulerian-marketing-platform`
- [ ] ✅ Environment variables are correctly set in AI client config
- [ ] ✅ Package is published to PyPI (or distributed to users)
- [ ] ✅ Users can run: `uvx eulerian-marketing-platform`
- [ ] ✅ Logs appear in: `/tmp/eulerian-mcp-proxy.log`
- [ ] ✅ Remote Eulerian server is accessible
- [ ] ✅ Authentication token is valid

---

## Publishing to PyPI (for uvx to work everywhere)

For `uvx eulerian-marketing-platform` to work without `--from`, you need to publish to PyPI:

### 1. Build the package:
```bash
pip install build twine
python -m build
```

### 2. Create PyPI account:
- Go to https://pypi.org/account/register/
- Create account
- Create API token at https://pypi.org/manage/account/token/

### 3. Publish:
```bash
# Test on TestPyPI first (recommended)
twine upload --repository testpypi dist/*

# If it works, publish to real PyPI
twine upload dist/*
```

### 4. Now anyone can use:
```bash
uvx eulerian-marketing-platform
```

---

## Quick Reference

### Check Installation:
```bash
uvx --version
```

### Install uv:
```bash
# Official installer (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Official installer (Windows PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip
pip install uv
```

### Test Package:
```bash
# From PyPI
uvx eulerian-marketing-platform

# From local build
uvx --from ./dist/*.whl eulerian-marketing-platform
```

### Claude Desktop Config:
```json
{
  "mcpServers": {
    "eulerian": {
      "command": "uvx",
      "args": ["eulerian-marketing-platform"],
      "env": {
        "EMP_API_ENDPOINT": "your_endpoint",
        "EMP_API_TOKEN": "your_token"
      }
    }
  }
}
```

---

## Support

If you encounter issues:

1. **Check logs:** `tail -f /tmp/eulerian-mcp-proxy.log`
2. **Verify uvx:** `uvx --version`
3. **Test manually:** `uvx eulerian-marketing-platform`
4. **Check environment:** Ensure `EMP_API_ENDPOINT` and `EMP_API_TOKEN` are in config file
5. **Restart AI client** after config changes

For more help, open an issue at:
https://github.com/EulerianTechnologies/eulerian-marketing-platform-mcp/issues
