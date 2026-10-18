import random
import numpy as np
from llmxive_toolkit import paths

def main():
    """Set deterministic seeds and log the action."""
    seed = 42
    random.seed(seed)
    np.random.seed(seed)

    # Write the required log line
    log_path = paths.path("logs", "seed_initialization.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("Seeds set to 42\n")

    print("Seed initialization complete.")

if __name__ == "__main__":
    main()
