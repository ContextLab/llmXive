import argparse
import logging
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import ensure_directories, dataset_url
from downloader import fetch_tebench_streaming, stream_dataset
from graph_builder import main as build_graphs_main
from metrics import main as metrics_main
from evaluator import (
    stratified_split, load_metrics, save_metrics,
    calculate_baseline, calculate_20th_percentile_threshold, calculate_f1_max_threshold,
    predict_collapse, evaluate_performance, calculate_correlation,
    run_sensitivity_analysis_threshold, run_sensitivity_analysis_percentile,
    calculate_null_distribution, calculate_linear_reasoning_index, calculate_power_analysis,
    report_comparative_thresholds, generate_results_report, save_json_file, load_json_file
)
from config import sensitivity_thresholds, sensitivity_percentiles, null_permutations, seed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    parser.add_argument("--config", type=str, default="code/config.py", help="Path to config file")
    args = parser.parse_args()

    logger.info("Starting llmXive Research Pipeline...")
    ensure_directories()

    # 1. Download Data (Skip if already done, or force download)
    # Assuming downloader is run separately or here. 
    # For simplicity, we assume data/raw is populated.
    logger.info("Data download step assumed complete or handled by downloader module.")

    # 2. Build Graphs
    logger.info("Building graphs...")
    build_graphs_main()

    # 3. Calculate Metrics
    logger.info("Calculating metrics...")
    metrics_main()

    # 4. Load Metrics and Split
    metrics_path = Path("data/processed/metrics.csv")
    if not metrics_path.exists():
        logger.error("Metrics file not found. Did you run metrics_main?")
        return

    df = load_metrics(str(metrics_path))
    logger.info(f"Loaded {len(df)} metrics.")

    train_df, test_df = stratified_split(df, train_ratio=0.8)
    save_metrics(train_df, "data/processed/train_metrics.csv")
    save_metrics(test_df, "data/processed/test_metrics.csv")
    logger.info("Split data into train/test.")

    # 5. Evaluate
    # 5.1 Baseline
    baseline_mean = calculate_baseline(train_df)
    save_json_file({"baseline_mean_connectivity": baseline_mean}, "data/processed/baseline_report.json")
    logger.info("Calculated baseline.")

    # 5.2 Thresholds
    threshold_20 = calculate_20th_percentile_threshold(train_df)
    save_json_file({"threshold": threshold_20}, "data/processed/threshold_config.json")
    
    f1_max = calculate_f1_max_threshold(train_df)
    save_json_file({"threshold": f1_max}, "data/processed/f1_max_threshold.json")
    logger.info("Calculated thresholds.")

    # 5.3 Sensitivity Analysis
    sens_thresh = run_sensitivity_analysis_threshold(test_df, sensitivity_thresholds)
    save_json_file(sens_thresh, "data/processed/sensitivity_threshold_matrix.json")
    
    sens_perc = run_sensitivity_analysis_percentile(test_df, sensitivity_percentiles)
    save_json_file(sens_perc, "data/processed/sensitivity_percentile_matrix.json")
    logger.info("Completed sensitivity analysis.")

    # 5.4 Comparative Report
    thresh_config = load_json_file("data/processed/threshold_config.json")
    f1_config = load_json_file("data/processed/f1_max_threshold.json")
    comp_report = report_comparative_thresholds(thresh_config, f1_config, sens_thresh, sens_perc)
    save_json_file(comp_report, "data/processed/comparative_report.json")
    logger.info("Generated comparative report.")

    # 5.5 Predict and Evaluate
    test_df_pred = predict_collapse(test_df, threshold_20)
    perf_results = evaluate_performance(test_df_pred)
    save_json_file(perf_results, "data/processed/test_performance.json")
    logger.info("Evaluated performance.")

    # 5.6 Correlation
    corr_results = calculate_correlation(test_df)
    save_json_file(corr_results, "data/processed/correlation_results.json")
    
    # 5.7 Null Distribution
    null_results = calculate_null_distribution(test_df, n_permutations=null_permutations, seed=seed)
    save_json_file(null_results, "data/processed/sc_002_result.json")
    logger.info("Completed null distribution test.")

    # 5.8 Linear Reasoning
    linear_report = calculate_linear_reasoning_index("data/processed/graphs", train_df)
    save_json_file(linear_report, "data/processed/linear_reasoning_report.json")
    logger.info("Completed linear reasoning analysis.")

    # 5.9 Power Analysis
    power_results = calculate_power_analysis(train_df)
    save_json_file(power_results, "data/processed/power_analysis.json")
    logger.info("Completed power analysis.")

    # 5.10 Final Report
    final_report = generate_results_report(
        baseline_report={"baseline_mean_connectivity": baseline_mean},
        threshold_config=thresh_config,
        f1_max_config=f1_config,
        sensitivity_threshold_matrix=sens_thresh,
        sensitivity_percentile_matrix=sens_perc,
        comparative_report=comp_report,
        test_results=perf_results,
        correlation_results=corr_results,
        null_dist_results=null_results,
        linear_reasoning_report=linear_report,
        power_analysis=power_results
    )
    save_json_file(final_report, "data/processed/results_report.json")
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()