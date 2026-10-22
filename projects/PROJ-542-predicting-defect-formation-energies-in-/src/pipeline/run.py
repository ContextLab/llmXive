"""
src/pipeline/run.py
-------------------

Minimal end‑to‑end pipeline entry point used by the unit test
``code/tests/test_pipeline_entry.py``.  It wires together the core
steps: download, checksum generation, featurization, descriptor‑gap
checking, validation, train‑test split, model training, evaluation,
and figure generation.  Each sub‑module already implements its own CLI
entry point; this ``run`` function simply calls those entry points in
the correct order.

The ``main`` function is retained for backward compatibility with the
original quick‑start command (``python -m src.pipeline.run``), but the
test suite expects a callable ``run`` function that returns ``None`` on
success.
"""

import sys

from llmxive_toolkit import get_logger, paths

# Import the public entry points of the individual stages.
from src.data.download import main as download_main
from src.utils.checksum_all import main as checksum_all_main
from src.featurize import main as featurize_main
from src.utils.check_descriptor_gaps import main as descriptor_gaps_main
from src.data.validate import main as validate_main
from src.models.split import main as split_main
from src.models.train import main as train_main
from src.models.evaluate import main as evaluate_main

log = get_logger(__name__)

def run() -> None:
    """
    Execute the full pipeline.  Each step is run in sequence; if any
    step exits with a non‑zero status the pipeline aborts and the
    exception propagates, causing the unit test to fail.
    """
    # 1. Acquire raw data (downloads if necessary)
    download_main()

    # 2. Generate checksums for raw and processed artefacts
    checksum_all_main()

    # 3. Compute compositional features
    featurize_main(
        "data/raw/materials_defects.csv",
        "data/processed/features.csv",
    )

    # 4. Verify no descriptor gaps remain
    descriptor_gaps_main()

    # 5. Validate dataset size and statistical power
    validate_main()

    # 6. Deterministic train‑test split
    split_main(
        "data/processed/features.csv",
        "data/processed/train.csv",
        "data/processed/test.csv",
    )

    # 7. 5‑fold GroupKFold cross‑validation and model serialization
    train_main(
        "data/processed/features.csv",
        "data/processed/cv_metrics.json",
    )

    # 8. Evaluate the best model on the held‑out test set
    evaluate_main(
        "data/processed/features.csv",
        "data/processed/performance.json",
    )

    log.info("Pipeline completed successfully")
    print("Pipeline completed successfully")

def main() -> None:
    """
    Compatibility wrapper used by the quick‑start documentation.
    """
    run()

if __name__ == "__main__":
    # When executed directly, behave like the original script.
    sys.exit(main())
