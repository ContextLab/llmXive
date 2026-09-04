"""
Runner script for T017b.
Executes the Markov artifact saving pipeline.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from save_markov_artifacts import main
from config import set_seed

def run() -> None:
    """Run the T017b pipeline."""
    # Set seed for reproducibility (though this task is deterministic)
    set_seed(42)
    main()

if __name__ == "__main__":
    run()
