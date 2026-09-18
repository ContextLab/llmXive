"""
CLI Entry Point for the Plant Metabolite Prediction Pipeline.
Orchestrates the full workflow from data download to report generation.
"""
import logging
from pathlib import Path
from typing import Optional
import argparse
import sys

# Import pipeline stages
from code.config import get_config, load_config
from code.config_env import load_environment, ensure_directories
from code.utils.logging import setup_logging, get_logger
from code.data.download import download_genomes, download_metabolites
from code.data.preprocess import run_antiSMASH_wrapper, harmonize_metabolites, map_bgc_to_metabolite
from code.data.align import align_data, save_aligned_matrix
from code.modeling.phylo import load_phylogeny, construct_covariance_matrix, train_pgls
from code.modeling.train import apply_pca, train_models_loo, create_stratified_split
from code.modeling.eval import run_sensitivity_sweep, evaluate_models, calculate_variation, report_primary_results
from code.utils.report import generate_report

def main():
    parser = argparse.ArgumentParser(description="Run Plant Metabolite Prediction Pipeline")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--force-download", action="store_true", help="Force re-downloading data")
    args = parser.parse_args()

    # 1. Setup
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting Plant Metabolite Prediction Pipeline")

    # Load Config
    config = load_config(args.config)
    ensure_directories(config.data_root)

    # 2. Data Download
    logger.info("Step 1: Downloading Data")
    genome_paths = download_genomes(config.species_list, force=args.force_download)
    metabo_paths = download_metabolites(config.species_list, force=args.force_download)

    # 3. Preprocessing
    logger.info("Step 2: Preprocessing")
    # Run antiSMASH (mocked or real wrapper call)
    bgc_data = run_antiSMASH_wrapper(genome_paths, config.confidence_threshold)
    # Harmonize metabolites
    metabo_df = harmonize_metabolites(metabo_paths)
    # Map BGC to Metabolite
    mapped_data = map_bgc_to_metabolite(bgc_data, metabo_df)

    # 4. Alignment
    logger.info("Step 3: Aligning Data")
    aligned_df = align_data(mapped_data)
    save_aligned_matrix(aligned_df, config.output_path / "aligned_matrix.csv")

    # 5. Modeling
    logger.info("Step 4: Training Models")
    # Load Phylogeny
    tree = load_phylogeny(config.phylogeny_path)
    cov_matrix = construct_covariance_matrix(tree)
    
    # PCA
    pca_features = apply_pca(aligned_df, n_components=10)
    
    # Train PGLS (Primary)
    pgls_model = train_pgls(pca_features, aligned_df['target'], cov_matrix)
    
    # Train RF/EN (Secondary)
    secondary_models = train_models_loo(pca_features, aligned_df['target'])

    # 6. Evaluation & Sensitivity
    logger.info("Step 5: Evaluation and Sensitivity Analysis")
    metrics = evaluate_models(pgls_model, secondary_models, aligned_df)
    sensitivity_results = run_sensitivity_sweep([0.1, 0.3, 0.5, 0.7])
    variation = calculate_variation(sensitivity_results)
    
    # Report Primary Results
    primary_report = report_primary_results(pgls_model, metrics)

    # 7. Report Generation
    logger.info("Step 6: Generating Report")
    full_report = generate_report(
        metrics=metrics,
        feature_importance=pgls_model.feature_importances_,
        sensitivity_results=sensitivity_results,
        variation=variation
    )
    
    report_path = config.output_path / "final_report.md"
    with open(report_path, 'w') as f:
        f.write(full_report)
    
    logger.info(f"Pipeline complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()