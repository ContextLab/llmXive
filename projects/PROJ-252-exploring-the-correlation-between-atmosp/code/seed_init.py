import random
import numpy as np
from pathlib import Path
from llmxive_toolkit import paths

def main():
    # Set seeds
    seed = 42
    random.seed(seed)
    np.random.seed(seed)

    # Verify seeds (simple check)
    val1 = random.random()
    val2 = np.random.random()

    # Define log path using toolkit
    log_file = paths.path("logs", "seed_initialization.log")
    
    # Ensure directory exists (paths.path creates the folder)
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"Seed initialization successful.\n")
        f.write(f"random.seed({seed}) set. Verification value: {val1}\n")
        f.write(f"np.random.seed({seed}) set. Verification value: {val2}\n")

    print("Pipeline completed successfully")

if __name__ == "__main__":
    main()
