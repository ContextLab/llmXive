# Quickstart: Testing the Equivalence Principle with Satellite Laser Ranging

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to GitHub Actions (for CI) or local Linux environment

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-752-testing-the-equivalence-principle-with-s
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify environment**:
   ```bash
   python -c "import scipy; import pandas; print('OK')"
   ```

## Configuration

Create `code/config.yaml` (or edit the default):

```yaml
data:
  sources:
    - name: "SLR NoteSense"
      url: "https://huggingface.co/datasets/vennsa/SLR-NoteSense/resolve/main/100.csv"
    - name: "Open SLR Turkish"
      url: "https://huggingface.co/datasets/emre/Open_SLR108_Turkish_10_hours/resolve/main/TR.zip"
    - name: "ILRS Archive"
      url: "https://ilrs.cddis.eosdis.nasa.gov/" # Programmatic access
  min_arc_days: 30  # Minimum temporal arc length (replaces 500 points)
  max_residual_cm: 2.0

dynamics:
  geopotential_models:
    - "GGM05C"
    - "EGM2008"
    - "GOCO06s"
  drag_model: "Jacchia"

analysis:
  correction_method: "Bonferroni"  # Options: Bonferroni, Holm-Bonferroni, Benjamini-Hochberg
  significance_level: 0.05
  target_precision: 1e-15
```

## Running the Pipeline

### 1. Ingest Data

```bash
python code/ingestion/downloader.py --config code/config.yaml
```

*Output*: `data/processed/normal_points.csv`, `logs/pipeline.log` (includes HTTP 403 retry logs and data sufficiency warnings).

### 2. Run Orbit Determination

```bash
python code/dynamics/solver.py --config code/config.yaml
```

*Output*: `data/processed/orbit_solutions.json`

### 3. Compute Eötvös Parameter

```bash
python code/analysis/eotvos.py --config code/config.yaml
```

*Output*: `data/processed/eotvos_results.csv`

### 4. Validation & Reporting

```bash
python code/analysis/validation.py --config code/config.yaml
```

*Output*: 
- `data/reports/summary.pdf`
- `data/reports/sensitivity_plot.png`
- `data/reports/diagnostic_report.csv` (Contains: $\chi^2$ improvement, final $\eta$ limit, post-fit residuals CSV)
- `data/reports/data_gap_report.txt` (If ILRS data is missing)

## Testing

Run unit tests:

```bash
pytest tests/unit/ -v
```

Run contract tests:

```bash
pytest tests/contract/ -v
```

## Troubleshooting

- **HTTP 403 Error**: The downloader implements exponential backoff (3 attempts). If it fails, check `logs/pipeline.log` for the specific error.
- **Insufficient Data**: If a satellite has < 30 days of arc length, it will be skipped with a warning in `logs/pipeline.log`.
- **Missing Metadata**: If satellite composition metadata is missing, the system will skip the satellite and log a warning.
- **Memory Error**: Ensure `streaming=True` is set in the config for large datasets.
