# Quick Start: Brain Network Dynamics & Sensorimotor Performance

This document outlines the minimal steps to run the analysis pipeline end-to-end.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`
- Sufficient disk space (~50 GB for HCP data downloads)
- For full preprocessing: FSL and AFNI installed locally (optional; CI uses synthetic validation)

## Running the Pipeline

### Phase 1: Setup
```bash
python code/setup_project_structure.py
python code/main.py --setup
```

### Phase 2: Data Acquisition & Preprocessing (User Story 1)
```bash
# Download HCP data (ICA-FIX if available, fallback to raw)
python code/data/download.py

# Preprocess (motion correction, slice-time, normalization, smoothing)
python code/data/preprocess.py

# Extract time-series and compute basic metrics
python code/data/metrics.py
```

### Phase 3: Network Metrics & Correlation Analysis (User Story 2)
```bash
# Compute graph metrics (modularity, efficiency, participation coeff, within-module degree)
python code/data/metrics.py

# Run PCA on network metrics and create full metrics CSV with PCA factors
python code/analysis/create_full_metrics.py

# Compute correlations with FD covariate and apply FDR correction
python code/analysis/correlations.py

# Calculate detectable effect size (power analysis)
python code/analysis/power.py
```

### Phase 4: Visualization & Report Generation (User Story 3)
```bash
# Generate scatter plots
python code/viz/scatter.py

# Generate network diagrams
python code/viz/network.py

# Generate final report (Markdown/PDF)
python code/report/generate.py
```

## Output Files

**Data:**
- `data/raw/` — Downloaded HCP NIfTI files
- `data/processed/` — Preprocessed images
- `data/analysis/metrics.csv` — Raw network metrics (modularity, efficiency, etc.)
- `data/analysis/pca_loadings.csv` — PCA component loadings
- `data/analysis/factor_scores.csv` — PCA factor scores per subject
- `data/analysis/full_metrics.csv` — **Complete dataset: raw metrics + PCA factors** (FR-005, FR-004)
- `data/analysis/correlation_results.csv` — Correlation statistics with FDR
- `data/analysis/power_analysis.csv` — Detectable effect sizes

**Figures:**
- `figures/scatter_*.png` — Metric vs. motor score scatter plots
- `figures/network_diagram.png` — Functional connectivity network

**Report:**
- `docs/report.md` — Markdown report with all results
- `docs/report.pdf` — PDF version (if pandoc available)

## Validation

```bash
# Verify all imports resolve correctly
python code/tools/verify_imports.py

# Check security hardening
python code/tools/verify_security.py

# Validate batching logic
python code/tools/verify_batching.py

# Run all unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v
```

## Troubleshooting

**Missing HCP data:**
- Ensure `HCP_CREDENTIALS` environment variable is set (or configure in `code/config.py`)
- Check network connectivity and HCP API status

**Memory errors during preprocessing:**
- Batch size is dynamically adjusted based on available RAM (7GB limit)
- Reduce `BATCH_SIZE` in `code/config.py` if needed

**FSL/AFNI not found:**
- Install locally: `fsl-complete`, `afni` packages
- Or use Docker: `docker run -it -v $(pwd):/work fsl-afni bash`
- CI uses synthetic validation for compatibility

**PCA or correlation computation fails:**
- Ensure `data/analysis/metrics.csv` exists with all required columns
- Run `python code/data/metrics.py` first to generate metrics

## Full Run (All Phases)

```bash
# One-command pipeline (sequential)
python code/main.py --full
```

This will:
1. Download and validate HCP data
2. Preprocess all subjects
3. Extract time-series and compute metrics
4. Run PCA and correlation analysis
5. Generate visualizations
6. Create final report