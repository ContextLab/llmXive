# Implementation Plan: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

**Branch**: `001-predict-reaction-yields-from-spectra` | **Date**: 2026-07-14 | **Spec**: `specs/001-predict-reaction-yields-from-spectra/spec.md`

## Summary
This project implements a multi-head self-attention neural network to predict chemical reaction yields using concatenated inputs: **real experimental** spectroscopic data (IR, Raman, NMR), structural fingerprints (ECFP4), and reaction condition embeddings. The plan prioritizes a robust, leakage-free data pipeline that splits by reaction template, ensuring no structural overlap between train/test sets. It addresses the core scientific hypothesis: **real** spectroscopic data contains independent predictive signal beyond molecular structure.

**Critical Constraint**: The project **strictly prohibits** the use of simulated, synthetic, or deterministic spectra generated from SMILES. All spectral inputs must be **real experimental measurements** from verified open datasets. If a sufficient number of verified paired samples (SMILES + Real Spectrum + Yield) cannot be assembled, the project will pivot to a **Qualitative Architecture Validation** mode using the available small real dataset, or generate a **Data Insufficiency Report** if no real paired data exists. This ensures the validity of the "independent signal" hypothesis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `scikit-learn`, `rdkit`, `pandas`, `pyyaml`, `datasets` (Hugging Face), `matplotlib`, `seaborn`.  
**Storage**: Local file system (`data/`, `src/`, `state/`), Parquet/CSV for datasets.  
**Testing**: `pytest` with `coverage` for unit tests; `pytest` integration tests for pipeline steps.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM).  
**Project Type**: Scientific computing pipeline / Machine Learning research prototype.  
**Performance Goals**: Complete full training/evaluation cycle (including data ingestion, preprocessing, model training, and analysis) within 6 hours on CPU.  
**Constraints**: Memory footprint < 7 GB RAM; Disk usage < 14 GB; No local GPU; Strict adherence to template-based splitting to prevent leakage.  
**Scale/Scope**: Dataset size limited to what fits in RAM or can be streamed; model architecture simplified (e.g., 2-3 attention heads, smaller hidden dimensions) to fit CPU constraints.

> **Note on Dataset Fit**: The spec requires paired SMILES, spectra, and conditions. Verified datasets in the input block provide SMILES (USPTO, ZINC, ChEMBL) and isolated NMR/IR samples (NMR_demo, MolSpectra). **No single verified dataset contains all three for the same reaction instance.**
> **Strategy**: The project will attempt to merge verified sources (e.g., matching SMILES from USPTO with spectra from NMR_demo). **If the number of successfully merged, real paired samples is < 500, the quantitative hypothesis (H1) is dropped.** The project will then pivot to a **Qualitative Architecture Validation** using the small real dataset to test if the model can learn *any* signal, or generate a **Data Insufficiency Report** if N=0. This adheres to the "No Fabrication" principle.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action/Mapping |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `random_seed` pinned in `src/utils/seeds.py`; `requirements.txt` pins versions; CI runs `pytest` end-to-end. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs cited in `research.md` are from the verified block. **No simulated data is used.** If data is insufficient, the project reports "Data Insufficiency" or "Qualitative Validation" rather than fabricating metrics. |
| **III. Data Hygiene** | **PASS** | `data/raw/` preserved; `data/processed/` checksummed via `src/utils/checksums.py`; no in-place modifications. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in `paper/` trace to `data/processed/` artifacts and `src/` execution logs. |
| **V. Versioning** | **PASS** | Content hashes recorded in `state/projects/...yaml`; artifact hashes updated on every `data/` write. |
| **VI. Spectral Preprocessing** | **PASS** | `src/data/preprocessing.py` implements resampling to fixed grid (low-wavenumber to high-wavenumber, 0-10 ppm) and unit variance normalization. |
| **VII. Structural Baseline** | **PASS** | `src/models/baselines.py` implements ECFP4-only, Spectrum-only, and Condition-only baselines for comparison. |

## Project Structure

### Documentation (this feature)
```text
specs/001-predict-reaction-yields-from-spectra/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Design Artifacts (Inputs)
    ├── dataset.schema.yaml
    ├── model_output.schema.yaml
    └── experiment_config.schema.yaml
```

### Source Code (repository root)
```text
src/
├── __init__.py
├── cli/
│   └── main.py          # Entry point for pipeline execution
├── data/
│   ├── ingestion.py     # Download/verify datasets
│   ├── preprocessing.py # Resampling, normalization, template splitting
│   └── loaders.py       # PyTorch Dataset/DataLoader wrappers
├── models/
│   ├── attention_net.py # Multi-head attention model
│   └── baselines.py     # Fingerprint/Spectrum/Condition only models
├── utils/
│   ├── seeds.py         # RNG pinning
│   ├── validators.py    # Schema validation, leakage checks
│   └── checksums.py     # Data integrity hashing
├── eval/
│   ├── metrics.py       # RMSE, MAE, R², t-tests
│   └── interpretability.py # Attention heatmaps, permutation tests
├── config/
│   └── default.yaml     # Hyperparameters (LR, batch size, epochs)
└── constants.py         # Spectral grid definitions

tests/
├── unit/
│   ├── test_preprocessing.py
│   └── test_models.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py

data/
├── raw/                 # Downloaded raw files (checksummed)
├── processed/           # Split, resampled, normalized data
└── artifacts/           # Manifests, leakage reports, logs

state/
└── projects/PROJ-165-.../
    └── artifact_hashes.yaml
```

**Structure Decision**: Single-project structure selected to minimize overhead. The `src/` hierarchy separates data, model, and evaluation logic clearly. `data/` is strictly read-only for raw, write-only for processed. `state/` tracks metadata.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Multi-modal Attention** | Required to isolate spectral signal from structural signal (SC-001). | Concatenated MLP would not allow per-channel attention weights needed for interpretability (SC-003). |
| **Template-based Splitting** | Required to prevent leakage (FR-002, US-1). | Random split would leak reaction templates, invalidating generalizability claims. |
| **Real Data Only** | Required to test "independent signal" hypothesis validly. | Simulated spectra would create a tautological relationship with fingerprints, invalidating the hypothesis. |

## Development & Linting
- **Linting**: `pyproject.toml` configures `ruff` and `black` for consistent code style.
- **CI**: GitHub Actions workflow runs `ruff check` and `black --check` on every PR.
- **Type Checking**: `mypy` is used for static type checking.

## Data Hygiene
- **Checksums**: `src/utils/checksums.py` generates and logs SHA-256 hashes for all files in `data/raw/`.
- **Logs**: `data/artifacts/ingestion_log.json` and `data/validation_status.json` track data acquisition status.
- **Leakage Reports**: `data/artifacts/leakage_report.json` documents the template split verification.

## Data Sufficiency Gate (Updated)

Before training begins, the pipeline MUST execute a "Data Sufficiency Check":
1. Count the number of samples with **real** paired spectra and yields.
2. If `N == 0`:
   - Halt training.
   - Generate `data/artifacts/data_insufficiency_report.json`.
   - Output a qualitative analysis of the available data (e.g., "No real paired samples found; quantitative hypothesis H1 cannot be tested.").
3. If `0 < N < 500`:
   - **Perform Template Diversity Check**: Count unique reaction templates.
     - If unique templates < 3: Report "Insufficient Template Diversity for Splitting". Halt template-based splitting. Perform single-set qualitative analysis.
     - If unique templates >= 3: Proceed with **Qualitative Architecture Validation**. Train the model on the small real dataset (using a single set or minimal split if possible). Report performance metrics but explicitly state that quantitative claims (H1, H2) are not supported due to low power and potential lack of statistical independence.
   - *Decision*: The project defaults to **Path 1 (Real Data Merge)**. If the merge yields < 500 samples, the project pivots to Path 2 (Qualitative Validation or Report).

This gate ensures the project does not proceed with a scientifically invalid dataset or fabricate data.

## FR-010 Fallback Strategy
FR-010 requires validation against an independent experimental dataset.
- **Primary Path**: Use a separate, verified experimental dataset (e.g., a hold-out set from a different publication) if available.
- **Fallback Path**: If no independent dataset exists, perform a **Temporal Split** or **Source-Stratified Split** on the available real data (e.g., using older USPTO reactions for training and newer ones for validation) **ONLY IF** the source distribution is demonstrably different (e.g., different instrument, different year range with documented shift).
- **Not Applicable**: If no independent dataset exists and no valid temporal/source split can be demonstrated, FR-010 is marked as "Not Applicable" in the final report with a limitation note. The report will explicitly state that independent validation was not possible.
- **Reporting**: The final report will explicitly state which validation strategy was used.
