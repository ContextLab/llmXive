# Quickstart Guide: Non-Neural VLA Approximation Pipeline

This guide describes the end-to-end execution of the llmXive pipeline for approximating VLA priors using non-neural models.

## Prerequisites

- Python 3.9+
- Install dependencies: `pip install -r requirements.txt`

## Directory Structure

The project assumes the following structure:
- `code/`: Source scripts
- `data/`: Input and output data
- `artifacts/`: Trained models
- `data/results/`: Execution logs and reports

## Execution Steps

Run the pipeline in the following order:

1. **Ingestion**: Download and parse the Qwen-VLA dataset.
 ```bash
 python code/01_ingest.py
 ```

2. **Clustering**: Extract kinematic features and cluster trajectories.
 ```bash
 python code/02_cluster.py
 ```

3. **Training**: Train Decision Trees and CGMMs per cluster.
 ```bash
 python code/03_train.py
 ```

4. **Inference**: Generate trajectories for new prompts.
 ```bash
 python code/04_inference.py
 ```

5. **Simulation**: Evaluate trajectories in PyBullet.
 ```bash
 python code/05_simulate.py
 ```

6. **Evaluation**: Compare against baselines and calculate metrics.
 ```bash
 python code/06_evaluate.py
 ```

7. **Fidelity**: Calculate trajectory fidelity.
 ```bash
 python code/07_calculate_fidelity.py
 ```

8. **Reporting**: Generate the final evaluation report.
 ```bash
 python code/08_generate_report.py
 ```

## Validation

To validate the entire pipeline execution, run:
```bash
python code/validate_quickstart.py
```
This will execute all steps and save the log to `data/results/e2e_run_log.txt`.

## Expected Output

Upon successful completion, the log will contain:
- "Pipeline Complete"
- "Exit Code: 0"
