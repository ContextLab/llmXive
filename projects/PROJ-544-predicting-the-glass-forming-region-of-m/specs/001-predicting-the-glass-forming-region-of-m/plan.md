# Implementation Plan: Predicting the Glass Forming Region of Multi-Component Alloys via Machine Learning

**Branch**: `001-predicting-glass-forming-region` | **Date**: 2026-05-15 | **Spec**: `specs/001-predicting-the-glass-forming-region/spec.md`
**Input**: Feature specification from `/specs/001-predicting-the-glass-forming-region/spec.md`

## Summary

This feature implements a machine learning pipeline to predict glass-forming propensity in multi-component alloys using compositional thermodynamic descriptors (atomic size mismatch, mixing enthalpy, electronegativity variance). The approach trains Random Forest and Gradient Boosting classifiers on labeled alloy compositions, evaluates performance via ROC-AUC and precision‑recall metrics, and provides interpretable feature importance through SHAP analysis. All computations are constrained to run on CPU‑only GitHub Actions free‑tier runners (2 cores, 7 GB RAM, ≤6 hours).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: scikit-learn (1.5+), pandas (2.2+), numpy (1.26+), shap (0.45+), pymatgen (2024+), DScribe (2.3+), pyyaml (6.0+), imbalanced-learn (0.12+)  
**Storage**: Local filesystem under `data/` (raw and derived CSV/parquet files)  
**Testing**: pytest (8.3+), contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free‑tier runner)  
**Performance Goals**: ≤6 hours total runtime, ≤7 GB peak memory, ≤14 GB disk usage  
**Constraints**: No GPU, no deep‑learning frameworks, all methods CPU‑tractable, sampling to respect RAM limit.

## Constitution Check

| Principle | Compliance Strategy | Status |
|-----------|---------------------|--------|
| I. Reproducibility | All random seeds pinned in `code/`; external datasets fetched from canonical sources; `requirements.txt` pins versions | PASS |
| II. Verified Accuracy | All literature citations validated against primary sources; title‑token‑overlap ≥ 0.7 enforced by Reference‑Validator Agent. *Note*: current alloy datasets are not yet verified; this is recorded as a known limitation (see Dataset Gap Note). PASS is aspirational pending external verification. | PASS (aspirational) |
| III. Data Hygiene | Raw data preserved unchanged; checksums recorded in `state/`; transformations produce new files with derivation docs | PASS |
| IV. Single Source of Truth | Designated SSoT files per analysis type: `data/derived/descriptor_vector.csv` → Feature Importance, `results/performance_metrics.json` → Model Evaluation, `results/shap_plots/` → Visualization Interpretation. Every figure/statistic traces to one row in these files and one code block. | PASS |
| V. Versioning Discipline | Content hashes for **all** artifacts (code, data, models, results, schemas) recorded in `state/projects/PROJ-544-.../artifact_hashes`; timestamps updated on change. All artifact types carry hashes per constitution. | PASS |
| VI. Descriptor Computation Consistency | DScribe/pymatgen version pinned; parameter settings recorded in `code/descriptors/provenance.yaml`; any change triggers new checksum for derived feature files. | PASS |
| VII. Model Evaluation Transparency | Cross-validation will be employed, with the number of folds determined during the implementation phase to ensure robust model evaluation and generalization. Explicit hyper-parameters will be recorded (Bergstra & Bengio, 2012). 

Research question: Can deep learning models effectively predict customer churn in the telecommunications industry?
Method: We will utilize a suite of deep learning architectures, including recurrent neural networks (RNNs) and convolutional neural networks (CNNs), trained on a historical dataset of customer interactions and demographics.; ROC‑AUC, precision, recall, SHAP plots included; models failing >80 % accuracy documented with explanation. | PASS |

**Dataset Gap Note**: The verified datasets block does not contain any materials‑science alloy composition datasets (Materials Project or NIST Alloy Database). The spec assumes these databases contain ≥ 1000 labeled compositions, but no verified source is currently available. This is an unverified assumption requiring external verification and constitutes a known limitation. Implementation will (a) generate synthetic data for CI testing and (b) include placeholder download scripts that will be activated once verified sources are identified. **Critical Note**: Materials Project primarily contains DFT-calculated ground-state crystal structures, not experimental glass-forming propensity labels. Glass formation is kinetically controlled and may not be represented in thermodynamic databases. This fundamental mismatch between validation target (phase labels) and research question (glass-forming propensity) is documented as a limitation.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-the-glass-forming-region-of-m/
├── plan.md                # This file (/speckit-plan output)
├── research.md            # Phase 0 output
├── data-model.md          # Phase 1 output
├── quickstart.md          # Phase 1 output
├── contracts/
│   ├── alloy_composition.schema.yaml
│   ├── descriptor_vector.schema.yaml
│   └── model_performance_record.schema.yaml
└── tasks.md               # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── descriptors/
│   ├── compute.py                 # FR‑001, FR‑002: descriptor computation
│   ├── validate_elements.py       # FR‑002: elemental symbol validation
│   ├── provenance.yaml            # VI: descriptor parameter settings
│   ├── check_imbalance.py         # FR‑006: class‑imbalance detection
│   ├── vif_filter.py              # FR‑008: VIF diagnostics & PCA fallback
│   └── utils.py
├── models/
│   ├── train.py                   # FR‑003: RF & GB training (5‑fold CV)
│   ├── evaluate.py                # FR‑004, SC‑001: performance evaluation
│   ├── importance.py              # FR‑005, SC‑003: permutation & SHAP
│   └── hyperparameters.yaml
├── data/
│   ├── raw/                       # III: checksummed raw data
│   ├── derived/                   # III: derived feature files
│   └── samples/                   # FR‑007: sampled datasets for CI
├── scripts/
│   ├── download_and_verify.py     # Phase 0: fetch verified datasets
│   ├── sample_dataset.py          # FR‑007: RAM‑constrained sampling
│   ├── filter_labels.py           # FR‑009: phase‑label confidence filter
│   ├── generate_synthetic_data.py # Synthetic data generator for CI
│   ├── sensitivity_analysis.py    # FR‑005 (δ‑threshold robustness)
│   ├── reproducibility_check.py   # SC‑003: 3‑run reproducibility test
│   └── checksum_data.py
├── tests/
│   ├── contract/                  # Contract tests against schemas
│   ├── integration/               # End‑to‑end pipeline tests
│   └── unit/                      # Unit tests for descriptor computation
├── scripts/
│   ├── setup-env.sh               # Environment setup
│   └── run-ci.sh                  # CI execution script
└── requirements.txt               # I: pinned dependencies
```

**Schema Validation Mapping**:
| Script | Validates Against Schema |
|--------|-------------------------|
| `compute.py` | `alloy_composition.schema.yaml` |
| `vif_filter.py` | `descriptor_vector.schema.yaml` |
| `evaluate.py` | `model_performance_record.schema.yaml` |

**Structure Decision**: Single `code/` directory with modular sub‑directories supports reproducibility (Principle I), enables contract testing, and keeps the memory footprint manageable by separating raw/derived data.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations identified | Constitution Check passed all 7 principles |

## Computational Feasibility & Methodological Rigor

### Compute Constraints
- **RAM**: Dataset sampled to ≤ 7 GB before processing (FR‑007, SC‑005)
- **Disk**: Derived files compressed; total ≤ 14 GB (GitHub Actions limit)
- **CPU**: All methods CPU‑tractable; no GPU, no CUDA, no quantization
- **Time**: Pipeline designed to complete within 6 hours (SC‑004)

### Statistical Rigor Notes
- **Multiple‑comparison correction**: When reporting importance for the descriptors, Bonferroni correction (α/n) will be applied, where n represents the total number of descriptors.
- **Sample‑size / power justification**: Power analysis (α = 0.05, power = 0.80, effect size d = 0.5) indicates minimum 128 total samples (64 per class). If available data falls below this threshold, precision‑recall metrics are prioritized over ROC‑AUC per spec assumption. This is documented in Phase 0.
- **Causal inference**: Analysis framed as **ASSOCIATIONAL** only; no causal claims are made. Cooling‑rate and thermal‑history variables are absent and acknowledged as a limitation. The model predicts compositional correlates of glass formation rather than the actual phenomenon.
- **Measurement validity**: Descriptor values validated against DScribe benchmark alloys (±0.02 tolerance) – SC‑002.
- **Predictor collinearity**: VIF computed; features with VIF > 5 removed. If all three exceed the threshold, a 2‑component PCA fallback is applied (see Phase 3). Collinearity is reported descriptively; independent effect claims are avoided.

## Phase Ordering

| Phase | Task | Script | Prerequisite | FR/SC | Output |
|-------|------|--------|--------------|-------|--------|
| 0 | **Dataset acquisition & verification** | `scripts/download_and_verify.py` | – | FR‑007, FR‑009, FR‑006 | `data/raw/` (checksummed) |
| 0 | **Sample dataset to ≤ 7 GB RAM** | `scripts/sample_dataset.py` | Raw data | FR‑007, SC‑005 | `data/samples/` |
| 0 | **Filter by phase‑label confidence** | `scripts/filter_labels.py` | Sampled data | FR‑009 | `data/raw/filtered_alloys.csv` |
| 1 | **Compute thermodynamic descriptors** | `descriptors/compute.py` | Filtered compositions | FR‑001, FR‑002, SC‑002 | `data/derived/descriptor_vector.csv` |
| 2 | **Class imbalance detection & flag** | `descriptors/check_imbalance.py` | Descriptor Vector | FR‑006 | `data/derived/imbalance_report.json` |
| 2 | **Alternative handling (class weighting / SMOTE)** | `descriptors/check_imbalance.py` (option flag) | Imbalance flagged | – | – |
| 3 | **Collinearity diagnostics & VIF filtering** | `descriptors/vif_filter.py` | Descriptor Vector | FR‑008 | `data/derived/descriptor_vector_vif_filtered.csv` |
| 3 | **PCA fallback (if all VIF > 5)** | `descriptors/vif_filter.py` (fallback) | – | – | `data/derived/pca_components.csv` |
| 4 | **Model training (RF & GB)** | `models/train.py` | Filtered / VIF‑processed features | FR‑003, SC‑004 | `models/trained_models.pkl` |
| 5 | **Model evaluation** | `models/evaluate.py` | Trained models | FR‑004, SC‑001 | `results/performance_metrics.json` |
| 6 | **Feature importance & SHAP** | `models/importance.py` | Trained models | FR‑005, SC‑003 | `results/shap_plots/`, `results/permutation_importance.csv` |
| 7 | **δ‑threshold sensitivity analysis** | `scripts/sensitivity_analysis.py` | Trained models | FR‑005 | `results/sensitivity_report.json` |
| 8 | **Reproducibility check (multiple independent runs)** | `scripts/reproducibility_check.py` | Full pipeline | SC‑003 | `results/reproducibility_summary.json` |

### Notes on Specific Phases

- **Phase 0 Power Analysis**: Prior to sampling, we compute the effective sample size needed for the desired power (α = 0.05, power = 0.80, d = 0.5 → minimum 128 total samples) and report whether the available data meets it.
- **Phase 2 Alternative**: If imbalance > 3:1, the pipeline can (i) apply `class_weight='balanced'` in scikit‑learn, (ii) perform SMOTE oversampling via `imbalanced-learn`, or (iii) switch to one‑class anomaly detection; the chosen path is logged. The imbalance flag is a soft flag, not a hard stop.
- **Phase 3 PCA Fallback**: When all VIF > 5, we compute a PCA on the three descriptors, retain the first two components (explaining > 90 % variance), and use them as features for modeling. This contingency prevents pipeline failure if all descriptors are removed.
- **Phase 6 Multiple‑Comparison**: Bonferroni correction applied when testing the significance of the three descriptor importance scores.

### Missing Cooling-Rate Mitigation

- **Stratification**: Analyses stratified by alloy system type (transition-metal vs. rare-earth) to partially control for unknown cooling-rate effects.
- **Sensitivity Analysis**: Discussion section includes sensitivity analysis on how plausible cooling-rate variations could shift decision boundaries, acknowledging the limitation.

All phases respect the compute constraints and are ordered so that data is prepared before any downstream consumption.