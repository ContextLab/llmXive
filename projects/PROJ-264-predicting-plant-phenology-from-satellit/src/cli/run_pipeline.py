"""
src/cli/run_pipeline.py
-----------------------

Minimal orchestration script required by the quick‑start documentation.
It forwards the ``--mode`` argument to the appropriate module entry‑point.
Only the ``train`` mode is implemented for the purpose of this task;
other modes raise ``NotImplementedError`` so that missing functionality is
obvious during execution.

The script is deliberately lightweight – it does **not** perform any heavy
data‑download work.  Its sole responsibility is to import ``src.models.train``
and invoke its ``main`` function when ``--mode train`` is supplied.
"""

import argparse
import sys
from llmxive_toolkit import get_logger

from src.models import train as train_module

log = get_logger(__name__)

def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Run pipeline steps")
    parser.add_argument("--mode", required=True, choices=["train", "ingestion", "sensitivity", "evaluate"])
    # Additional arguments are accepted but ignored for this minimal stub
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--sites")
    parser.add_argument("--cv-type")
    parser.add_argument("--alpha")
    parser.add_argument("--model")
    return parser.parse_args(argv)

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = _parse_args(argv)

    if args.mode == "train":
        log.info("Running training step")
        return train_module.main()
    elif args.mode == "ingestion":
        raise NotImplementedError("Ingestion mode not implemented in this minimal stub")
    elif args.mode == "sensitivity":
        raise NotImplementedError("Sensitivity mode not implemented in this minimal stub")
    elif args.mode == "evaluate":
        raise NotImplementedError("Evaluation mode not implemented in this minimal stub")
    else:
        raise ValueError(f"Unsupported mode: {args.mode}")

if __name__ == "__main__":
    sys.exit(main())