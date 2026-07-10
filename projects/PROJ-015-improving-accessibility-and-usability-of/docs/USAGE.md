# Usage Guide

## Introduction
This guide details how to use the PROJ-015 pipeline for conducting usability studies and analyzing results.

## Step 1: Data Collection (Simulator)
The simulator is the primary tool for collecting user interaction data.

1. **Launch the App**:
 Run `streamlit run code/simulator/app.py`.
2. **Configure Session**:
 - Select the interface variant (Traditional or Explainable).
 - The system automatically assigns sequences using Latin Square counterbalancing.
3. **Execute Tasks**:
 - Participants complete tasks while the system logs `completion_time` and `error_count`.
 - For Explainable interfaces, `explanation_engagement_time` is recorded.
4. **SUS Questionnaire**:
 - After the task, the System Usability Scale (SUS) questionnaire is presented.
 - Missing responses are handled per EC-001 (impute if ≤1 missing, reject if >1).
5. **Save Data**:
 - Raw data is saved to `data/raw/session_{id}.json` with a checksum.

## Step 2: Data Analysis
Once data is collected, run the analysis pipeline.

1. **Run Analysis Script**:
 ```bash
 python code/analysis/run_analysis.py
 ```
 This script performs:
 - Data cleaning and filtering (removes incomplete sessions).
 - Normality testing (Shapiro-Wilk).
 - Repeated Measures ANOVA.
 - Holm-Bonferroni correction.
 - Effect size calculation.
2. **Outputs**:
 - `data/processed/metrics_summary.csv`: Statistical results.
 - `data/processed/descriptive_stats.csv`: Mean and std dev for all metrics.
 - `figures/*.png`: Box plots with error bars.
 - `data/processed/report_summary.txt`: Text summary of findings.

## Step 3: Reproducible Reporting
For a full interactive report, use the Jupyter notebook.

1. **Open Notebook**:
 ```bash
 jupyter notebook code/analysis.ipynb
 ```
2. **Execute Cells**:
 The notebook loads raw data, cleans it, runs statistics, and generates figures automatically.

## Troubleshooting
- **Missing Dependencies**: Ensure `requirements.txt` is installed.
- **Data Path Errors**: Verify `data/raw` contains valid JSON files.
- **Logging Issues**: Check `code/utils/logger.py` configuration.
