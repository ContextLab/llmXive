#!/usr/bin/env python3
"""
T082 - Verify config.yaml is under 2KB per FR-009

This script verifies that the config.yaml file size is under 2KB (2048 bytes)
as required by FR-009, and documents the final size in test_report.md.
"""

import os
import sys
from pathlib import Path

# Project root is the parent of code/
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
TEST_REPORT_PATH = PROJECT_ROOT / "tests" / "test_report.md"

MAX_CONFIG_SIZE = 2048  # 2KB in bytes


def get_file_size(path: Path) -> int:
    """Get file size in bytes."""
    if path.exists():
        return os.path.getsize(path)
    return 0


def update_test_report(config_size: int, max_size: int, passed: bool) -> None:
    """Update test_report.md with config size verification results."""
    # Create tests directory if it doesn't exist
    TEST_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    report_content = f"""# Test Report

## T082 - Config Size Verification

**Status**: {'PASS' if passed else 'FAIL'}
**Config File**: {CONFIG_PATH}
**Config Size**: {config_size} bytes ({config_size / 1024:.2f} KB)
**Maximum Allowed**: {max_size} bytes ({max_size / 1024:.2f} KB)
**Compliance**: {'✓' if passed else '✗'}

## FR-009 Compliance

The config.yaml file must remain under 2KB to ensure:
- Readability and maintainability
- Easy version control diffs
- Simple configuration management

## Verification Details

- Verification Date: 2026-01-15
- Verification Method: os.path.getsize()
- Config Location: code/config.yaml
- Test Report Location: code/tests/test_report.md

"""

    with open(TEST_REPORT_PATH, 'w') as f:
        f.write(report_content)


def main() -> int:
    """Main entry point for config size verification."""
    print(f"Verifying config.yaml size...")
    print(f"Config path: {CONFIG_PATH}")

    if not CONFIG_PATH.exists():
        print(f"ERROR: Config file not found at {CONFIG_PATH}")
        update_test_report(0, MAX_CONFIG_SIZE, False)
        return 1

    config_size = get_file_size(CONFIG_PATH)
    passed = config_size <= MAX_CONFIG_SIZE

    print(f"Config size: {config_size} bytes ({config_size / 1024:.2f} KB)")
    print(f"Max allowed: {MAX_CONFIG_SIZE} bytes ({MAX_CONFIG_SIZE / 1024:.2f} KB)")
    print(f"Result: {'PASS' if passed else 'FAIL'}")

    # Update test report
    update_test_report(config_size, MAX_CONFIG_SIZE, passed)
    print(f"Test report updated: {TEST_REPORT_PATH}")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
