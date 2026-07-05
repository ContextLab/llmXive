# Implementation Plan: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

**Branch**: `001-uncovering-correlations` | **Date**: 2026-06-24 | **Spec**: `specs/001-uncovering-correlations/spec.md`

## Summary

This feature implements a reproducible data pipeline to predict crystallographic texture coefficients (ODF peak intensities for {100}, {110}, {111} planes) from rolling process parameters (speed, temperature, reduction ratio) across multiple alloy families. 

**Critical Distinction**: The system distinguishes between **Pipeline Validation** (using synthetic data) and **Scientific Discovery** (using real data). 
- **Synthetic Data**: Used exclusively to validate code logic, data flow, and contract enforcement. Results (e.g., R² ≥ 0.50) are tautological sanity checks and **cannot** validate physical hypotheses.
- **Real Data**: Required to answer the research question regarding "how parameters influence texture." If real data is insufficient, the study explicitly reports an inability to draw scientific conclusions, rather than relying on synthetic results.

The system ingests real data from Materials Project/OMDB/NIST if available; otherwise, it falls back to a physics-informed synthetic data generator. A multi-output RandomForestRegressor is trained and evaluated against strict success criteria. The pipeline includes rigorous data hygiene, VIF-based collinearity checks (with forced inclusion of confounders), and sensitivity analysis, all containerized for GitHub Actions execution on free-tier CPU resources.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `pymtex` (with spherical-harmonic fallback), `numpy`, `matplotlib`, `pyyaml`, `joblib`  
**Storage**: Local file system (`data/`, `models/`, `output/`)  
**Testing**: `pytest` (unit/contract), GitHub Actions CI integration  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM, no GPU)  
**Project Type**: Data science pipeline / CLI tool  
**Performance Goals**: ≤ 30 min hyperparameter tuning, ≤ 6h total runtime, ≤ 6GB RAM peak  
**Constraints**: 
- No GPU usage.
- Synthetic data only for pipeline validation (not scientific hypothesis).
- VIF ≥ 5 triggers feature removal **only for derived features**; known confounders (composition, history) are forced inclusion.
- Missing data > 20% aborts training.
- **Fallback**: If `pymtex` is unavailable, use spherical-harmonic approximation with equivalence criterion (±5% MRD on reference).

**Contract Enforcement**: The pipeline validates all data ingestion and output against the schemas in `contracts/` (e.g., `dataset.schema.yaml`, `model.schema.yaml`) before proceeding.

> All empirical quantities (dataset sizes, R² thresholds, sample counts) are derived from spec requirements or deferred to research/implementation phases.

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | ✅ PASS | Seeds pinned in code; data fetched from canonical sources; Docker/CI workflow defined. |
| **II. Verified Accuracy** | ✅ PASS | Dataset URLs cited from verified block. **Note**: Materials Project & NIST have NO verified source; OMDB is Partial. Plan reflects this accurately. |
| **III. Data Hygiene** | ✅ PASS | Checksums recorded; raw data immutable; derivations versioned; PII scan enforced. |
| **IV. Single Source of Truth** | ✅ PASS | All metrics trace to `data/` and `code/`; no hand-typed stats. |
| **V. Versioning Discipline** | ✅ PASS | Content hashes for artifacts; state file updated on change. |
| **VI. Experimental Measurement Fidelity** | ✅ PASS | **Synthetic generator MUST produce raw diffraction/ODF files** to satisfy this principle. |
| **VII. Model Transparency** | ✅ PASS | Model serialized with metadata; validation set held-out; feature engineering documented. |

## Project Structure

### Documentation (this feature)

```text
specs/001-uncovering-correlations/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # CLI entry point
├── data/
│   ├── __init__.py
│   ├── loader.py        # Real data ingestion (Materials Project, OMDB, NIST)
│   ├── synthetic.py     # Synthetic data generator (FR-011) - MUST generate ODF files
│   └── preprocess.py    # Cleaning, imputation, VIF, feature engineering (FR-002)
├── models/
│   ├── __init__.py
│   ├── trainer.py       # RandomForest training + tuning (FR-004)
│   └── evaluator.py     # Metrics, importance, sensitivity (FR-005, FR-009, FR-010)
├── utils/
│   ├── __init__.py
│   ├── logger.py        # Pipeline logging (FR-007)
│   └── validators.py    # Data quality checks (edge cases)
└── config/
    └── settings.yaml    # Paths, seeds, thresholds

tests/
├── __init__.py
├── contract/
│   └── test_schemas.py  # Validates against contracts/*.schema.yaml
├── unit/
│   ├── test_synthetic.py
│   └── test_preprocess.py
└── integration/
    └── test_pipeline.py

data/
├── raw/                 # Immutable raw data (real or synthetic)
├── processed/           # Derived features, ODF coefficients
└── models/              # Serialized models, logs

output/
├── predictions.csv
├── new_predictions.csv
├── evaluation_report.json
├── importance_plot.png
└── pipeline.log

requirements.txt
Dockerfile
.github/workflows/ci.yml
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `output/`) chosen for simplicity and alignment with CLI/data-pipeline nature. No frontend/backend split. Tests organized by contract/unit/integration.

## Complexity Tracking

*No violations identified. All complexity justified by spec requirements (e.g., multi-output RF, VIF checks, synthetic fallback, causal distinction).*