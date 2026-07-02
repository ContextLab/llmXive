# Quickstart: Exploring the Relationship Between Brain Network Dynamics and Fluid Intelligence

## Prerequisites
- Python +
- FSL and AFNI installed (or available via system package manager)
- Git
- GB+ RAM available

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-216-exploring-the-relationship-between-brain
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Install system tools** (if not already present):
   ```bash
   # Ubuntu/Debian example
   sudo apt-get update
   sudo apt-get install fsl afni
   ```

## Running the Pipeline

### 1. Download and Validate Data
```bash
python code/download.py --datasets ds000224 --sample-size 10
```
- This script validates the presence of **Fluid Intelligence** scores.
- If no valid data is found, it halts with a critical error.
- Limit the number of subjects to a feasible range for confidence interval (CI) estimation.

### 2. Preprocess fMRI Data
```bash
python code/preprocess.py --input data/raw --output data/interim
```
- Processes subjects sequentially to manage memory.
- Generates motion-corrected, normalized, bandpass-filtered NIfTI files.
- Generates `data/processed/preprocessing_stats.json` for SC-001.

### 3. Compute Graph Metrics
```bash
python code/graph_metrics.py --input data/interim --atlas Schaefer200 --output data/processed/metrics.csv
```
- Computes global efficiency, modularity, and clustering coefficient.

### 4. Statistical Analysis
```bash
python code/stats.py --metrics data/processed/metrics.csv --behavioral data/processed/behavioral.csv --output reports/
```
- Performs correlation analysis, **Bonferroni** correction, and generates figures.

### 5. Resource Profiling
```bash
python code/utils.py --profile --output data/processed/resource_profile.json
```
- Generates `resource_profile.json` for SC-005.

### 6. Update Versioning
```bash
python code/hash_update.py --state state/projects/PROJ-216-exploring-the-relationship-between-brain.yaml
```
- Updates artifact hashes in the project state file.

## Verification
- Check `reports/summary.pdf` for correlation coefficients, p-values, and effect sizes.
- Verify `data/processed/preprocessing_stats.json` for success rate (SC-001).
- Verify `data/processed/resource_profile.json` for resource usage (SC-005).
- Run `pytest tests/` to ensure unit and integration tests pass.