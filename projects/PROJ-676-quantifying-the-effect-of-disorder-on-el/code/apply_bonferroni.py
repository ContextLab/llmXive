"""
Stub for the Bonferroni‑correction entry point.
The heavy lifting is performed in ``aggregate_and_correct_stats``; this
script simply forwards to that implementation to keep the original CLI
contract intact.
"""
from code.aggregate_and_correct_stats import main as agg_main

def main():
    agg_main()

if __name__ == "__main__":
    main()
