# Quickstart: Episodic Future Thinking in LLMs

## Prerequisites

- Python 3.11+
- 7GB+ RAM available
- Git
- Access to HuggingFace (for datasets)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llm-episodic-thinking/projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` pins `torch` to a CPU-only version, `faiss-cpu`, and `statsmodels` for LMM.*

## Data Setup

1. **Download Datasets**:
 The `data/setup.sh` script will download and verify checksums for ALFWorld and TextWorld datasets from their **official** repositories.
 ```bash
 bash data/setup.sh
 ```
 *This script fetches data from the verified official HuggingFace/GitHub URLs and records SHA256 checksums.*

2. **Verify Data Integrity**:
 ```bash
 python utils/verify_data.py
 ```

## Running the Baseline

Run the standard transformer baseline on a subset of tasks:
```bash
python experiments/run_baseline.py --tasks 10 --seed 42
```

## Running the Episodic Model

Run the episodic-augmented model:
```bash
python experiments/run_episodic.py --tasks 10 --seed 42 --threshold 0.75
```

## Running the Validation Protocol

Execute the counterfactual confidence calibration:
```bash
python validation/counterfactual_gen.py --perturbations 100
python validation/confidence_calib.py
```

## Sensitivity Analysis

Sweep retrieval thresholds to test robustness:
```bash
python experiments/sensitivity_analysis.py --thresholds 0.70 0.75 0.80
```

## Statistical Analysis

Run the Linear Mixed-Effects Modeling and FDR correction:
```bash
python utils/stats.py --input data/logs/episodic_results.json --variant 10 --fdr
```

## Expected Outputs

- `data/logs/baseline_results.json`: Accuracy metrics for baseline.
- `data/logs/episodic_results.json`: Accuracy metrics for episodic model.
- `data/logs/confidence_calibration.json`: Confidence scores for known/unknown details.
- `reports/statistical_analysis.pdf`: Mixed-effects modeling results and power analysis.

## Troubleshooting

- **OOM Error**: Reduce `--tasks` or batch size. Ensure you are using the CPU version of PyTorch.
- **Retrieval Slow**: Check FAISS index construction parameters. Ensure `state_embedding` dimension matches the model.
- **Data Mismatch**: Verify checksums in `data/checksums.txt` match the downloaded files.
- **Model Fails to Load**: Ensure `statsmodels` is installed for LMM functionality.

