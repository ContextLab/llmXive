# Quickstart Guide: llmXive Follow-up (Wan-Streamer v0.1)

This guide validates the end-to-end reproducibility of the research pipeline.

## Prerequisites

- Python 3.9+
- `pip install -r code/requirements.txt`

## Step-by-Step Execution

To reproduce the research results, run the following scripts in order:

1. **Data Source Check**
 ```bash
 python code/data/validate_logs.py
 ```

2. **Extract Latents**
 ```bash
 python code/data/extract_latents.py
 ```

3. **Validate Thresholds**
 ```bash
 python code/tasks/validate_thresholds.py
 ```

4. **Preprocess Data**
 ```bash
 python code/data/preprocess.py
 ```

5. **Power Analysis & Sampling**
 ```bash
 python code/data/generate_power_analysis.py
 ```

6. **Train Model**
 ```bash
 python code/models/trainer.py
 ```

7. **Generate Counterfactual Indices**
 ```bash
 python code/data/generate_counterfactual_indices.py
 ```

8. **Hybrid Simulation**
 ```bash
 python code/inference/hybrid_sim.py
 ```

9. **Evaluate Metrics**
 ```bash
 python code/evaluation/metrics.py
 ```

## Automated Validation

To verify the entire flow at once, run:

```bash
python code/tasks/validate_quickstart.py
```

This script will execute the steps above and generate a report at `data/logs/quickstart_validation_report.json`.

## Expected Outputs

After successful execution, you should see:

- `data/processed/raw_extract.parquet`
- `data/processed/sampled_dataset.parquet`
- `data/models/estimator_checkpoint_final.pt`
- `data/processed/hybrid_output.parquet`
- `data/metrics/tost_results.csv`
- `data/logs/quickstart_validation_report.json`

## Troubleshooting

- If data source check fails, ensure `data/raw/wan-streamer-logs` exists or network access is available for VoxCeleb2.
- If memory errors occur, the pipeline includes automatic sample size reduction (see `code/tasks/reduce_sample_size.py`).
