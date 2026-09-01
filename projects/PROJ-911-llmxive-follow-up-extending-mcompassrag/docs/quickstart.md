# Quickstart: GraphCompass Reproducibility Validation

This guide validates the full pipeline reproducibility for project **PROJ-911-llmxive-follow-up-extending-mcompassrag**.
It ensures all components (Data Loading, Graph Construction, Retrieval Simulation, Correlation Analysis) run end-to-end on real data within the CI constraints.

## Prerequisites

- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`
- Real data access (HotpotQA, Wikipedia) via `datasets` library.

## Step 1: Initialize Directories and Data

Run the setup script to create directory structures and fetch/sample the real dataset.

```bash
python code/setup_data_dirs.py
python code/data_loader.py
```

**Expected Outputs**:
- `data/raw/sampled_corpus.parquet` (N ≤ 360)
- `data/processed/fixed_vocab.json`

## Step 2: Graph Construction & Feature Extraction (US1)

Execute the graph builder and topology extractor.

```bash
python code/vocabulary_builder.py
python code/graph_builder.py
python code/topology_extractor.py
```

**Expected Outputs**:
- `data/processed/graphs.json`
- `data/processed/features.csv`
- `data/results/latency.log`

## Step 3: Neural Baseline & Retrieval Simulation (US2)

Run the BERTopic baseline (CPU mode) and TF-IDF retrieval simulation.

```bash
python code/neural_baseline.py
python code/retrieval_sim.py
```

**Expected Outputs**:
- `data/results/retrieval_scores.csv`
- `data/results/retrieved_features.csv` (Topological metrics for retrieved docs)

## Step 4: Correlation & Validation (US3)

Calculate Spearman correlation, t-tests, and final metrics.

```bash
python code/evaluator.py
python code/final_metrics_writer.py
python code/validate_success_criteria.py
```

**Expected Outputs**:
- `data/results/correlation.csv`
- `data/results/ttest_results.json`
- `data/results/metrics.json`
- `data/results/validation_status.json`

## Verification Checklist

After running the steps above, verify the following:

1. **Artifacts Exist**: All files listed in "Expected Outputs" are present in `data/`.
2. **Schema Compliance**: Run `python code/validate_schemas.py` to ensure JSON/CSV schemas match contracts.
3. **Success Criteria**: Check `data/results/validation_status.json` for `hypothesis_supported` status.
4. **Latency**: Confirm `data/results/latency.log` shows processing time < 60s per document.
5. **Resource Usage**: Confirm `data/results/resource_usage.log` shows peak RAM < 7GB.

## Full Reproducibility Command

To run the entire pipeline in one go (for CI validation):

```bash
bash scripts/run_full_pipeline.sh
```

*(Note: Ensure `scripts/run_full_pipeline.sh` exists and calls the above steps in order.)*
