# Implementation Plan: Predicting Molecular Stability from Spectroscopic Data with Attention Mechanisms

**Branch**: `001-predict-reaction-yields-from-spectra` | **Date**: 2026-07-14 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-predict-reaction-yields-from-spectra/spec.md`

## Summary

This project implements a multi-head self-attention neural network to predict **normalized DFT total molecular energy** (a proxy for molecular stability) using concatenated inputs: spectroscopic data (IR/Raman/NMR), structural fingerprints (ECFP4), and reaction conditions (if available). The core technical challenge is constructing a leakage-free dataset split based on molecular scaffolds while resampling heterogeneous spectral data to a unified grid. The implementation strictly adheres to CPU-only constraints (GitHub Actions free tier), utilizing PyTorch with CPU tensors and scikit-learn for statistical baselines. The plan ensures every Functional Requirement (FR-001 to FR-011) and Success Criterion (SC-001 to SC-005) is addressed by a specific implementation phase, with a formal pivot from "reaction yield" to "molecular stability" due to data availability.

> **Scope Note**: Due to the lack of verified datasets containing paired (Reaction SMILES, Experimental Yield, Spectrum) data, the target variable is defined as **normalized DFT total molecular energy**. The research question is reframed to investigate "predictive signal for molecular stability" rather than experimental yield. The plan explicitly acknowledges the circularity of DFT spectrum vs. DFT energy and focuses on testing "computational distinctness" and "robustness to noise" as the primary scientific contribution.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: PyTorch (CPU-only build), scikit-learn, RDKit, pandas, numpy, matplotlib, seaborn, pyyaml
**Storage**: Local file system (CSV/Parquet for data, JSON/YAML for logs); no external database.
**Testing**: `pytest` (unit tests for preprocessing, integration tests for model training).
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7GB RAM, no GPU).
**Project Type**: Computational research pipeline / CLI tool.
**Performance Goals**: End-to-end execution (data prep + training + eval) ≤ 6 hours on CPU.
**Constraints**: No GPU usage; no 8-bit/4-bit quantization; dataset size subset to fit available RAM; strict scaffold-based leakage prevention.
**Scale/Scope**: Processing of a subset of DFT data (simulated spectra and energy) to validate the attention mechanism's ability to detect spectral signals.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Addressed by pinning `requirements.txt`, using fixed random seeds in `code/`, and ensuring datasets are fetched from canonical HuggingFace URLs defined in `research.md`.
- **Principle II (Verified Accuracy)**: All citations in `research.md` are sourced from the "Verified datasets" block in `research.md`. The Reference-Validator Agent will verify these URLs before any artifact is accepted. **No external URLs will be invented.**
- **Principle III (Data Hygiene)**: The plan includes a `data/` directory structure where raw data is preserved, checksums are recorded in `state/`, and all transformations produce new files (no in-place modification).
- **Principle IV (Single Source of Truth)**: The `data-model.md` defines the **AnalysisTrace** entity and linkage mechanism that links every figure/statistic to a specific data row and code block hash. The `AnalysisTrace` entity includes `statistic_id`, `data_row_ids`, `code_block_hash`, `artifact_path`, and `description`.
- **Principle V (Versioning)**: Artifacts will carry content hashes. The plan mandates running `python -m src.cli.main --update-state` after any change to update the `updated_at` timestamp in the project state file. The `src/utils/state_manager.py` module performs this update.
- **Principle VI (Spectral Preprocessing)**: The data pipeline (Phase) explicitly implements resampling to fixed grids (typical IR ranges, –10 ppm for NMR) and unit variance normalization as required.
- **Principle VII (Structural Baseline & Interpretability)**: The evaluation phase (Phase 2) mandates training a **Fingerprint-Only Baseline** as a prerequisite for the interpretability analysis required by SC-003. The baseline isolates the signal contributed by spectra. The attention visualization is compared against the baseline to identify regions where the spectrum adds value.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-chemical-reaction-yields-from-spectra/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── ingestion.py          # Downloads and validates raw data
│   ├── preprocessing.py      # Resampling, normalization, splitting
│   └── loaders.py            # PyTorch Dataset classes
├── models/
│   ├── attention_net.py      # Multi-head attention model definition
│   ├── baselines.py          # Fingerprint-only, Spectrum-only, Condition-only
│   └── trainer.py            # Training loop, early stopping, logging
├── eval/
│   ├── metrics.py            # RMSE, MAE, R², t-test implementation
│   ├── interpretability.py   # Attention visualization, sensitivity analysis
│   └── permutation.py        # Permutation test logic
├── cli/
│   └── main.py               # Entry point for pipeline execution (--update-state)
├── config/
│   └── defaults.yaml         # Hyperparameters (LR, epochs, batch size)
├── utils/
│   ├── seeds.py              # Random seed management
│   ├── validators.py         # Schema validation helpers
│   └── state_manager.py      # State file update logic (Principle V)
└── tests/
    ├── contract/                 # Schema validation tests
    ├── integration/              # End-to-end pipeline tests
    └── unit/                     # Preprocessing and model logic tests

data/
├── raw/                      # Downloaded raw datasets (checksummed)
├── processed/                # Split, normalized, resampled data
└── artifacts/                # Model checkpoints, logs, figures

state/
└── projects/PROJ-165-.../    # Project state and artifact hashes
```

**Structure Decision**: A modular Python package structure (`src/`) is selected to separate concerns (data, model, eval) and facilitate unit testing. The `data/` directory is split into `raw` and `processed` to enforce Principle III (Data Hygiene). The `contracts/` directory in `specs/` holds the YAML schemas for validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multi-head Attention | Required by FR-003 to capture non-linear interactions between spectral regions and molecular properties. | Simple MLP or linear regression cannot model the "independent predictive signal" of specific spectral regions as required by the research question. |
| Scaffold Splitting | Required by FR-002 to prevent data leakage and ensure generalization to new chemical scaffolds. | Random splitting would leak structural information, inflating performance metrics and violating the scientific validity of the study. |
| CPU-Only Constraint | Required by the GitHub Actions free-tier environment (no GPU available). | GPU-accelerated training would fail in the CI environment, preventing the project from reaching `research_complete`. |
| Permutation Test | Required by FR-008 and SC-004 to verify signal learning vs. noise. | Omitting this test would leave the model's validity unproven against spurious correlations. |
| Structure-Only Baseline | Required to mitigate circularity (DFT energy vs. DFT spectra). | Without this baseline, it is impossible to prove the spectrum adds signal beyond the structure used to generate the target. |
| Noise Robustness Test | Required to validate that the spectral signal is not just a trivial reconstruction of DFT physics. | Omitting this test would leave the model's robustness to experimental error unproven. |

## Evaluation Strategy

### Static vs. Dynamic Validation
To ensure the spectral signal is not just a proxy for static structure:
1.  **Structure-Only Baseline**: Train a model on ECFP4 fingerprints only.
2.  **Spectrum-Only Baseline**: Train a model on spectra only.
3.  **Attention Model**: Train the full model.
4.  **Comparison**: If the Attention model significantly outperforms the Structure-Only baseline, it proves the spectrum adds independent signal. If the Attention model significantly outperforms the Spectrum-Only baseline, it proves the structure adds independent signal.

### Spectral Relevance Verification
- **Correlation with Residuals**: The attention weights must correlate significantly with the yield (energy) residuals (after controlling for fingerprints).
- **Literature Sanity Check**: Attention peaks will be compared to literature values as a secondary sanity check, but **not** as a primary pass/fail metric (SC-003 updated).

### Permutation Test
- **Shuffle Yields**: Randomly shuffle the target variable (DFT Energy) and retrain.
- **Expectation**: The model performance (R²) should drop to near-random levels (< 0.05), confirming the model learned signal rather than noise.

### Noise Robustness Test
- **Add Noise**: Add Gaussian noise to the spectral input to simulate experimental error.
- **Expectation**: The model trained on noisy spectra should maintain performance better than the model trained on clean spectra, demonstrating robustness.
