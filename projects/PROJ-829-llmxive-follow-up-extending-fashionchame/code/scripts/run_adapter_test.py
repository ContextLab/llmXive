import sys
from pathlib import Path

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from adapters.text_cross_attention import main

if __name__ == '__main__':
    main()
