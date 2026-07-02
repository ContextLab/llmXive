# Quickstart: 001-social-exclusion-reward-neural

## Prerequisites

- Python 3.11+
- `git`
- GitHub Actions free-tier runner (2 vCPU, 7 GB RAM)
- Access to OpenNeuro (via CLI or HuggingFace)

## Installation

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-392-the-impact-of-simulated-social-exclusion
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

3. **Set Environment Variables** (if needed for dataset access):
   ```bash
   export OPENNEURO_API_KEY=<your-key>
   ```

## Running the Pipeline

### 1. Download Data
```bash
python code/main.py --action download --dataset ds000246
```
- Downloads `ds000246` (or `ds003195`) to `data/raw-fmri/`.
- Verifies checksums.

### 2. Preprocess Data
```bash
python code/main.py --action preprocess --smoothing 6 --batch-size 5
```
- Processes participants in batches to stay within 7 GB RAM.
- Outputs preprocessed NIfTI to `data/processed-fmri/`.

### 3. Extract ROIs
```bash
python code/main.py --action extract --roi ventral_striatum --roi orbitofrontal_cortex
```
- Extracts beta estimates for 'Reward > Neutral' and 'Anticipation > Baseline'.
- Saves to `data/extracted/`.

### 4. Run Analysis
```bash
python code/main.py --action analyze --correction fwe-svc
```
- Performs two-sample t-tests.
- Applies FWE correction.
- Saves results to `data/results/`.

### 5. Sensitivity Analysis
```bash
python code/main.py --action sensitivity --smoothing-range 4,6,8 --roi-range 8,10,12
```
- Sweeps thresholds and reports consistency.

### 6. Generate Visualizations
```bash
python code/main.py --action viz --format png
```
- Creates bar plots and SPM overlays.
- Saves to `docs/paper/figures/`.

### 7. Compile Report
```bash
python code/main.py --action report
```
- Generates summary report with all findings.

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Contract Tests
```bash
pytest tests/contract/
```

### Integration Test (Sample Data)
```bash
pytest tests/integration/ --dataset ds000246 --sample-size 4
```

## Troubleshooting

- **Memory Error**: Reduce `--batch-size` in preprocessing.
- **Missing Labels**: Check `participants.tsv` for `condition` column.
- **Power Limitation**: If N<20 per group, results are framed as exploratory.
