# Quickstart Guide for llmXive Follow-up Project

This guide provides the commands to run the full pipeline and verify the proxy validation chain.

## Prerequisites

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`

## 1. Data Preparation

Fetch BEIR datasets and prepare injected redundancy datasets.

```bash
python code/data_loader.py prepare
```

This command:
- Downloads `nfcorpus`, `scifact`, and `trec-covid` from BEIR.
- Generates synthetic redundancy clusters.
- Writes `data/processed/injected_datasets.json`.

## 2. Run Pipeline (Baseline & Clustering-Aided)

Execute the full active learning pipeline with resource limits.

```bash
# Baseline variant (unique subset only)
python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 5

# Clustering-aided variant (MinHash-LSH pre-filtering)
python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 5
```

**Note**: The `--variant` argument must be either `baseline` or `clustering_aided`.
The `--budgets` argument accepts multiple integer values.
The `--seeds` argument specifies the number of random seeds for statistical robustness.

## 3. Verify Proxy Validation Chain (T069)

Execute the dry-run of the proxy validation chain (T013 -> T013e -> T013f -> T013d)
to confirm artifact integrity and data flow.

```bash
python code/verify_proxy_chain.py --data-dir data --results-dir data/results
```

This command:
- Reads `consensus_sample.json` (from T013c).
- Runs T013e (Consensus Validation) -> writes `consensus_ground_truth.json`.
- Runs T013f (Correction Factor) -> writes `correction_factor.json`.
- Runs T013d (Final Ratio) -> writes `us1_efficiency_ratio.json`.
- Outputs a summary to `data/results/t069_chain_verification.json`.

## 4. Statistical Analysis

Run statistical tests on the results.

```bash
python code/confirm_statistical_robustness.py
python code/generate_statistical_report.py
```

## 5. Validation & Auditing

Validate the Constitution compliance and data integrity.

```bash
python code/audit/validate_constitution.py
python code/quickstart_validator.py
```

## Troubleshooting

- **Missing Artifacts**: Ensure `code/data_loader.py prepare` has been run successfully before running the pipeline.
- **Resource Limits**: If the pipeline terminates early, check `data/processed/resource_log.json` for memory or timeout violations.
- **Data Flow Errors**: If `DataFlowViolationError` is raised, verify that all prerequisite artifacts (e.g., `injected_datasets.json`, `clusters.json`) exist in `data/processed/`.
