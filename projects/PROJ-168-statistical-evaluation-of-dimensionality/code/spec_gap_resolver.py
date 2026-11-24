# Placeholder script to satisfy quickstart reference.
# The actual data‑gap resolution logic resides in `code/data_gap_resolver.py`.
# This wrapper simply invokes the resolver and exits with the appropriate code.
import sys
from data_gap_resolver import main as resolver_main

if __name__ == "__main__":
    resolver_main()