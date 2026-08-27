import sys
from pathlib import Path

from save_markov_artifacts import run_t017b
from config import set_seed

def main():
    """
    Entry point for running T017b script.
    """
    # Ensure we are in the project root or handle path correctly
    # The artifact is expected to be run from the project root
    run_t017b()

if __name__ == "__main__":
    main()
