# Quickstart: llmXive Follow-up: Extending ProRL for Zero-Shot Proactive Recommendation

## 1. Prerequisites
- Python 3.11+
- Access to a GitHub Actions runner (or local machine with 7GB+ RAM).

## 2. Installation

1. **Clone and Setup**:
   ```bash
   git checkout 001-llmxive-prorl-zero-shot
   cd projects/PROJ-940-llmxive-follow-up-extending-prorl-effect/code
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Dependencies include: `pandas`, `numpy`, `scikit-learn`, `networkx`, `scipy`, `datasets`, `pyyaml`, `pytest`.*

## 3. Data Download
The pipeline automatically downloads the verified dataset on the first run.
```bash
python main.py --download-only
```
*This will fetch the MovieLens `ml-latest-small` dataset from the verified Hugging Face URL and store it in `data/raw/`.*

## 4. Running the Pipeline

Execute the full zero-shot analysis:
```bash
python main.py --seed 42 --path-length 5 --alpha 0.1 --beam-width 50 --k 10
```

**Parameters**:
- `--seed`: Random seed for reproducibility (default: 42).
- `--path-length`: Length of recommendation paths (default: 5).
- `--alpha`: PSA coefficient (default: 0.1). Set to 0.0 for the control condition.
- `--beam-width`: Number of candidate paths to generate (default: 50).
- `--k`: K value for Precision@K (default: 10).

## 5. Sensitivity Analysis
Run the sensitivity sweep over thresholds:
```bash
python main.py --sweep-thresholds 0.01,0.05,0.1
```

## 6. Expected Outputs
- `results/raw_paths.json`: Baseline beam paths.
- `results/rectified_paths.json`: ProRL-scored paths.
- `results/metrics_summary.json`: Precision, Recall, Diversity, Coverage.
- `results/statistical_report.json`: P-values and test types.

## 7. Troubleshooting
- **Memory Error**: Reduce `--beam-width` or `--sample-size` in `config.py`.
- **No Paths Found**: Check if the graph is disconnected; the system will report null paths for disconnected seeds.
- **Dataset Missing**: Ensure network access to Hugging Face.