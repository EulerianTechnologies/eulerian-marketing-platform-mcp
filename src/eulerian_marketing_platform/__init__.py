"""Eulerian Marketing Platform MCP Server.

This package provides a Model Context Protocol (MCP) server that enables
AI assistants to interact with Eulerian Marketing Platform APIs.
"""

__version__ = "0.2.0"
__author__ = "Eulerian Technologies"
__all__ = []

# Import main only when explicitly requested
def get_main():
    """Lazy import of main function to avoid side effects."""
    from .server import main
    return main
