# Quickstart: Investigating the Relationship Between Brain Network Dynamics and Baseline Working Memory Performance

## Prerequisites

- Python 3.11+
- Docker (for fMRIPrep)
- Git
- GB free disk space
- 7 GB RAM

## Installation

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-359-investigating-the-relationship-between-b
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

3. **Verify fMRIPrep**:
   ```bash
   docker pull nipreps/fmriprep:23.1.3
   ```

## Running the Pipeline

### Step 1: Download Data
```bash
python code/src/download.py --dataset ds000278 --output data/raw/
```
*Verifies checksums and logs to `data/raw/checksums.json`.*

### Step 2: Preprocess & Validate
```bash
python code/src/preprocess.py --input data/raw/ds000278 --output data/preprocessed/ --motion-threshold 0.3 --docker-memory 6g
```
*Excludes participants with mean FD > 0.3 mm. Logs exclusions to `data/logs/pipeline_log.json`. Docker memory limited to a constrained capacity to fit the available RAM constraint..*

### Step 3: Extract Metrics
```bash
python code/src/metrics.py --preprocessed data/preprocessed/ --parcellation Schaefer400 --output data/results/baseline_metrics.csv
```

### Step 4: Power Analysis & PCA
```bash
python code/src/utils.py --power-analysis --n <actual_N> --alpha 0.05 --effect-size 0.15 --output data/results/power_analysis.txt
python code/src/metrics.py --input data/results/baseline_metrics.csv --pca --output data/results/pca_components.csv
```
*Aborts if N < 30. Calculates achieved power (expected ~0.65 for N=30). Warns if power < 0.80.*

### Step 5: Regression
```bash
python code/src/regression.py --metrics data/results/pca_components.csv --output data/results/model_summary.csv --seed 42
```
*Performs permutation testing (a sufficient number of shuffles) and Holm-Bonferroni correction.*

### Step 6: Visualization
```bash
python code/src/visualize.py --summary data/results/model_summary.csv --output data/results/effect_sizes.pdf --seed 42
```

## Reproducibility Check

To verify deterministic reproducibility:
```bash
# Run twice with same seed
python code/src/visualize.py --summary data/results/model_summary.csv --output test1.pdf --seed 42
python code/src/visualize.py --summary data/results/model_summary.csv --output test2.pdf --seed 42

# Compare hashes
sha256sum test1.pdf test2.pdf
# Output hashes must be identical
```

## Troubleshooting

- **Memory Error**: Ensure Docker memory limit is set to 6 GB (`--docker-memory 6g`). Check swap space.
- **fMRIPrep Failure**: Check Docker logs; ensure sufficient disk space.
- **Missing IDs**: Pipeline aborts with exit code 1. Check `data/logs/pipeline_log.json`.
- **Power Warning**: If power < 0.80, results are framed as exploratory.