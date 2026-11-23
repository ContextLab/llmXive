# Quickstart Guide: llmXive Follow-up - Active Learners as Efficient PRP Rerankers

## Prerequisites

- Python 3.11+
- Required packages (install via `pip install -r requirements.txt`)

## Project Structure

- `code/`: Source code modules
- `data/`: Raw and processed data artifacts
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications

## Execution Workflow

### 1. Environment Validation

```bash
bash code/validate_env.sh
```

### 2. Data Preparation

Fetch BEIR datasets and inject synthetic redundancy:

```bash
python code/data_loader.py prepare
python code/data_loader.py validate_trec_covid
```

### 3. Baseline Metrics (Unique Subset)

Generate unique subset and run baseline:

```bash
python code/unique_subset_generator.py
python code/run_baseline_unique.py
```

### 4. Flagged Pairs Analysis (T013a)

Calculate cosine similarity proxy and flag wasted calls:

```bash
python code/calculate_flagged_pairs.py
```

### 5. Sample Size Calculation (T013c)

Calculate dynamic sample size for LLM consensus:

```bash
python code/calculate_sample_size.py
```

### 6. Stratified Sampling (T013b)

Filter logged comparisons and select stratified sample:

```bash
python code/run_sampling.py
```

### 7. LLM Consensus Validation (T014/T014b)

Run LLM validation on sampled pairs:

```bash
python code/run_consensus.py
```

### 8. Full Pipeline Execution (US2)

Run the full pipeline with clustering-aided variant:

```bash
python code/run_pipeline.py --variant baseline --budgets 20 50 100 --seeds 5
python code/run_pipeline.py --variant clustering_aided --budgets 20 50 100 --seeds 5
```

### 9. Threshold Sweep (T025)

Run sensitivity analysis on MinHash-LSH thresholds:

```bash
python code/run_threshold_sweep.py
```

### 10. Statistical Analysis (US3)

Run statistical tests and generate reports:

```bash
python code/generate_statistical_report.py
```

## Artifact Outputs

| Task | Output File | Description |
|------|-------------|-------------|
| T012a/T012c | `data/processed/injected_datasets.json` | Injected redundant datasets |
| T013a | `data/results/flagged_pairs_count.json` | Count of flagged wasted calls |
| T013c | `data/results/sample_config.json` | Dynamic sample size configuration |
| **T013b** | **`data/results/consensus_sample.json`** | **Stratified sample indices for LLM validation** |
| T014b | `data/results/consensus_accuracy.json` | LLM consensus accuracy metrics |
| T015b | `data/results/us1_baseline_metrics.json` | Baseline NDCG@10 metrics |
| T013d | `data/results/us1_efficiency_ratio.json` | Wasted call ratio metrics |
| T020a | `data/processed/clusters.json` | MinHash-LSH cluster artifacts |
| T025a | `data/results/threshold_sweep.json` | Threshold sweep results |
| T031 | `data/results/statistical_report.md` | Final statistical report |

## Troubleshooting

- **Missing artifacts**: Ensure all prerequisite tasks are completed in order.
- **Resource limits**: Adjust `MAX_RUNTIME_HOURS` and `MAX_MEMORY_GB` in `code/config.py`.
- **Data integrity**: Run `python code/check_data_integrity.py` to verify artifacts.

## Parallel Execution

Tasks marked [P] in `tasks.md` can be executed in parallel if dependencies are met.

## Next Steps

After completing T013b, proceed to T014 (LLM consensus validation) and T015 (baseline active ranker execution).