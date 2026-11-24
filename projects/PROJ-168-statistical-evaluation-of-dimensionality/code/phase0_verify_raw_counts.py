"""
Phase 0 verification script.

This lightweight wrapper invokes the DataGapResolver to ensure that the
required raw count matrices are present and recorded in `data/manifest.json`.
It exits with status 0 when at least three datasets are available,
otherwise exits with status 1.
"""

import sys
from data_gap_resolver import DataGapResolver

def main() -> None:
    resolver = DataGapResolver()
    status, _, _ = resolver.resolve()
    if status == "enough":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
