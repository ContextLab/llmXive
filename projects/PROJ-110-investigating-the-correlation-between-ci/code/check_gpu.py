"""Check that no GPU devices are available.

This script is intended to be run in CI to enforce CPU‑only execution.
It exits with a non‑zero status if a GPU is detected via ``torch.cuda.is_available()``.
"""
import sys
import logging

try:
    import torch
except ImportError as e:
    logging.error("torch is not installed. Ensure it is added to requirements.txt.")
    sys.exit(1)

if torch.cuda.is_available():
    logging.error("GPU devices are available; this project requires CPU‑only execution.")
    sys.exit(1)

logging.info("No GPU devices detected; proceeding with CPU‑only execution.")
sys.exit(0)