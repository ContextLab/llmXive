# PROJ-052: Leveraging LLMs for Automated Test Case Generation

## Project Overview
This project investigates the efficacy of Large Language Models (LLMs) in generating automated test cases from natural language requirements, specifically using the Defects4J dataset. The pipeline involves data ingestion, test generation, execution, coverage measurement, and statistical analysis.

## Prerequisites
- Python 3.9+
- Java JDK 11+ (for test compilation and execution)
- pip dependencies listed in `requirements.txt`
- CPU-only environment (GPU not required/used)

## Quickstart Instructions

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Run the Pipeline**:
 ```bash
 python code/main.py
 ```

3. **View Results**:
 - Coverage metrics: `data/coverage_metrics.csv`
 - Statistical analysis: `data/analysis_results.json`
 - Final report: `data/final_report.md`

## Methodological Constraints

### Strict Pairing
This study employs a "Strict Pairing" methodology to ensure valid statistical comparison. Only samples where a known, failing manual test baseline exists for the buggy version are included in the statistical analysis subset. Samples lacking this specific manual baseline are excluded and logged in `data/exclusion_log.json`.

**Impact on Exclusion Rate**:
- The exclusion rate is a critical methodological constraint. A high exclusion rate (e.g., >50%) indicates that the dataset's availability of paired samples is limited.
- The final report (`data/final_report.md`) will explicitly state the exclusion rate and include a warning if the sample size (N) falls below 30, labeling the results as "exploratory".
- Samples with status `timeout` or `[deferred]` are also excluded from the statistical subset to prevent bias from incomplete executions.

## Architecture
- `code/`: Source code for data loading, LLM generation, test execution, and analysis.
- `data/`: Output artifacts (datasets, coverage metrics, logs).
- `specs/`: Feature specifications.
- `tests/`: Unit and integration tests.
- `contracts/`: JSON/YAML schemas for data validation.
