# Quickstart: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or local environment with same constraints (CPU-only, <7GB RAM)
- Access to PhysioNet (for TUH EEG Corpus download)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-429-the-impact-of-network-efficiency-on-age-
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Download Data
```bash
python code/data/download.py
```
- Downloads TUH EEG Corpus (tuh_eeg) from PhysioNet.
- Validates checksums; stores in `data/raw/`.
- Generates `trace_id` and updates `state/version_map.yaml`.

### Step 2: Preprocess EEG
```bash
python code/data/preprocess.py
```
- Applies bandpass filter (1-40 Hz), ICA artifact removal, epoching (10s for connectivity).
- Outputs preprocessed epochs to `data/processed/`.
- Generates `trace_id` and updates `state/version_map.yaml`.

### Step 3: Compute Network Metrics
```bash
python code/network/metrics.py --density-range 0.05,0.20,0.01
```
- Computes coherence (10s epochs), constructs graphs across density range, derives AUC metrics.
- Outputs `data/results/metrics.csv`.
- Generates `trace_id` and updates `state/version_map.yaml`.

### Step 4: Statistical Analysis
```bash
python code/stats/correlation.py
python code/stats/regression.py
```
- Performs Spearman correlation, multiple regression (Cognition ~ Efficiency), correction.
- Outputs `data/results/stats.csv` and `power_analysis_report.json`.
- Generates `trace_id` and updates `state/version_map.yaml`.

### Step 5: Visualization
```bash
python code/viz/plots.py
```
- Generates age-stratified plots, regression tables.
- Outputs to `data/results/plots/`.

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

## Configuration

- **Density Threshold**: Set via `--density-range` flag (default: 0.05 to 0.20).
- **Frequency Band**: Alpha (8-12 Hz) by default; configurable in `config.py`.
- **Correction Method**: Bonferroni by default; switch to FDR in `config.py`.
- **Cognitive Registry**: Defined in `code/config/cognitive_registry.json`.

## Troubleshooting

- **Memory Error**: Reduce dataset size or process in batches; ensure subset fits <7GB RAM.
- **Missing Data**: Check dataset-variable fit; if cognitive scores missing, analysis restricts to age.
- **Low Power**: If N < 100 (or effective N < 85), expect warnings; interpret results cautiously.
- **Traceability**: Verify `trace_id` in output CSVs matches entries in `state/version_map.yaml`.

## Output

- `data/results/metrics.csv`: Network metrics per participant (AUC values).
- `data/results/stats.csv`: Correlation and regression results.
- `power_analysis_report.json`: Power analysis results.
- `state/version_map.yaml`: Artifact hashes and timestamps.
- `data/results/plots/`: Visualizations for paper.