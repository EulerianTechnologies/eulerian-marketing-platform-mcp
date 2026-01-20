# Quick UVX Installation Script for Windows
# Run this in PowerShell as Administrator

Write-Host "=== Eulerian Marketing Platform MCP Server - UVX Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if uvx is already installed
Write-Host "Checking for uvx installation..." -ForegroundColor Yellow
$uvxExists = Get-Command uvx -ErrorAction SilentlyContinue

if ($uvxExists) {
    $version = uvx --version 2>&1 | Select-Object -First 1
    Write-Host "✓ uvx is already installed: $version" -ForegroundColor Green
    exit 0
}

Write-Host "⚠ uvx is not installed. Installing now..." -ForegroundColor Yellow
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "✗ This script requires Administrator privileges" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Install uv (which includes uvx)
Write-Host "Installing uv (which includes uvx) via official installer..." -ForegroundColor Cyan
Write-Host "Running: irm https://astral.sh/uv/install.ps1 | iex" -ForegroundColor Gray
Write-Host ""

try {
    powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    Write-Host ""
    Write-Host "✓ Installation completed!" -ForegroundColor Green
}
catch {
    Write-Host "✗ Installation failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please try installing manually:" -ForegroundColor Yellow
    Write-Host "  Option 1 (recommended):" -ForegroundColor White
    Write-Host "    powershell -ExecutionPolicy ByPass -c ""irm https://astral.sh/uv/install.ps1 | iex""" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Option 2 (via pip):" -ForegroundColor White
    Write-Host "    pip install uv" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Refresh environment variables
Write-Host ""
Write-Host "Refreshing environment variables..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host ""
Write-Host "=== Installation Summary ===" -ForegroundColor Cyan
Write-Host "✓ uv (including uvx) has been installed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Close and reopen PowerShell/Terminal" -ForegroundColor White
Write-Host "  2. Verify installation:" -ForegroundColor White
Write-Host "     uvx --version" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Test Eulerian MCP server:" -ForegroundColor White
Write-Host "     uvx eulerian-marketing-platform --help" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Configure Claude Desktop at:" -ForegroundColor White
Write-Host "     %APPDATA%\Claude\claude_desktop_config.json" -ForegroundColor Gray
Write-Host ""
Write-Host "✓ Setup complete!" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to exit"
