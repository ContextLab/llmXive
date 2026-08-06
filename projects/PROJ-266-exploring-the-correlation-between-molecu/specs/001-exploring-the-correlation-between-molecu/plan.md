# Implementation Plan: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

**Branch**: `001-molecular-flexibility-permeability` | **Date**: 2024-01-15 | **Spec**: `specs/001-molecular-flexibility-permeability/spec.md`
**Input**: Feature specification from `/specs/001-molecular-flexibility-permeability/spec.md`

## Summary

This project implements a computational chemistry pipeline to investigate the correlation between molecular flexibility (quantified via normal‑mode‑analysis‑derived torsional variance) and Caco‑2 membrane permeability (logPapp). The system retrieves raw data from ChEMBL, validates records, generates 3D conformers using RDKit, performs normal‑mode analysis with **PyVib** to derive torsional variance, computes flexibility descriptors (with bond/angle metrics used only for diagnostic purposes), validates conformer ensemble convergence via an iterative stability loop, and conducts statistical analyses controlling for known confounders, protocol heterogeneity, and molecular size. Results are evaluated with robust regression (Huber/Ridge) and k-fold cross-validation, and visualizations are produced for publication.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `rdkit`, `pyvib`, `pandas`, `numpy`, `scikit-learn`, `scipy`, `statsmodels`, `matplotlib`, `requests`, `datasets` (Hugging Face)
**Storage**: Local filesystem (`data/raw`, `data/processed`) with checksums recorded in `state/artifact_hashes` (SHA‑256).
**Testing**: `pytest` (contract tests for schema validation, unit tests for descriptor calculation).
**Target Platform**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, ≤6 h). All steps are CPU‑tractable; no GPU fallback is used.
**Project Type**: Computational Research Pipeline / CLI Tool
**Performance Goals**: Complete full pipeline (download → visualization) within 6 h on CPU; memory usage < 6 GB.
**Constraints**: No external API credentials; all datasets fetched programmatically; strict adherence to spec (FR‑001 – FR‑010).
**Scale/Scope**: Target a representative set of raw records (based on preliminary ChEMBL query), ≥ 500 valid after filtering, ≥ 450 molecules with successful NMA-derived descriptors and converged variance.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re‑check after Phase 1 design.*

- **I. Reproducibility**:
 - Random seeds (`seed = 42`) are pinned in all scripts (conformer generation, NMA, train/test splits).
 - External datasets are fetched via deterministic REST queries; raw data checksums are recorded in `state/artifact_hashes`.
 - No manual steps; `requirements.txt` pins versions.
 - **No GPU offload**: All steps are CPU-tractable to ensure reproducibility on a fresh GitHub Actions runner.

- **II. Verified Accuracy**:
 - Citations are validated by `code/validate_citations.py`, which invokes the Reference‑Validator Agent and enforces title‑overlap ≥ 0.7.
 - The validator runs immediately after data fetch and before analysis.

- **III. Data Hygiene**:
 - Raw data (`data/raw/`) is immutable; each transformation writes a new file under `data/processed/`.
 - Checksums are computed by `code/utils/checksum.py` and written explicitly to the `artifact_hashes` map in `state/projects/PROJ-266...yaml`.

- **IV. Single Source of Truth**:
 - Every figure/statistic traces back to a row in `data/processed/final_dataset.csv` and a block in `code/`.

- **V. Versioning Discipline**:
 - All artifacts carry content hashes; `state/projects/PROJ-266...yaml` is updated on change.

- **VI. Computational Method Transparency**:
 - RDKit generates 3D conformer ensembles (`EmbedMultipleConfs`).
 - **PyVib** performs normal‑mode analysis on the lowest‑energy conformer to compute vibrational frequencies; torsional variance (dihedral) is derived from these modes using the equipartition theorem (units rad²).
 - Bond and angle variances are computed for diagnostic purposes but excluded from predictive modeling.
 - Scripts and versions are recorded; seeds are deterministic.

- **VII. Statistical Rigor**:
 - Pearson/Spearman correlations with Benjamini‑Hochberg FDR correction.
 - Robust regression (HuberRegressor) and heteroscedasticity‑consistent SEs are used; Ridge regression (alpha=1.0) is the fallback for VIF > 5.
 - K-fold cross-validation with reporting of mean R², RMSE, MAE.
 - All reported effects are flagged as associational.
 - Power analysis is performed upfront; results are flagged if N < 150 or MDES > 0.3.

## Project Structure

```text
specs/001-molecular-flexibility-permeability/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md # Auto‑generated execution manifest (Phase 6 output)
├── contracts/
│ ├── dataset.schema.yaml
│ ├── descriptor.schema.yaml
│ ├── analysis_output.schema.yaml
│ ├── correlation.schema.yaml
│ ├── output.schema.yaml
│ └── __init__.py
└──.gitkeep
```

```text
projects/PROJ-266-exploring-the-correlation-between-molecu/
├── code/
│ ├── requirements.txt
│ ├── fetch_data.py
│ ├── preprocess.py
│ ├── conformer_gen.py
│ ├── nma_analysis.py # PyVib wrapper
│ ├── descriptors.py
│ ├── analysis.py
│ ├── visualize.py
│ ├── run_pipeline.py # Orchestrator
│ ├── utils/
│ │ ├── checksum.py
│ │ └── logger.py
│ ├── validate_citations.py
│ └── main.py
├── data/
│ ├── raw/
│ └── processed/
├── tests/
│ └── contract/
│ └── test_dataset.py
└── state/
 └── projects/PROJ-266-exploring-the-correlation-between-molecu.yaml
```

## Phases & Tasks

| Phase | Description | Key Tasks (scripts) |
|-------|-------------|---------------------|
| **0** | **Research Design** – create `research.md` (this file) and `tasks.md`. | `tasks.md` generated from plan. |
| **1** | **Data Acquisition & Hygiene** – fetch, filter, checksum. | `fetch_data.py`, `preprocess.py`, `utils/checksum.py`. |
| **2** | **3D Conformer & NMA** – generate ensembles, validate convergence (iterative), run PyVib NMA. | `conformer_gen.py`, `nma_analysis.py`. |
| **3** | **Descriptor Calculation** – compute dihedral variance (primary), bond/angle variance (diagnostic only). | `descriptors.py`. |
| **4** | **Statistical Analysis** – power analysis, correlation, robust regression, protocol covariates, VIF, cross‑validation. | `analysis.py`. |
| **5** | **Visualization & Reporting** – produce PNG plots, export results. | `visualize.py`. |
| **6** | **Validation & Export** – run citation validator, write checksums to state YAML, generate `tasks.md`. | `validate_citations.py`, `utils/checksum.py`. |

## Compute Feasibility

- **CPU‑First**: All steps (RDKit conformer generation, PyVib NMA, statistical analysis) run comfortably on 2 CPU cores for ≤ 500 molecules using batch processing.
- **Memory Management**: Process molecules in batches; peak RAM < 5 GB.
- **No GPU**: Removed optional GPU offload to guarantee reproducibility on a fresh GitHub Actions runner.

## Data Strategy

| Dataset | Source URL | Load Method | Variables | Status |
|:--- |:--- |:--- |:--- |:--- |
| ChEMBL Caco‑2 | `https://www.ebi.ac.uk/chembl/api/data/assay.json?assay_type=Caco-2&standard_type=MEASUREMENT` | `requests` (REST) | SMILES, logPapp, MW, PSA, protocol metadata (lab_id, temperature, passage) | **Verified** |
| Fallback SMILES/Descriptors | ` | `datasets.load_dataset` | SMILES, RDKit descriptors (used only if API fails) | **Verified** |

*No gated datasets are used.*

## Success Criteria & Power Analysis

- **SC‑001** – Dataset completeness ≥ 83 % (≥ 500 / ≥ 600).
- **SC‑002** – Conformer/NMA success ≥ 90 % (≥ 450 / ≥ 500) AND convergence stability achieved.
- **SC‑003** – Correlation results include r, p, FDR‑q for dihedral variance only.
- **SC‑004** – Cross‑validation R² variance reported; VIF ≤ 5 or Ridge fallback applied.
- **SC‑005** – Total runtime ≤ 6 h on CPU; memory < 7 GB.
- **SC‑006** – Protocol heterogeneity count reported and modeled.
- **Power** – Prior to analysis, `statsmodels.stats.power.FTestPower` computes detectable effect size; if N < 150 or MDES > 0.3, the pipeline logs a "Limited Power" warning but proceeds.

## Tasks.md Generation

`run_pipeline.py` orchestrates the above phases and writes a deterministic `tasks.md` manifest that lists each script, its inputs, outputs, and checksum references. This satisfies the "Plan ↔ tasks" consistency requirement.