"""
Setup directories (T004).
"""
import os
import sys
from pathlib import Path

def setup_directories():
    dirs = [
        'data/raw', 'data/processed', 'data/interim', 'data/results',
        'code', 'tests', 'state', 'figures'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def main():
    setup_directories()

if __name__ == "__main__":
    main()
