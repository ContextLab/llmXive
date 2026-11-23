"""
Configuration for linting and formatting tools.
Provides command builders for ruff and black.
"""
import sys
from pathlib import Path

def get_ruff_command(action: str = "check", fix: bool = False) -> list:
    """
    Construct the ruff command based on the desired action.
    
    Args:
        action: Either 'check' or 'format'
        fix: Whether to apply fixes automatically
    
    Returns:
        List of command arguments
    """
    cmd = [sys.executable, "-m", "ruff"]
    
    if action == "check":
        cmd.append("check")
        if fix:
            cmd.append("--fix")
    elif action == "format":
        cmd.append("format")
        if fix:
            cmd.append("--check")
    
    # Target the code directory
    cmd.append("code/")
    
    return cmd

def get_black_command(check: bool = False) -> list:
    """
    Construct the black command.
    
    Args:
        check: If True, only check formatting without modifying files
    
    Returns:
        List of command arguments
    """
    cmd = [sys.executable, "-m", "black"]
    
    if check:
        cmd.append("--check")
    
    cmd.append("code/")
    
    return cmd
