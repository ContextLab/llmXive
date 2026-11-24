from __future__ import annotations

from code.data import (
    download_all,
    load_bigbench_lite,
    load_gsm8k,
)

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="LLMXive data entry point")
    parser.add_argument("--download", action="store_true", help="Download datasets")
    args = parser.parse_args(argv)

    if args.download:
        return 0 if download_all() else 1
    return 0
