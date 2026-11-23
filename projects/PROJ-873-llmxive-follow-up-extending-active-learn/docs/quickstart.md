# llmXive Quickstart Guide

This guide provides the commands to run the llmXive research pipeline end-to-end.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## Running the Pipeline

### 1. Data Preparation

Prepare the BEIR datasets and inject synthetic redundancy:

```bash
python code/data_loader.py prepare
```

This command:
- Downloads BEIR datasets (nfcorpus, scifact, trec-covid)
- Injects synthetic redundancy (T012)
- Validates the injection (T043)
- Writes `data/processed/injected_datasets.json` and `data/processed/validation_status.json`

### 2. Baseline Execution

Run the baseline active ranker on the full redundant list:

```bash
python code/run_pipeline.py --variant baseline --budgets 100 --seeds 1
```

This command:
- Processes the full redundant list (T014-Baseline)
- Generates `data/processed/comparison_log_full.json`
- Calculates flagged pairs (T013)
- Writes `data/results/flagged_pairs_count.json`

### 3. Sample Size Calculation (T013b)

Calculate the sample size for LLM consensus validation:

```bash
python code/scripts/run_t013b.py
```

This command:
- Reads `data/results/flagged_pairs_count.json`
- Calculates sample size (max of 10 or 5% of flagged count)
- Writes `data/results/sample_config.json`

### 4. Unique Subset Baseline

Run the baseline on the unique subset:

```bash
python code/run_baseline_unique.py
```

This command:
- Generates unique subset (T014-UniqueBaseline)
- Runs baseline on unique subset
- Writes `data/results/us1_baseline_metrics.json`

### 5. Clustering-Aided Variant

Run the clustering-aided variant:

```bash
python code/run_pipeline.py --variant clustering_aided --budgets 100 --seeds 1
```

This command:
- Applies MinHash-LSH clustering (T020)
- Filters candidates (T021)
- Writes `data/processed/clusters.json`

### 6. Statistical Analysis

Run statistical significance tests:

```bash
python code/confirm_statistical_robustness.py
```

This command:
- Performs Wilcoxon signed-rank tests (T028, T029)
- Applies Bonferroni correction (T030)
- Generates final report (T031)

## Verification

Validate the complete pipeline:

```bash
python code/quickstart_validator.py
```

This command checks that all required artifacts are present and valid.

## Output Artifacts

The pipeline produces the following key artifacts:

- `data/processed/injected_datasets.json` - Synthetic redundancy data
- `data/processed/comparison_log_full.json` - Full pairwise comparison log
- `data/results/flagged_pairs_count.json` - Count of wasted calls
- `data/results/sample_config.json` - Sample size configuration (T013b)
- `data/results/us1_baseline_metrics.json` - Baseline NDCG metrics
- `data/results/us1_efficiency_ratio.json` - Corrected wasted call ratio
- `data/results/statistical_report.md` - Final statistical analysis
