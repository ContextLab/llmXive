#!/usr/bin/env python3
"""
Script to run the motif aggregation task (T026).
Executes code/motifs.py aggregate_motif_profiles() function.
"""
import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motifs import main

if __name__ == "__main__":
    sys.exit(main())
