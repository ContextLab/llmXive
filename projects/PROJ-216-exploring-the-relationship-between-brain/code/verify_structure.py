import os
import sys
from pathlib import Path

def main():
    expected = ['data/raw', 'data/interim', 'data/processed', 'tests/unit', 'tests/integration', 'reports']
    log_path = 'data/.verify_structure.log'
    
    if not os.path.exists(log_path):
        print(f'FAIL: Verification log {log_path} does not exist', file=sys.stderr)
        sys.exit(1)

    with open(log_path, 'r') as f:
        lines = [l.strip() for l in f.readlines() if l.startswith('OK')]
        found = [l.split(' ', 1)[1] for l in lines]
    
    missing = set(expected) - set(found)
    if missing:
        print(f'FAIL: Missing directories: {missing}', file=sys.stderr)
        sys.exit(1)
    
    print('OK: All directories verified')
    sys.exit(0)

if __name__ == "__main__":
    main()
