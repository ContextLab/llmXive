"""
Top‑level driver that orchestrates the full analysis pipeline.
"""
import json
from pathlib import Path

# Updated import paths
from code.ingestion.download_ace import run_ingestion as run_ace_ingest
from code.ingestion.download_noaa import run_ingestion as run_noaa_ingest
from code.ingestion.generate_synthetic_data import main as generate_synthetic
from code.ingestion.align import align_data
from code.analysis.coupling_functions import compute_all_coupling_functions
from code.analysis.regression import run_regression_analysis
from code.analysis.cross_validation import run_cross_validation
from code.analysis.permutation_test import run_permutation_tests
from code.analysis.sensitivity import run_sensitivity_analysis, save_sensitivity_results
from code.analysis.integrate_results import integrate_results

from code.utils.logging import get_logger, log_duration

logger = get_logger(__name__)


@log_duration
def main() -> None:
    """
    Execute the full pipeline:
    1. Attempt real data download; on failure fall back to synthetic generation.
    2. Align data.
    3. Compute coupling functions.
    4. Run regressions.
    5. Cross‑validation.
    6. Permutation tests.
    7. Sensitivity analysis.
    8. Integrate results and write final JSON report.
    """
    # Configuration (dates for the synthetic default)
    start_date = "2000-01-01"
    end_date = "2020-01-01"

    # 1. Data ingestion (real → synthetic fallback)
    try:
        ace_df, ace_source = run_ace_ingest(
            {"start_date": start_date, "end_date": end_date, "output_path": "data/processed/ace.parquet"}
        )
        noaa_df, noaa_source = run_noaa_ingest(
            {"start_date": start_date, "end_date": end_date, "output_path": "data/processed/noaa.parquet"}
        )
        data_source = "real"
    except Exception as e:
        logger.warning(f"Real data fetch failed ({e}); generating synthetic data.")
        # Generate synthetic aligned dataset directly
        synthetic_path = Path("data/processed/synthetic_aligned.parquet")
        generate_synthetic(
            ["--output", str(synthetic_path), "--start", start_date, "--end", end_date]
        )
        data_source = "synthetic"

    # 2. Alignment (if we have real ACE/NOAA data, align them; otherwise alignment already done)
    aligned_path = Path("data/processed/aligned.parquet")
    if data_source == "real":
        # Align real data (implementation placeholder – assumes function exists)
        align_data(
            ace_path=Path("data/processed/ace.parquet"),
            noaa_path=Path("data/processed/noaa.parquet"),
            output_path=aligned_path,
        )
    else:
        aligned_path = Path("data/processed/synthetic_aligned.parquet")

    # 3. Compute coupling functions
    df = pd.read_parquet(aligned_path)
    df = compute_all_coupling_functions(df)
    df.to_parquet(aligned_path, index=False)

    # 4. Regression analysis
    regression_output_dir = Path("data/artifacts")
    regression_summary = run_regression_analysis(str(aligned_path), str(regression_output_dir))

    # 5. Cross‑validation
    cv_results = run_cross_validation(df, target="Dst", predictors=regression_summary["Baseline_Dst"]["coefficients"].keys())
    cv_path = regression_output_dir / "cv_metrics.json"
    with open(cv_path, "w", encoding="utf-8") as f:
        json.dump(cv_results, f, indent=2)

    # 6. Permutation tests
    predictors = ["O_Fe", "He_H", "C_O"]
    perm_results = run_permutation_tests(df, target="Dst", predictors=predictors)
    for pred, res in perm_results.items():
        out_path = regression_output_dir / f"permutation_{pred.lower()}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)

    # 7. Sensitivity analysis
    sensitivity_summary = run_sensitivity_analysis(perm_results)
    sensitivity_path = regression_output_dir / "fdr_results.csv"
    save_sensitivity_results(sensitivity_summary, sensitivity_path)

    # 8. Integrate results
    final_report_path = regression_output_dir / "final_report.json"
    integrate_results(
        regression_output=regression_output_dir / "regression_results.json",
        cv_output=cv_path,
        output_dir=regression_output_dir,
    )

    # Assemble final JSON report
    final_report = {
        "source_type": data_source,
        "model_summary": regression_summary,
        "cross_validation": cv_results,
        "permutation_summary": perm_results,
        "sensitivity_summary": sensitivity_summary,
    }
    with open(final_report_path, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)

    logger.info(f"Pipeline completed; final report written to {final_report_path}")


if __name__ == "__main__":
    main()
