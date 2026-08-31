import sys
from pathlib import Path

from save_markov_artifacts import run_t017b
from config import set_seed

def main():
    """Main entry point for T017b."""
    set_seed(42)
    run_t017b()

if __name__ == '__main__':
    main()
