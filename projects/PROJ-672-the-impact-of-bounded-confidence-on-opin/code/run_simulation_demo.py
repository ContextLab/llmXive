"""
Demo script to exercise the HK simulation on a tiny subset of the data.
It runs a very small number of simulations (controlled by --max-total-runs)
so that the quickstart pipeline finishes quickly on CI.

The script simply forwards the arguments to ``code.simulate_hk.main``.
"""
from code.simulate_hk import main as hk_main

if __name__ == "__main__":
    import sys
    hk_main(sys.argv[1:])