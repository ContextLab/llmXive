#!/usr/bin/env python3
"""
Verification script for T040: Verify Memory Chunking.

This script reads data/processed/memory_log.json and asserts that
the maximum peak RAM usage is less than 7000 MB (7 GB).

Usage:
    python scripts/verify_memory.py [memory_log_path] [output_path]

Args:
    memory_log_path: Path to memory_log.json (default: data/processed/memory_log.json)
    output_path: Path for verification report (default: data/processed/memory_verification.json)
"""
import sys
import os

# Add project root to path if running from scripts/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.verify_memory_constraint import main as verify_main

if __name__ == "__main__":
    # Pass command line arguments if provided
    exit_code = verify_main()
    sys.exit(exit_code)