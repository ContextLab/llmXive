"""
Script to execute the Speed Metrics Analysis (T036c).
"""
import sys
import logging
from pathlib import Path

# Add the project root to the path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.speed_metrics import main

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    sys.exit(main())
