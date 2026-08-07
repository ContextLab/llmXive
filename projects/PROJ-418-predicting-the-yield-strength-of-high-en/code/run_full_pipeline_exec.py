#!/usr/bin/env python
"""
Execute the full end‑to‑end pipeline.

This script is a thin wrapper around the project's high‑level ``run_full_pipeline``
entry point.  It invokes the pipeline, which (through the existing code base)
performs the following steps:

1. Download and validate the raw HEA dataset.
2. Pre‑process the data, normalise units and calculate compositional descriptors.
3. Train the Linear Regression and Random Forest models.
4. Evaluate the models (metrics, VIF, permutation importance, bootstrap CI, etc.).
5. Generate the final report (``output/report.md``) and reproducibility manifest
   (``output/manifest.json``).
6. Write auxiliary artefacts such as ``output/metrics.json``,
   ``output/pipeline_runtime.json``, ``output/data_status.json`` and others.

All artefacts are written to the locations defined in the task specifications,
so after successful execution the repository contains the required output files.
"""

import sys
import os

# Ensure deterministic behaviour for the Random Forest trainer (see T018)
os.environ["OMP_NUM_THREADS"] = "1"

# The high‑level pipeline entry point lives in ``code/run_full_pipeline.py``.
# According to the project's API surface it exposes a ``main`` function.
from run_full_pipeline import main as run_full_pipeline_main

def main() -> None:
    """
    Run the full pipeline and exit with the appropriate status code.

    The imported ``run_full_pipeline_main`` may call ``sys.exit`` internally.
    To keep this wrapper robust we simply invoke it and, if it returns,
    propagate any integer return value as the process exit code.
    """
    try:
        ret = run_full_pipeline_main()
    except SystemExit as e:
        # The pipeline chose to exit explicitly – forward that code.
        raise
    else:
        # If the pipeline returns a value, treat ``0`` as success.
        if isinstance(ret, int) and ret != 0:
            sys.exit(ret)

if __name__ == "__main__":
    main()
