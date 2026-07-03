# Quickstart: Assessing the Impact of Data Augmentation on Statistical Power in Small Samples

## Prerequisites

- Python 3.11+
- Git
- GitHub Actions runner (or local equivalent)

## Setup

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-269-assessing-the-impact-of-data-augmentatio
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

3. **Download Datasets**:
   ```bash
   python code/download_data.py
   ```
   This fetches 3 verified datasets (Breast Cancer, Ionosphere, Heart Disease) from verified URLs and checksums them in `data/raw/`.

4. **Run Simulation**:
   ```bash
   python code/main.py
   ```
   Executes the full Monte Carlo loop (36,000 iterations: 3 datasets × 3 sizes × 2 ground truths × 4 augmentations × 1000 iters) and outputs results to `results/`.

5. **Verify Results**:
   ```bash
   python code/analyze.py --validate
   ```
   Checks for missing configurations, checksum mismatches, and statistical validity (including safety threshold flagging).

## Expected Output

- `results/[dataset]_[size]_[ground_truth]_[method].json` files containing:
  - `type1_error_rate` (for null ground truth)
  - `type2_error_rate` (for alternative ground truth)
  - `confidence_interval`
  - `safety_threshold`: 0.10
  - `disclaimer`: "DISCLAIMER: Findings are associational..."

## Troubleshooting

- **Class Imbalance**: If a dataset cannot be subsampled to N=15, the system logs a warning and skips that configuration.
- **Memory Error**: Reduce `N_MAX` in `code/subsample.py` if running locally on constrained hardware.
- **Runtime Exceeded**: Parallelize iterations via `joblib` (optional; not default).