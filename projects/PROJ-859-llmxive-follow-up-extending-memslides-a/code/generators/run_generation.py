import sys
from pathlib import Path
from config import Config
from generators.synthetic_trace import generate_synthetic_traces

def main():
    """
    Orchestrate the generation of training data for T001.
    This script is the entry point for the task.
    """
    # Import the specific generation logic
    from generators.synthetic_trace import main as generate_training_main
    
    # Execute the training data generation
    generate_training_main()

if __name__ == "__main__":
    main()
