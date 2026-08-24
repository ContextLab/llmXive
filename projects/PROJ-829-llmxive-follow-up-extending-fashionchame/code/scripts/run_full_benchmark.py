import sys
from pathlib import Path

# Add code directory to path
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from src.pipeline.benchmark_runner import main

if __name__ == "__main__":
    main()
