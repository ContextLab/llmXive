import sys
import os
from pathlib import Path
from src.pipeline.manifest import main

if __name__ == "__main__":
    # Ensure we are running from the project root context if called as a script
    # but the imports are relative to code/src
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    main()
