# Quickstart: Examining the Impact of Auditory Feedback on Motor Sequence Learning

## Prerequisites

- Python 3.11+
- Docker (for `fmriprep`)
- `datalad` or `aws` CLI (for OpenNeuro download)
- GitHub Actions free-tier runner (2 CPU, 7 GB RAM)

## Installation

```bash
# Clone repository
git clone <repo-url>
cd projects/PROJ-195-examining-the-impact-of-auditory-feedbac

# Create virtualenv
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r code/requirements.txt
```

## Running the Pipeline

### 1. Download Data (FR-001)
```bash
python code/download.py --dataset ds000246 --subset 5
```
*Note: Subsets to 5 subjects if full dataset >14GB. Corrected dataset ID from ds000115 to ds000246.*

### 2. Preprocess (FR-002)
```bash
python code/preprocess.py --mem-mb 6000 --nprocs 2
```
*Excludes subjects with motion >2mm.*

### 3. First-Level GLM (FR-003)
```bash
python code/glm_first_level.py --contrast perturbed_normal
```
*Generates contrast maps for each subject (perturbed > normal).*

### 4. Group Analysis (FR-004)
```bash
python code/glm_group.py --correction fdr --q 0.05 --test one-sample
```
*Outputs statistical map and cluster table (One-sample t-test against zero).*

### 5. Brain-Behavior Correlation (FR-006)
```bash
python code/correlation.py --roi auditory_cortex
```
*Generates scatter plot and correlation stats (Global learning rate vs. Sensitivity).*

### 6. Visualization (FR-007)
```bash
python code/viz.py --output-dir data/processed/results
```
*Generates thresholded maps and plots.*

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests (subset)
pytest tests/integration/test_pipeline.py --subset
```

## Troubleshooting

- **OOM Errors**: Reduce `--mem-mb` in `preprocess.py` or decrease subject subset.
- **Motion Failures**: Check `preprocessing.log` for excluded subjects.
- **No Clusters**: Verify FDR threshold; check `stats_config.yaml`. Note: Null results are valid outcomes in this pilot study.
- **Dataset Error**: Ensure `ds000246` is used. `ds000115` does not contain the required event labels.