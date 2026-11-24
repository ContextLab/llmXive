"""
CLI Entry Point for the Plant Metabolite Prediction Pipeline.
Extended to accept ``--step`` arguments matching the quick‑start guide.
"""

import argparse
import logging
import pandas as pd  # Added pandas import for DataFrame handling

# Import pipeline stages
from code.config import load_config, get_species_list
from code.config_env import ensure_directories
from code.data.align import align_data, save_aligned_matrix
from code.data.download import download_genomes, download_metabolites
from code.data.preprocess import (
    harmonize_metabolites,
    map_bgc_to_metabolite,
    run_antiSMASH_wrapper,
)
from code.modeling.eval import (
    calculate_variation,
    evaluate_models,
    report_primary_results,
    run_sensitivity_sweep,
    save_metrics,
)
from code.modeling.phylo import construct_covariance_matrix, load_phylogeny, train_pgls
from code.modeling.train import apply_pca, train_models_loo
from code.utils.logging import get_logger, setup_logging
from code.utils.report import generate_report


def _run_download_and_align(config) -> None:
    """
    Execute the data‑download + alignment sub‑pipeline.
    Mirrors the behaviour of the historic ``code/data/download.py`` script
    but is now reachable via the ``--step download_and_align`` CLI flag.
    """
    logger = get_logger(__name__)
    logger.info("Running download_and_align step")

    # Load species definitions from the configuration
    species = get_species_list()
    if not species:
        logger.warning("No species configured – aborting download step.")
        return

    # Download genomes and metabolites
    genomes_df = download_genomes([s.dict() for s in species])
    metabolites_df = download_metabolites([s.dict() for s in species])

    # Prepare a minimal genome DataFrame (BGC counts will be filled later)
    genome_records = [
        {"species": row["species"], "total_bgc_count": 0}
        for _, row in genomes_df.iterrows()
    ]
    genome_df = pd.DataFrame(genome_records)

    # Load metabolite tables into a single DataFrame
    metabolite_frames = []
    for _, row in metabolites_df.iterrows():
        try:
            df = pd.read_csv(row["metabolite_path"], sep="\t")
            metabolite_frames.append(df)
        except Exception as e:
            logger.error(f"Failed to read metabolite file {row['metabolite_path']}: {e}")

    metabolite_df = pd.concat(metabolite_frames, ignore_index=True) if metabolite_frames else pd.DataFrame()

    # Align and persist
    aligned_df, _ = align_data(genome_df, metabolite_df, species_list=None)

    # Use the default output location defined in ``save_aligned_matrix``.
    # This avoids reliance on a possibly‑missing ``output_path`` attribute in the config.
    save_aligned_matrix(aligned_df)
    logger.info("download_and_align step completed")


def _run_train_and_evaluate(config) -> None:
    """
    Execute the modelling sub‑pipeline (placeholder implementation).
    The full modelling logic is outside the scope of T006; this function
    simply wires together the existing modelling utilities so that the
    quick‑start command succeeds.
    """
    logger = get_logger(__name__)
    logger.info("Running train_and_evaluate step")

    # Load the aligned matrix produced by the previous step
    aligned_path = config.output_path / "aligned_matrix.csv"
    if not aligned_path.exists():
        logger.error(f"Aligned matrix not found at {aligned_path}")
        return

    aligned_df = pd.read_csv(aligned_path)

    # Load phylogeny and construct covariance matrix (required by PGLS)
    tree = load_phylogeny(config.phylogeny_path)
    cov_matrix = construct_covariance_matrix(tree)

    # Apply PCA (dummy – real implementation lives in modeling.train)
    pca_features = apply_pca(aligned_df, n_components=10)

    # Train primary PGLS model
    pgls_model = train_pgls(pca_features, aligned_df["target"], cov_matrix)

    # Train secondary models (RF, EN, etc.) via LOO CV
    secondary_models = train_models_loo(pca_features, aligned_df["target"])

    # Evaluate models and persist metrics
    metrics = evaluate_models(pgls_model, secondary_models, aligned_df)
    save_metrics(metrics)

    # Sensitivity analysis
    sensitivity_results = run_sensitivity_sweep([0.1, 0.3, 0.5, 0.7])
    variation = calculate_variation(sensitivity_results)

    # Generate final report
    report_md = generate_report(
        metrics=metrics,
        feature_importance=getattr(pgls_model, "feature_importances_", {}),
        sensitivity_results=sensitivity_results,
        variation=variation,
    )
    report_path = config.output_path / "final_report.md"
    with open(report_path, "w") as f:
        f.write(report_md)

    logger.info(f"Training and evaluation complete. Report written to {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Plant Metabolite Prediction Pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force re‑downloading data",
    )
    parser.add_argument(
        "--step",
        type=str,
        choices=["download_and_align", "train_and_evaluate"],
        help="Execute a single pipeline step (used by quickstart)",
    )
    args = parser.parse_args()

    # 1. Setup logging
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting Plant Metabolite Prediction Pipeline")

    # Load configuration
    config = load_config(args.config)
    ensure_directories(config.data_root)

    # Dispatch based on the optional ``--step`` argument
    if args.step == "download_and_align":
        _run_download_and_align(config)
    elif args.step == "train_and_evaluate":
        _run_train_and_evaluate(config)
    else:
        # Full pipeline – retained for backward compatibility
        logger.info("Running full pipeline (download → preprocess → align → model)")

        # Data download
        genome_df = download_genomes(get_species_list(), force=args.force_download)
        metabolite_df = download_metabolites(get_species_list(), force=args.force_download)

        # Preprocessing (antiSMASH placeholder + harmonisation)
        bgc_df = run_antiSMASH_wrapper(genome_df, confidence=0.5)
        met_df = harmonize_metabolites(metabolite_df)
        mapped_df = map_bgc_to_metabolite(bgc_df, met_df)

        # Alignment
        aligned_df, _ = align_data(mapped_df)
        save_aligned_matrix(aligned_df)  # Uses default location

        # Modelling (same as above)
        _run_train_and_evaluate(config)

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    main()
