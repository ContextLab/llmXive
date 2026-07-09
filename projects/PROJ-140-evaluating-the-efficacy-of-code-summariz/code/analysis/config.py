"""
Configuration module for the statistical analysis pipeline.

Defines sensitivity analysis ranges and other hyperparameters for the study.
"""

# Sensitivity Analysis Configuration
# These are the standard cutoffs for the threshold sweep as mandated by the study design.
SENSITIVITY_CUTOFFS = [0.01, 0.05, 0.10]

# Analysis Parameters
BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_SEED = 42

# Statistical Test Parameters
McNEMAR_CORRECTION_METHOD = 'holm-bonferroni'
ALPHA_LEVEL = 0.05

# Data Paths (relative to project root)
ANONYMIZED_LOGS_PATH = "data/interaction_logs/anonymized_logs.csv"
SUMMARY_DATA_PATH = "data/summaries/llm_sim_summaries.csv"
RULE_SUMMARY_PATH = "data/summaries/rule_summaries.csv"

# Output Paths
RESULTS_CSV_PATH = "data/analysis_results/results.csv"
SENSITIVITY_CSV_PATH = "data/analysis_results/sensitivity_analysis.csv"
OUTLIER_FLAGS_PATH = "data/analysis_results/outlier_flags.json"
BASELINE_RESULTS_PATH = "data/analysis_results/baseline_results.json"