import hashlib
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

# Ensure code directory is in path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import RANDOM_SEED, MAX_TRACES
import random

def stream_alfworld_traces(split: str = "train", streaming: bool = True) -> Iterator[Dict[str, Any]]:
    """
    Stream ALFWorld traces from the real dataset.
    Uses datasets library if available, otherwise falls back to local files.
    """
    try:
        from datasets import load_dataset
        # Try to load real dataset
        ds = load_dataset("alfworld/alfworld", split=split, streaming=streaming)
        for item in ds:
            yield item
    except Exception as e:
        # If datasets not available or real fetch fails, check local fallback
        raw_dir = Path("data/raw")
        if raw_dir.exists():
            for file in raw_dir.glob("*.json"):
                with open(file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            yield item
                    else:
                        yield data
        else:
            # No real source available - FAIL LOUDLY
            raise RuntimeError(
                f"Failed to load ALFWorld traces from remote or local sources. "
                f"Error: {e}. Please ensure 'data/raw/' contains valid trace files "
                f"or 'datasets' package is installed with network access."
            )

def load_traces_as_list(split: str = "train", max_traces: int = MAX_TRACES) -> List[Dict[str, Any]]:
    """
    Load traces as a list, optionally limiting to max_traces.
    Uses streaming to handle large datasets.
    """
    traces = []
    random.seed(RANDOM_SEED)
    
    for trace in stream_alfworld_traces(split=split, streaming=True):
        if len(traces) >= max_traces:
            break
        traces.append(trace)
    
    if not traces:
        raise RuntimeError("No traces loaded from any source.")
    
    return traces

def main():
    """CLI entry point for data loader."""
    import argparse
    parser = argparse.ArgumentParser(description="Data Loader")
    parser.add_argument("--sample", type=int, default=10, help="Number of traces to sample")
    args = parser.parse_args()
    
    try:
        traces = load_traces_as_list(max_traces=args.sample)
        print(f"Loaded {len(traces)} traces.")
        for t in traces[:3]:
            print(json.dumps(t, indent=2))
    except Exception as e:
        print(f"Error loading traces: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()