# Quickstart Guide for PROJ-169

This guide outlines the steps to run the full pipeline end-to-end.

## Prerequisites

1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

2. Set the data source environment variable (optional, defaults to 'materials_project'):
 ```bash
 export DATA_SOURCE=materials_project
 ```

## Execution Steps

Run the following commands in order. Each step produces artifacts required by the next.

### Step 1: Data Ingestion (T013d)

Download, parse, filter, and save the 2D material graphs.

```bash
python code/ingest/pipeline.py --source materials_project --output data/processed/graphs_v1.parquet
```

This command:
- Downloads raw data from the specified source.
- Parses CIF files into `MaterialGraph` objects.
- Filters for 2D materials and valid elastic tensors.
- Saves the processed graphs to `data/processed/graphs_v1.parquet`.
- Generates `data/processed/split_indices.json` (train/val/test).
- Updates `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` with the SHA256 checksum.
- Performs the volume check (SC-001).

### Step 2: Model Training (T018b)

Train the lightweight GNN on the processed data.

```bash
python code/model/train.py --config code/model/train_config.py --epochs 50 --patience 5 --data_path data/processed/graphs_v1.parquet --split_path data/processed/split_indices.json --output_log data/results/training_logs.json --output_test_indices data/processed/test_indices.json
```

This command:
- Loads the split indices.
- Trains the GNN model.
- Saves model weights to `data/processed/model_v1.pt`.
- Outputs `predictions.json` for the test set.
- Logs metrics to `data/results/training_logs.json`.

### Step 3: Inter-Family Generalization Test (T021a)

Evaluate the model's ability to generalize to unseen families.

```bash
python code/model/generalization_test.py --graphs data/processed/graphs_v1.parquet --split-indices data/processed/split_indices.json --predictions data/processed/predictions.json --output data/results/generalization_metrics.json
```

This command:
- Verifies that train and test sets are family-disjoint.
- Calculates the inter-family MAPE.
- Outputs `data/results/generalization_metrics.json`.

### Step 4: Terminology Audit (T037)

Scan the codebase for forbidden terminology.

```bash
python code/utils/terminology_scanner.py --output data/results/terminology_audit.json
```

## Verification

After running the pipeline, verify the following artifacts exist:
- `data/processed/graphs_v1.parquet`
- `data/processed/split_indices.json`
- `data/processed/test_indices.json`
- `data/processed/predictions.json`
- `data/results/training_logs.json`
- `data/results/generalization_metrics.json`
- `data/results/terminology_audit.json`
- `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` (with checksums)