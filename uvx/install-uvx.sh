#!/bin/bash
# Quick UVX Installation Script for Eulerian MCP Server
# This script ensures uvx is installed and ready to use

set -e

echo "=== Eulerian Marketing Platform MCP Server - UVX Setup ==="
echo ""

# Color codes for pretty output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if uvx is already installed
echo "Checking for uvx installation..."
if command -v uvx &> /dev/null; then
    UVX_VERSION=$(uvx --version 2>&1 | head -n1)
    print_success "uvx is already installed: $UVX_VERSION"
    exit 0
fi

print_warning "uvx is not installed. Installing now..."
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo "Detected OS: $OS"
echo ""

# Install based on OS
if [[ "$OS" == "linux" ]] || [[ "$OS" == "macos" ]]; then
    echo "Installing uv (which includes uvx) via official installer..."
    echo "Running: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        print_success "Installation completed!"
    else
        print_error "Installation failed!"
        echo ""
        echo "Please install manually:"
        echo "  Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "  or with pip: pip install uv"
        exit 1
    fi
    
    # Add to PATH if needed
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        print_warning "Adding ~/.local/bin to PATH..."
        
        # Detect shell
        if [ -n "$BASH_VERSION" ]; then
            SHELL_RC="$HOME/.bashrc"
        elif [ -n "$ZSH_VERSION" ]; then
            SHELL_RC="$HOME/.zshrc"
        else
            SHELL_RC="$HOME/.profile"
        fi
        
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
        print_success "Added to $SHELL_RC"
        print_warning "Please restart your terminal or run: source $SHELL_RC"
    fi
    
elif [[ "$OS" == "windows" ]]; then
    print_error "Automatic installation on Windows is not supported by this script."
    echo ""
    echo "Please install manually using PowerShell (run as Administrator):"
    echo "  powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\""
    echo ""
    echo "Or install with pip:"
    echo "  pip install uv"
    exit 1
else
    print_error "Unsupported operating system: $OSTYPE"
    echo ""
    echo "Please install manually:"
    echo "  pip install uv"
    exit 1
fi

echo ""
echo "=== Installation Summary ==="
print_success "uv (including uvx) has been installed!"
echo ""
echo "Next steps:"
echo "  1. Restart your terminal (or run: source ~/.bashrc)"
echo "  2. Verify installation: uvx --version"
echo "  3. Test Eulerian MCP server:"
echo "     uvx eulerian-marketing-platform --help"
echo ""
echo "  4. Configure Claude Desktop or Gemini CLI with:"
echo "     {\"command\": \"uvx\", \"args\": [\"eulerian-marketing-platform\"]}"
echo ""
print_success "Setup complete!"
