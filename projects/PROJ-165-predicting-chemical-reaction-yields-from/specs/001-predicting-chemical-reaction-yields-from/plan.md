# Implementation Plan: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

**Branch**: `001-predict-reaction-yields-from-spectra` | **Date**: 2026-07-14 | **Spec**: `specs/001-predict-reaction-yields-from-spectra/spec.md`

## Summary

This project implements a multi-head self-attention neural network to predict chemical reaction yields using concatenated inputs: spectroscopic data (IR, NMR), ECFP4 fingerprints, and reaction condition vectors. The plan strictly adheres to the "CPU-first" compute constraint, utilizing a scaled-down dataset and quantized/efficient model architecture to fit within GitHub Actions limits (limited CPU, ~7GB RAM, 6h). The pipeline prioritizes rigorous data hygiene (leakage prevention via template splitting), statistical validity (Bonferroni-corrected t-tests, power analysis), and interpretability (attention heatmaps validated against simulation logic).

**Critical Pivot**: Due to the lack of verified experimental paired spectra/yield data, this plan pivots to using **DFT-simulated data** (sdmattpotter/dftest61523) exclusively. The research question is reframed to "Can a model learn the simulation logic mapping spectra to yield?" with a "Circularity Check" to reject the hypothesis if the simulation is too deterministic (R² > 0.95).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU mode), `scikit-learn`, `pandas`, `pyarrow`, `rdkit`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `joblib`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/artifacts`) with Parquet/JSONL formats  
**Testing**: `pytest` (unit, integration, contract)  
**Target Platform**: GitHub Actions Free Tier (Linux, CPU-only) with automatic offload logic for GPU-specific tasks (none planned for this scope, as models are scaled for CPU)  
**Project Type**: Computational Research Pipeline / CLI  
**Performance Goals**: Complete full training/evaluation pipeline ≤ 6 hours on 2 vCPU; Memory usage ≤ 6 GB peak.  
**Constraints**: No local GPU available; **Dataset size limited to a large-scale collection of samples (operational target)** to fit RAM, with a theoretical maximum if streaming is optimized; No access to gated datasets; Must handle missing spectral channels via masking.  
**Scale/Scope**: Single reaction type analysis (e.g., cross-coupling) or broad multi-task with strict template separation; A large-scale set of training samples.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
| :--- | :--- |
| **I. Reproducibility** | All random seeds pinned in `src/utils/seeds.py`. External datasets fetched via `datasets` library with specific commit hashes or checksums recorded in `state/`. Training logs saved deterministically. |
| **II. Verified Accuracy** | **Mandatory Blocking Gate**: The Reference-Validator Agent runs before execution. If any citation is unreachable or mismatch, the pipeline halts with exit code 1. All citations mapped to the "Verified datasets" block. |
| **III. Data Hygiene** | Raw data immutable; derivatives written to `data/processed/`. Checksums recorded in `state/...yaml`. No PII (chemical data is inherently non-PII). |
| **IV. Single Source of Truth** | All metrics in `paper/` trace to `data/artifacts/metrics.json`. Figures trace to `data/artifacts/figures/`. |
| **V. Versioning Discipline** | **Explicit Mapping**: After every artifact generation (code, config, data), compute SHA256 and update `state/...yaml`. This includes `tasks.md`, `plan.md`, and generated JSON/Parquet files. |
| **VI. Spectral Preprocessing** | `src/data/preprocessing.py` implements resampling to fixed grids (covering the mid-infrared to near-infrared regions and typical NMR chemical shift ranges) and unit variance normalization. **Masking Strategy**: Zero-fill missing spectrum arrays and append a binary mask vector (1=present, 0=missing) to the input tensor. |
| **VII. Structural Baseline** | `src/models/baselines.py` implements ECFP4-only, Spectrum-only, and Condition-only baselines. Attention heatmaps generated and compared against *simulated injection points* (not NIST, due to data mismatch). |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-reaction-yields-from-spectra/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── reaction_sample.schema.yaml
│   └── prediction_output.schema.yaml
└── tasks.md             # Phase 2 output (Generated previously, currently under revision (rejected by verifier))
```

### Source Code (repository root)

```text
src/
├── cli/
│   └── main.py          # Entry point for pipeline execution
├── data/
│   ├── ingestion.py     # Download and verify datasets (US-1)
│   ├── preprocessing.py # Resampling, normalization, template splitting (FR-001, FR-002)
│   └── loaders.py       # PyTorch Dataset/DataLoader wrappers
├── models/
│   ├── attention_net.py # Multi-head attention architecture (FR-003)
│   └── baselines.py     # Fingerprint/Spectrum/Condition only baselines (FR-005)
├── utils/
│   ├── seeds.py         # Reproducibility seed management (Constitution I)
│   ├── validators.py    # Schema validation, leakage checks (FR-014)
│   └── nist_refs.py     # Versioned reference module for functional groups (FR-012)
├── evaluation/
│   ├── metrics.py       # RMSE, MAE, R², VIF calculation
│   └── interpretability.py # Attention heatmaps, permutation tests (FR-007, FR-008)
└── config/
    └── defaults.yaml    # Hyperparameters (LR, batch size, epochs)

data/
├── raw/                 # Downloaded datasets (checksummed)
├── processed/           # Resampled spectra, split indices
└── artifacts/           # Leakage reports, model checkpoints, figures, validation reports

tests/
├── contract/            # Schema validation tests
├── integration/         # Pipeline end-to-end tests
└── unit/                # Unit tests for preprocessing, metrics
```

**Structure Decision**: Single project structure selected to minimize overhead. The `src/` hierarchy separates concerns (data, models, evaluation) to facilitate the "Single Source of Truth" principle and allow independent testing of the preprocessing pipeline vs. the model training.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Multi-Head Attention** | Required by FR-003 to capture distinct spectral regions and condition interactions. | Simple MLP would fail to isolate spectral contributions (SC-003) and provide interpretability. |
| **Template-Based Splitting** | Required by FR-002 to prevent data leakage. | Random splitting would allow reaction templates to appear in both train/test, invalidating SC-001. |
| **Baseline Suite** | Required by SC-001 to quantify "independent predictive signal" of spectra. | Training only the attention model would not prove spectra add value over fingerprints alone. |
| **Spectral Masking Ablation** | Required to mathematically decouple spectral signal from fingerprint input. | Architecture alone does not prove independence. **Mechanism**: Zero-out specific spectral bands (e.g., 1600-1800 cm⁻¹) and measure the drop in R². If the drop is significant while the fingerprint input remains constant, the signal is isolated. |
| **VIF Calculation** | Required by FR-016 to detect collinearity between spectral and fingerprint inputs. | Ignoring collinearity could lead to false claims of "independent" signal. |

## Data Flow & Transformations

1.  **Raw Ingestion**:
    *   Input: Parquet files from Hugging Face (sdmattpotter/dftest).
    *   Transformation: Extract SMILES, compute fingerprints (RDKit), parse conditions (if available).
    *   Output: `data/raw/intermediate.parquet`.

2.  **Spectral Preprocessing**:
    *   Input: Raw spectral arrays (variable length).
    *   Transformation: Resample to `SpectralGrid`, normalize (unit variance), handle missing channels (masking).
    *   Output: `data/processed/spectra_resampled.parquet`.

3.  **Splitting (Leakage Prevention)**:
    *   Input: `ReactionSample` list.
    *   Transformation: Group by `reaction_template_id`. Split groups into training, validation, and test sets..
    *   **Step 3.2**: Compute MD5 hashes of canonical SMILES and reaction template IDs. Compare against test set. Write results to `data/artifacts/leakage_report.json`.
    *   Output: `data/processed/train.parquet`, `data/processed/val.parquet`, `data/processed/test.parquet`.

4.  **Model Input**:
    *   Input: Preprocessed samples.
    *   Transformation: Batch creation, tensor conversion.
    *   Output: PyTorch `DataLoader` batches.

5.  **Evaluation Output**:
    *   Input: Predictions vs. Ground Truth.
    *   Transformation: Compute RMSE, MAE, R², Attention Weights.
    *   Output: `data/artifacts/metrics.json`, `data/artifacts/attention_heatmaps.png`.

6.  **Phase 4: Simulated Validation Report Generation** (FR-010, SC-003b):
    *   Trigger: If no experimental data is found (which is the case).
    *   Action: Generate `data/artifacts/simulated_validation_report.json` documenting the reliance on simulated data and the inability to validate against experimental reality.

7.  **Phase 5: Integrity & Limitation Reports** (FR-015, FR-016):
    *   Action: Run "Simulated Data Integrity Check" (R² > 0.95 threshold) and write `data/artifacts/integrity_report.json`.
    *   Action: Compute VIF and write `data/artifacts/vif_report.json`.
    *   Action: Generate `data/artifacts/limitation_note.md` documenting the data mismatch.

## Limitations & Assumptions

*   **Data Source**: Reliance on DFT-simulated spectra may not perfectly reflect experimental noise. This is mitigated by the "Simulated Validation Report" requirement.
*   **Condition Encoding**: If solvent/catalyst data is missing from the DFT dataset, the "condition" input will be a simplified reaction-type embedding.
*   **Power**: Sample size may limit the power to detect small effect sizes. in the t-test. We will report the achieved power or confidence intervals.
*   **Circularity**: The "independent signal" claim is not testable with DFT data if the simulation is deterministic. The plan includes a "Circularity Check" to reject the hypothesis if R² > 0.95.
*   **NIST Reference**: No verified programmatic dataset exists for the specific functional group frequencies required. We use a versioned, checksummed local JSON file (`src/data/nist_refs.json`) as a "Versioned Reference Module".