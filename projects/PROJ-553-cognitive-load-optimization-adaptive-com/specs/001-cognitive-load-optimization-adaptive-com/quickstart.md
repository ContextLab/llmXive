# Quickstart: Cognitive Load Optimization

## Prerequisites

- Python 3.11+
- `pip` or `poetry`
- Access to GitHub Actions (for CI execution)
- **External Data**: A manually curated "Golden Set" of ≥50 expert-labeled interactions (or a dataset with concurrent NASA-TLX ratings) must be provided in `data/processed/golden_set.csv`.

## Installation

1. **Clone and Setup Environment**
   ```bash
   cd projects/PROJ-553-cognitive-load-optimization-adaptive-com
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Download Datasets & Verify Golden Set**
   Run the data loading script. This will fetch from verified HuggingFace sources and checksum the files.
   ```bash
   python code/load_data.py --download
   ```
   *Note*: The script will verify the presence of `data/processed/golden_set.csv`. **If this file is missing or lacks expert labels, the script will halt with an error.** No synthetic proxy will be generated.

## Running the Pipeline

Execute the full research pipeline:
```bash
python code/run_pipeline.py
```

This script performs:
1. **Load & Verify**: Checks dataset integrity and **Golden Set availability**.
2. **Train Load Model**: Fits the Gradient Boosting Regressor (only if Golden Set exists).
3. **Generate Tiers**: Creates complexity variations.
4. **Simulate**: Runs Adaptive vs Static conditions (only if load model is validated).
5. **Analyze**: Fits the Mixed-Effects Model and outputs statistics.

## Key Outputs

- `data/simulation_results/efficiency_metrics.csv`: Session-level efficiency scores.
- `data/simulation_results/model_stats.json`: Cohen's d, CI, p-values.
- `data/explanation_tiers/`: Generated text and metadata.
- `outputs/report.md`: Summary of findings (associational only).

## Troubleshooting

- **"Validation Data Missing"**: If `load_data.py` cannot find a Golden Set with expert labels (or concurrent self-reports), it will halt. **This is expected behavior.** You must provide the external data to proceed.
- **"Power Limitation"**: If an insufficient number of sessions are available, the pipeline will warn and may skip the mixed-effects model.
- **"VIF > 5"**: If predictors are collinear, the model will report this in the logs and avoid claiming independent effects.
- **"Circular Validation Detected"**: If the system detects that labels were generated from the same features used for training, it will halt. This confirms the heuristic proxy rejection.