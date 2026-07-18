import sys
from pathlib import Path
from analysis.stats import main as stats_main

def main():
    """
    Wrapper to run the stats analysis (T031c) and ensure output is generated.
    This script is the entry point for the pipeline step that produces final_metrics.json.
    """
    return stats_main()

if __name__ == "__main__":
    sys.exit(main())