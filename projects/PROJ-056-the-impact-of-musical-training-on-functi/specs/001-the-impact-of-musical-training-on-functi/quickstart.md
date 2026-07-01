# Quickstart: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Prerequisites

- Python +
- GB RAM available
- GB Disk space
- Git

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-056-the-impact-of-musical-training-on-functi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Running the Pipeline

### 3.1 Synthetic Data Mode (Default)
Since no verified real dataset is available, the pipeline defaults to generating synthetic data for validation.

```bash
python code/main.py --mode synthetic --n-subjects
```

**Output**:
- `data/processed/subjects.csv`
- `data/processed/connectivity_matrices.npy`
- `data/results/statistical_results.csv`
- `data/results/nbs_components.json`

### 3.2 Real Data Mode (If Verified Source Available)
If a verified ABCD/HCP dataset is provided:

```bash
python code/main.py --mode real --data-path /path/to/verified/data
```

*Note: This will fail with "Data Source Missing" if the path does not contain the required variables (rs-fMRI, years_of_training).*

## 4. Verifying Results

Run the test suite to ensure the pipeline is working correctly:

```bash
pytest tests/
```

Check the memory usage log:
```bash
cat data/logs/memory_usage.log
```

## 5. Output Interpretation

- **`statistical_results.csv`**: Contains edge-wise comparisons. Look for `q_value < 0.05` for significant connections.
- **`nbs_components.json`**: Contains the largest connected component. Check `p_value_fwer` for network-level significance.
- **`sensitivity_analysis.csv`**: Shows how results change with different p-value thresholds.

## 6. Troubleshooting

- **Memory Error**: Reduce `--n-subjects` or ensure no other processes are using RAM.
- **Data Missing**: If running in `real` mode, ensure the dataset contains `years_of_training` and `rs-fMRI` columns. If not, switch to `synthetic` mode.
- **Runtime Error**: If NBS takes too long, reduce `--n-permutations` in `code/analysis/stats.py`.
