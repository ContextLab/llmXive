"""
Utility functions for R project initialization and management.
"""
import subprocess
import sys
import os
import json
from typing import List, Optional

def check_r_version(min_version: float = 4.3) -> bool:
    """
    Check if installed R version meets the minimum requirement.
    
    Args:
        min_version: Minimum required R version (default 4.3)
        
    Returns:
        True if version is sufficient, False otherwise
        
    Raises:
        RuntimeError: If R is not found
    """
    try:
        result = subprocess.run(
            ["R", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse version from output (e.g., "R version 4.3.1 (2023-06-16)")
        lines = result.stdout.split('\n')
        if lines:
            version_line = lines[0]
            parts = version_line.split()
            if len(parts) >= 3:
                version_str = parts[2]
                major, minor = map(float, version_str.split('.')[:2])
                current_version = major + minor / 10
                return current_version >= min_version
    except subprocess.CalledProcessError:
        raise RuntimeError("R is not installed or not in PATH.")
    except Exception as e:
        raise RuntimeError(f"Error checking R version: {e}")
    
    return False

def verify_packages(required_packages: List[str]) -> List[str]:
    """
    Check which required packages are missing in the R environment.
    
    Args:
        required_packages: List of package names to check
        
    Returns:
        List of missing package names
    """
    missing = []
    # This would typically run an R command to check installed packages
    # For now, we return an empty list as a placeholder
    # In a real implementation, we'd run:
    # result = subprocess.run(
    #     ["Rscript", "-e", f'installed.packages()[,1]'],
    #     capture_output=True, text=True
    # )
    # Then parse the output and compare with required_packages
    return missing

def initialize_renv():
    """
    Initialize renv and install required packages.
    
    This is a wrapper that calls the R initialization script.
    """
    r_script_path = os.path.join(os.path.dirname(__file__), "00_init_renv.R")
    if not os.path.exists(r_script_path):
        raise FileNotFoundError(f"R initialization script not found: {r_script_path}")
    
    result = subprocess.run(
        ["Rscript", r_script_path],
        check=True,
        capture_output=False
    )
    
    return result.returncode == 0
