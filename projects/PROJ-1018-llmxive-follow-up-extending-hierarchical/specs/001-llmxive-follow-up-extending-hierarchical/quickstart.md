# Quickstart: llmXive follow-up: extending "Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode"

## 1. Prerequisites

- **Python**: 3.10 or higher.
- **System**: Linux environment with 2+ CPU cores and ~7GB RAM.
- **Dependencies**: `pip install -r requirements.txt`

## 2. Installation

```bash
# Clone the repository (if not already done)
git clone <repo-url>
cd projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Running the Pipeline

The pipeline consists of three stages: Extraction, Clustering, and Evaluation.

### Step 1: Dynamic Baseline Extraction
Extract relevance profiles from the validation split.
```bash
python src/extraction.py --mode dynamic --dataset "deepmind/pg19" --split "validation" --output data/interim/relevance_profiles.json
```

### Step 2: Static Index Construction
Cluster profiles to generate the static index (includes PCA and K-Means).
```bash
python src/clustering.py --input data/interim/relevance_profiles.json --k 100 --output data/processed/static_index_k100.json --seed 42
```

### Step 3: Comparative Evaluation
Evaluate the static model against the dynamic baseline on the test split.
```bash
python src/evaluation.py --dynamic-model "hils-dynamic" --static-index data/processed/static_index_k100.json --dataset "deepmind/pg19" --split "test" --output data/reports/eval_report.json
```

### Alternative: Run Full Pipeline Script
For automated execution of all stages:
```bash
./run_pipeline.sh
```
This script sequentially runs extraction, clustering, and evaluation with default parameters.

## 4. Sensitivity Sweep (Optional)

To run the sensitivity analysis across $K \in \{50, 100, 200\}$ (tuned on validation):
```bash
python src/evaluation.py --sweep-k "50,100,200" --dataset "deepmind/pg19" --output data/reports/sweep_report.json
```
*Note: The sweep selects the best K on the validation set and reports the final metrics on the test set.*

## 5. Verification

After running, verify the outputs:
- Check `data/interim/relevance_profiles.json` for non-empty `relevance_scores`.
- Check `data/processed/static_index_k100.json` for `chunk_to_cluster_map`, `centroids`, and `pca_components`.
- Check `data/reports/eval_report.json` for `p_value` (from Wilcoxon test) and `latency_reduction_factor`.

## 6. Troubleshooting

- **CUDA Error**: If the model requires GPU, the execution stage will auto-offload. If running locally, ensure `CUDA_VISIBLE_DEVICES` is set or use the CPU-only flag if available.
- **Memory Error**: If RAM is exceeded, reduce the batch size in `extraction.py` or stream the dataset more aggressively.
- **K-Means Failure**: If convergence fails, the script will retry with different seeds. If it fails after 3 retries, check the input data for NaNs.
- **PCA Failure**: If PCA reduces dimensionality to 0, check that the input relevance profiles have sufficient variance.