# Quickstart: 001-code-generation-performance-outcomes

## Prerequisites

- Python 3.11+
- Git
- Access to verified developer productivity datasets (see research.md Section 1)

## ⚠️ CRITICAL: Dataset Availability

**This project cannot proceed without verified developer productivity datasets.**

Current verified datasets block contains NO developer productivity data. Before running this pipeline:

1. Add verified dataset URLs for OpenDev benchmark or GitHub Copilot adoption studies to the verified datasets block, OR
2. Revise the spec to use available data (which currently has no developer productivity data)

See research.md Section 5 for resolution options.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-462-evaluating-the-impact-of-code-generation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Directory Structure

```text
projects/PROJ-462-evaluating-the-impact-of-code-generation/
├── code/
│   ├── requirements.txt
│   ├── ingest/
│   ├── analysis/
│   ├── viz/
│   ├── export/
│   └── main.py
├── data/
│   ├── raw/          # Downloaded datasets
│   ├── processed/    # Validated datasets
│   └── output/       # Results
├── specs/001-code-generation-performance-outcomes/
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   └── contracts/
└── tests/
```

## Running the Pipeline

### Step 1: Download and Validate Data

```bash
# Download datasets with checksum validation (FR-001)
python code/ingest/download.py --dataset-url <verified-url>

# Validate variable presence (FR-002)
python code/ingest/validate.py --input data/raw/dataset.parquet
```

**Expected Output**: Variable presence report showing which required variables are present/missing.

### Step 2: Run Statistical Analysis

```bash
# Run two-way ANCOVA with interaction terms (FR-003, updated from ANOVA)
# Calculate effect sizes (FR-004)
# Apply family-wise error correction (FR-005)
python code/main.py --input data/processed/cleaned.parquet --output data/output/
```

**Expected Output**: ANOVA/ANCOVA tables, effect sizes, adjusted p-values in `data/output/analysis.json`.

### Step 3: Generate Visualizations

```bash
# Generate boxplots with interaction lines (FR-007)
python code/viz/plots.py --input data/output/analysis.json --output data/output/plots/
```

**Expected Output**: Publication-ready boxplots in `data/output/plots/`.

### Step 4: Run Sensitivity Analysis

```bash
# Sweep experience thresholds (FR-009)
python code/analysis/sensitivity.py --input data/processed/cleaned.parquet --thresholds 1 2 3 --output data/output/sensitivity.csv
```

**Expected Output**: Sensitivity analysis results in `data/output/sensitivity.csv`.

### Step 5: Export Results

```bash
# Export CSV and JSON (FR-008)
python code/export/results.py --input data/output/analysis.json --output data/output/final/
```

**Expected Output**: CSV and JSON files in `data/output/final/`.

## Testing

```bash
# Run contract tests
pytest tests/contract/

# Run integration tests
pytest tests/integration/

# Run unit tests
pytest tests/unit/
```

## Reproducibility

- Random seeds are pinned in `code/main.py` (seed=42)
- Dependencies are pinned in `code/requirements.txt`
- Dataset checksums are recorded in `state/projects/PROJ-462.../artifacts.yaml`

**Principle I Compliance**: Results are reproducible by re-running `code/` against `data/` on a fresh runner.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Missing required variables | Check dataset-variable fit; see research.md Section 1 |
| Missing experience data >20% | Dataset filtered; flag for clarification (FR-010) |
| Power limitation (<30 per stratum) | Flag in output; interpret effect sizes with caution |
| VIF > 5 | Warning issued; independent effects cannot be claimed |
| Compute exceeds 6 hours | Sample data or simplify method; document scoping decision |

---

# References

(Only URLs from the verified‑datasets block are cited; none currently satisfy the variable requirements, reinforcing the need for dataset acquisition.)