"""QC-only preprocessing pipeline for T014b.

This script orchestrates the tSNR evidence recording and subject filtering
required by task T014b. It reads preprocessed NIfTI files from data/raw,
calculates tSNR statistics, and writes the required CSV outputs to data/analysis.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from code.data.preprocess import record_tsnr_evidence_and_filter
from code.logging_config import get_logger

logger = get_logger(__name__)

def main(argv: list[str] | None = None) -> None:
    """Entry point for QC-only preprocessing.

    This runs the tSNR evidence recorder and subject filter on preprocessed data.
    It expects NIfTI files in the input directory and writes:
      - data/analysis/qc_summary.csv
      - data/analysis/subjects_included.csv
    """
    parser = argparse.ArgumentParser(
        description="Run QC-only preprocessing: tSNR calculation and subject filtering."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw"),
        help="Directory containing preprocessed NIfTI files (default: data/raw).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed"),
        help="Directory where processed outputs will be saved (default: data/processed).",
    )
    parser.add_argument(
        "--analysis-output",
        type=Path,
        default=Path("data/analysis"),
        help="Directory where QC CSV files will be saved (default: data/analysis).",
    )
    parser.add_argument(
        "--tsnr-threshold",
        type=float,
        default=50.0,
        help="Voxel-wise tSNR threshold (default: 50).",
    )
    parser.add_argument(
        "--inclusion-percent",
        type=float,
        default=90.0,
        help="Minimum percent of good voxels for inclusion (default: 90).",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    logger.log("qc_pipeline_start", input_dir=str(args.input), output_dir=str(args.output))

    try:
        # Run the tSNR evidence recorder and subject filter
        record_tsnr_evidence_and_filter(
            nifti_dir=args.input,
            output_dir=args.analysis_output,
            tsnr_threshold=args.tsnr_threshold,
            inclusion_percent=args.inclusion_percent,
        )
        logger.log("qc_pipeline_success")
    except Exception as exc:
        logger.log("qc_pipeline_failed", error=str(exc))
        raise

if __name__ == "__main__":
    main()
