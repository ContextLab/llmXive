"""
Seed Initialization Script

This script sets the random seeds for NumPy and the built‑in random module,
writes a log file confirming the operation, and prints a success message.
It is intended to be the first step of the quick‑start pipeline to guarantee
reproducibility.
"""

import random
import numpy as np
from pathlib import Path

# Import the project's path helper. It creates parent directories as needed.
from llmxive_toolkit import paths

# Define the log file location.
log_path = paths.path("logs", "seed_initialization.log")

# Ensure the logs directory exists.
log_path.parent.mkdir(parents=True, exist_ok=True)

# Set the seeds.
np.random.seed(42)
random.seed(42)

# Write a confirmation line to the log file.
with open(log_path, "w") as f:
    f.write("Random seeds set: np.random.seed(42), random.seed(42)\\n")

# Print the required success message.
print("Pipeline completed successfully")