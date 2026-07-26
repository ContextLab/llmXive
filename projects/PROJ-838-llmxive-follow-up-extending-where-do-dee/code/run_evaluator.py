import json
import logging
from pathlib import Path
import pandas as pd
from config import ensure_directories
from evaluator import (
    load_metrics, stratified_split, calculate_baseline,
    calculate_20th_percentile_threshold, calculate_f1_max_threshold,
    predict_collapse, evaluate_performance, calculate_correlation,
    run_sensitivity_analysis, calculate_null_distribution,
    calculate_linear_reasoning_index, calculate_power_analysis,
    report_comparative_thresholds, generate_results_report,
    save_json_file
)
from config import sensitivity_thresholds, sensitivity_percentiles

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    ensure_directories()
    
    metrics_path = Path("data/processed/metrics.csv")
    if not metrics_path.exists():
        logger.error(f"Metrics file not found: {metrics_path}. Please run metrics.py first.")
        return

    logger.info("Loading metrics...")
    metrics_df = load_metrics(str(metrics_path))

    logger.info("Performing stratified split...")
    train_df, test_df = stratified_split(metrics_df, test_size=0.2, random_state=42)
    
    # Save splits
    train_df.to_csv("data/processed/train_metrics.csv", index=False)
    test_df.to_csv("data/processed/test_metrics.csv", index=False)
    logger.info("Train and test splits saved.")

    # T034: Calculate Baseline
    logger.info("Calculating baseline mean connectivity...")
    baseline_mean = calculate_baseline(train_df, success_label=0)
    baseline_report = {"baseline_mean_connectivity": baseline_mean}
    save_json_file(baseline_report, "data/processed/baseline_report.json")
    logger.info(f"Baseline report saved: {baseline_report}")

    # T030: Calculate 20th Percentile Threshold
    logger.info("Calculating 20th percentile threshold...")
    threshold_20 = calculate_20th_percentile_threshold(train_df, success_label=0)
    threshold_config = {"threshold_20_percentile": threshold_20}
    save_json_file(threshold_config, "data/processed/threshold_config.json")
    logger.info(f"Threshold config saved: {threshold_config}")

    # T031: Calculate F1 Max Threshold
    logger.info("Calculating F1 max threshold...")
    threshold_f1 = calculate_f1_max_threshold(train_df)
    f1_config = {"threshold_f1_max": threshold_f1}
    save_json_file(f1_config, "data/processed/f1_max_threshold.json")
    logger.info(f"F1 max threshold saved: {f1_config}")

    # T032: Predict Collapse
    logger.info("Predicting collapse on test set...")
    predictions = predict_collapse(test_df, threshold_20)

    # T033: Evaluate Performance
    logger.info("Evaluating performance...")
    performance_metrics = evaluate_performance(test_df, predictions)
    logger.info(f"Performance metrics: {performance_metrics}")

    # T035: Calculate Correlation
    logger.info("Calculating correlation...")
    correlation_metrics = calculate_correlation(test_df)
    logger.info(f"Correlation metrics: {correlation_metrics}")

    # T036a: Sensitivity Analysis (Thresholds)
    logger.info("Running sensitivity analysis (thresholds)...")
    sensitivity_threshold_results = run_sensitivity_analysis(test_df, sensitivity_thresholds)
    save_json_file(sensitivity_threshold_results, "data/processed/sensitivity_threshold_matrix.json")
    logger.info("Sensitivity threshold matrix saved.")

    # T036b: Sensitivity Analysis (Percentiles)
    logger.info("Running sensitivity analysis (percentiles)...")
    # Calculate thresholds from percentiles for sensitivity
    percentile_thresholds = []
    for p in sensitivity_percentiles:
        thresh = train_df[train_df['collapse'] == 0]['connectivity'].quantile(p/100.0)
        percentile_thresholds.append(thresh)
    sensitivity_percentile_results = run_sensitivity_analysis(test_df, percentile_thresholds)
    save_json_file(sensitivity_percentile_results, "data/processed/sensitivity_percentile_matrix.json")
    logger.info("Sensitivity percentile matrix saved.")

    # T037a: Null Distribution
    logger.info("Calculating null distribution...")
    null_dist_result = calculate_null_distribution(test_df, n_permutations=1000, seed=42)
    save_json_file(null_dist_result, "data/processed/sc_002_result.json")
    logger.info(f"SC-002 result: {null_dist_result['sc_002_passed']}")

    # T037b: Linear Reasoning (Placeholder for graph analysis)
    # Requires graph artifacts from T017
    graphs_dir = "data/processed/graphs"
    linear_reasoning_result = calculate_linear_reasoning_index(graphs_dir, train_df)
    save_json_file(linear_reasoning_result, "data/processed/linear_reasoning_report.json")
    logger.info(f"Linear reasoning result: {linear_reasoning_result}")

    # T046: Comparative Report
    logger.info("Generating comparative thresholds report...")
    comparative_report = report_comparative_thresholds(threshold_20, threshold_f1, sensitivity_threshold_results)
    save_json_file(comparative_report, "data/processed/comparative_report.json")
    logger.info("Comparative report saved.")

    # T044: Power Analysis
    logger.info("Calculating power analysis...")
    power_result = calculate_power_analysis(train_df)
    save_json_file(power_result, "data/processed/power_analysis.json")
    logger.info(f"Power analysis result: {power_result}")

    # T045: Generate Final Results Report
    logger.info("Generating final results report...")
    final_report = generate_results_report(
        baseline_report,
        threshold_config,
        f1_config,
        predictions,
        performance_metrics,
        correlation_metrics,
        null_dist_result,
        linear_reasoning_result,
        power_result,
        comparative_report
    )
    save_json_file(final_report, "data/processed/results_report.json")
    logger.info("Final results report saved.")

    logger.info("Evaluator pipeline completed successfully.")

if __name__ == "__main__":
    main()