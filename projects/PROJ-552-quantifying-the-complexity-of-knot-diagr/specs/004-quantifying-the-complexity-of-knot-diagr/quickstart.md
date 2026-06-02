# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or later
- pip (Python package manager)
- Access to internet (for downloading Knot Atlas data)
- Git (for version control)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r code/requirements.txt
```

**Key Dependencies**:
- pandas: Data manipulation
- scikit-learn: Regression modeling
- matplotlib, seaborn: Visualization
- requests: HTTP requests for Knot Atlas
- pyyaml: Configuration file parsing
- datasets: HuggingFace dataset utilities (if needed)

### 4. Verify Installation

```bash
python -c "import pandas; import sklearn; print('Dependencies installed successfully')"
```

## Running the Analysis

### Full Pipeline

Execute the complete analysis pipeline:

```bash
python code/cli/run_pipeline.py
```

This will:
1. Download knot data from Knot Atlas
2. Parse and clean the dataset
3. Compute additional invariants
4. Generate exploratory plots
5. Fit regression models
6. Construct composite complexity score
7. Generate reproducibility documentation

### Individual Stages

**Stage 1: Data Download**
```bash
python code/cli/run_stage.py --stage download
```

**Stage 2: Invariant Computation**
```bash
python code/cli/run_stage.py --stage compute_invariants
```

**Stage 3: Exploratory Analysis**
```bash
python code/cli/run_stage.py --stage exploratory_analysis
```

**Stage 4: Regression Modeling**
```bash
python code/cli/run_stage.py --stage regression_analysis
```

**Stage 5: Composite Score**
```bash
python code/cli/run_stage.py --stage composite_score
```

### Reproducibility Check

Verify all reproducibility artifacts are present:

```bash
python code/cli/verify_reproducibility.py
```

This checks:
- Random seeds are pinned
- Checksums are recorded
- Derivation notes are complete
- Logs are present

## Output Files

### Data Files
| File | Location | Description |
|------|----------|-------------|
| `knot_atlas_export.json` | `data/raw/` | Raw downloaded data (unchanged) |
| `knot_records_cleaned.csv` | `data/processed/` | Parsed and cleaned dataset |
| `knot_records_with_invariants.csv` | `data/processed/` | Dataset with computed invariants |
| `regression_results.json` | `data/processed/` | Model fitting results |
| `composite_complexity_scores.csv` | `data/processed/` | Composite score values |

### Plot Files
| File | Location | Description |
|------|----------|-------------|
| `crossing_vs_braid_alternating.png` | `data/plots/` | Scatter plot for alternating knots |
| `crossing_vs_braid_nonalternating.png` | `data/plots/` | Scatter plot for non-alternating knots |

### Documentation Files
| File | Location | Description |
|------|----------|-------------|
| `checksums.md` | `docs/reproducibility/` | SHA-256 checksums for all data files |
| `derivation_notes.md` | `docs/reproducibility/` | Step-by-step transformation documentation |
| `algorithm_validation.md` | `docs/reproducibility/` | Algorithm validation results |
| `validation_scope.md` | `docs/reproducibility/` | Phase 1 scope validation documentation |
| `excluded_knots.md` | `docs/reproducibility/` | List of excluded knots (torus/satellite) |
| `uncomputable_invariants.md` | `docs/reproducibility/` | Records where invariants not computable |

## Configuration

### Complexity Weights

Edit `config/complexity_weights.yaml` to customize composite score weights:

```yaml
crossing_number_weight: 0.5
braid_index_weight: 0.5
```

### Random Seeds

Random seeds are pinned in code per Constitution Principle I. To view current seed values:

```bash
grep -r "random.seed" code/
```

Seed values used are documented in `docs/reproducibility/derivation_notes.md`.

## Troubleshooting

### Knot Atlas Unavailable

If Knot Atlas is unavailable, the system will:
1. Apply exponential backoff (1s → 2s → 4s → ... → 60s max)
2. After 3 consecutive failures, cache partial results to disk
3. Log retry attempts in `docs/reproducibility/logs/`

### Missing Invariants

Knots with missing invariants are flagged with `missing_invariant_flags` rather than silently excluded. See `docs/reproducibility/uncomputable_invariants.md` for details.

### Algorithm Validation Coverage <10%

If KnotInfo reference coverage is <10% of the dataset, validation is skipped and limitation documented in `docs/reproducibility/algorithm_validation.md`.

### Tie-Breaking Validation Failure

If tie-breaking validation script fails, invariant computations are considered incomplete and must be re-run. See `docs/reproducibility/validation_status.md` for error details.

## Next Steps

1. Review exploratory plots in `data/plots/`
2. Examine regression results in `data/processed/regression_results.json`
3. Read reproducibility documentation in `docs/reproducibility/`
4. Prepare Phase 1 report with explicit scope limitations (crossing number ≤10 validated)
