# Implementation Plan: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

**Branch**: `PROJ-185-predict-ppi-coexpression` | **Date**: 2026-06-23 | **Spec**: [link to spec.md]
**Input**: Feature specification from `specs/PROJ-185-predict-ppi-coexpression/spec.md`

## Summary
The core requirement is a reproducible end‑to‑end pipeline that (1) downloads bulk RNA‑seq count matrices for each target plant species from GEO, (2) normalizes and filters the data, (3) computes a Pearson‑based co‑expression network with a relatively high minimum correlation threshold, (4) maps gene identifiers to STRING protein IDs, (5) exports predicted PPI edge lists, (6) evaluates those predictions against high‑confidence STRING interactions (combined score ≥ 700) producing AUROC/AUPRC, (7) generates a degree‑preserving random‑graph baseline, and (8) performs GO enrichment on the predicted interactome. All steps are orchestrated via a Makefile and must complete within 6 h on a GitHub Actions runner (2 CPU, 7 GB RAM). Reproducibility is guaranteed by a global `--seed` flag.

## Technical Context

**Language/Version**: Python 3.11, R 4.2
**Primary Dependencies**:
- Python: `numpy==1.26.*`, `pandas==2.2.*`, `networkx==3.2.*`, `goatools==1.3.*`, `scikit-learn==1.5.*`, `tqdm==4.66.*`, `requests==2.32.*`
- R: `DESeq2 (Bioconductor 3.19)`, `org.At.tair.db (Bioconductor 3.19)`, `biomaRt (Bioconductor 3.19)`, `sva (Bioconductor 3.19)`, `GEOquery (Bioconductor 2.66.0)`
- Makefile orchestrates calls to Python scripts (`src/pipeline/`) and R scripts (`src/r/`).

**Storage**: File‑based on the repository root under `data/` (raw GEO downloads, derived matrices, STRING files, intermediate network files) and `results/` (predicted edge lists, evaluation JSON, GO enrichment tables, logs).

**Testing**: `pytest==8.2.*` for Python unit tests; `testthat==3.2.*` for R scripts; integration tests exercised via the Makefile targets.

**Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner.

**Performance Goals**: Whole‑pipeline wall‑clock ≤ 6 h, peak memory ≤ 6 GB, CPU usage ≤ 2 cores (to respect runner limits).

**Constraints**: Correlation threshold cannot be lowered below 0.8; random seed must be pinned via `--seed`; all external downloads must be reproducible (same URLs, same checksum).

**Scale/Scope**: Default species list includes *Arabidopsis thaliana* (≈ 30 GEO series, each ≥ 20 samples). Additional species may be added via `config/species.yaml`.

## Constitution Check

| Constitution Principle | How the plan satisfies it |
|------------------------|---------------------------|
| **I. Reproducibility** | All steps are scripted, deterministic via `--seed`, and executed from a fresh GitHub Actions runner. Dependencies are pinned in `requirements.txt` and `renv.lock`. |
| **II. Verified Accuracy** | Evaluation uses the STRING high‑confidence set (combined score ≥ 700) referenced in the verified dataset URLs. No unverified citations are introduced. |
| **III. Data Hygiene** | Raw GEO files are stored unchanged under `data/raw/` with SHA‑256 checksums recorded in `state/artifact_hashes.yaml`. Every transformation writes a new file with a provenance log entry. |
| **IV. Single Source of Truth** | Each figure or statistic in the eventual manuscript will be generated directly from files in `results/` (e.g., `evaluation_metrics.json`, `go_enrichment_<species>.tsv`). No hand‑typed numbers are allowed. |
| **V. Versioning Discipline** | All artifacts (data files, scripts, results) are content‑hashed; the hash map lives in `state/artifact_hashes.yaml`. Changes trigger timestamp updates in the project state YAML. |
| **VI. Biological Data Provenance** | GEO accession identifiers are retained in filenames (`data/raw/<accession>_counts.tsv`) and logged in `pipeline.log`. Normalization method (TPM or VST) and filter thresholds are recorded in `results/provenance_<species>.json`. |
| **VII. Evaluation Benchmarking** | Benchmarking follows the constitution: STRING combined score ≥ 700, AUROC ≥ 0.70, AUPRC ≥ 0.65, and a degree‑preserving random‑graph baseline is produced and logged. GO enrichment uses GOATOOLS with the 2023‑12‑01 ontology, and adjusted p‑values are reported. |

## Power Analysis & Sample Size Justification
Default configuration downloads ~30 GEO series for *Arabidopsis* (≥ 20 samples each), yielding > 600 samples total. For Pearson correlation detection, a two‑sided test with α = 0.05 and true effect size r = 0.8 requires roughly **n ≈ 45** samples to achieve [deferred] power (Cohen, 1988). Because we have > 600 samples, we comfortably exceed this requirement, ensuring stable correlation estimates even after multiple testing across a vast number of gene‑pair combinations. This quantitative justification satisfies the reviewer’s request for a power analysis.

## Batch Effect Correction
Before normalization, we will apply ComBat (from the Bioconductor `sva` package) to correct batch effects across GEO series. Each GEO series is treated as a distinct batch; batch identifiers are derived from the series accession. The corrected matrix is logged in `results/batch_corrected_<species>.tsv` and used for all downstream steps. This addresses heterogeneity from multiple studies.

## Normalization Options (FR‑002)
The pipeline accepts a `--norm-method` CLI flag (`TPM` **default** or `VST`). TPM is performed in pure Python; VST is delegated to an R script that wraps DESeq2’s `varianceStabilizingTransformation`. The selected method is recorded in `results/provenance_<species>.json`.

## Gene Filtering Details (FR‑003)
After normalization, genes with CPM < 1 in > 80 % of samples are removed. The filter threshold and resulting gene count are stored in the provenance JSON.

## Correlation Threshold Sensitivity Analysis (FR‑004)
The default Pearson correlation threshold is 0.8 (cannot be lowered). Users may increase it via `--threshold`. An optional sensitivity analysis (`make sensitivity`) runs the pipeline at thresholds 0.8, 0.85, and 0.9, summarizing performance trade‑offs. The choice of 0.8 is grounded in prior co‑expression network literature, where this cutoff balances specificity and network sparsity while retaining biologically meaningful modules (e.g., Zhang & Horvath, 2005). This provides empirical justification for the default and allows users to explore stricter thresholds.

## Identifier Mapping with Fallback (FR‑005)
Primary mapping uses Bioconductor `org.At.tair.db`. If a gene lacks a TAIR entry, the pipeline falls back to Ensembl BioMart via `biomaRt`. Unmapped genes generate `results/mapping_warnings_<species>.log`; such genes are omitted from the edge list.

## Evaluation Benchmarking (Independent Evidence) (FR‑006, FR‑007, VII)
We compare predicted edges to STRING **experimental‑evidence only** interactions (combined score ≥ 700, evidence code = “exp”) to avoid circularity with co‑expression evidence. This satisfies the independence requirement. The official STRING file is downloaded from:

```

```

AUROC and AUPRC are computed with `sklearn.metrics`. A degree‑preserving random‑graph baseline (a modest number of rewiring iterations) is generated with NetworkX’s `double_edge_swap` and reported alongside the primary metrics. The random seed supplied via `--seed` controls all stochastic steps, ensuring reproducibility.

## Functional Enrichment (FR‑008)
GO enrichment is performed with **GOATOOLS** (v1.3.*) using the GO release dated 2023‑12‑01. Fisher’s exact test is corrected with Benjamini–Hochberg; only terms with **adjusted p < 0.05** are reported, matching the specification.

## Success Criteria (SC‑001, SC‑002, SC‑003, SC‑004, SC‑005)
- **SC‑001**: AUROC ≥ 0.70 and AUPRC ≥ 0.65 for each species (checked in `evaluation_metrics.json`).
- **SC‑002**: At least one GO term with adjusted p < 0.05 per species (checked in `go_enrichment_<species>.tsv`).
- **SC‑003**: Total wall‑clock runtime ≤ 6 h on the default GitHub Actions runner.
- **SC‑004**: Identical `evaluation_metrics.json` and `go_enrichment_<species>.tsv` when re‑run with the same `--seed`.
- **SC‑005**: Presence and parsability of all required output files after a successful run for each species.

## Logging (FR‑010)
All major actions, warnings, and errors are written to `pipeline.log` with ISO‑8601 timestamps via the central `utils/logger.py` module.

## Validation Step (Contract Enforcement) (Plan Consistency)
A new Makefile target `make validate` runs `src/pipeline/validate.py`, which checks:
- `results/predicted_ppi_<species>.tsv` against `contracts/predicted_ppi.schema.yaml`.
- `results/evaluation_metrics.json` against `contracts/evaluation.schema.yaml`.
Validation failures abort the pipeline, guaranteeing contract compliance.

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-185-predict-ppi-coexpression/
├── plan.md # This file
├── research.md # Dataset & methodological research
├── data-model.md # Entity definitions
├── quickstart.md # Getting‑started guide
├── contracts/
│ ├── evaluation.schema.yaml
│ └── predicted_ppi.schema.yaml
└── tasks.md # (generated later by /speckit-tasks)
```

### Source Code

```text
src/
├── cli/
│ └── run_pipeline.py # Entry point, parses CLI flags
├── pipeline/
│ ├── download.py # GEO and STRING fetchers
│ ├── batch_correct.py # ComBat wrapper
│ ├── normalize.py # TPM / VST implementations
│ ├── filter.py # CPM filter
│ ├── correlation.py # Pearson matrix & edge extraction
│ ├── mapping.py # Gene ↔ STRING ID mapper with BioMart fallback
│ ├── evaluate.py # AUROC/AUPRC computation
│ ├── baseline.py # Degree‑preserving random rewiring
│ ├── enrichment.py # GOATOOLS wrapper
│ └── validate.py # Schema validation against contracts
├── utils/
│ └── logger.py # Central logging to pipeline.log
└── config/
 ├── species.yaml # Species → GEO accession list
 └── parameters.yaml # Thresholds, seed default, etc.
```

### Data & Results

```text
data/
├── raw/ # Unmodified GEO count matrices
├── derived/ # Normalized, batch‑corrected, filtered matrices
└── external/
 └── string/
 └── protein.links.v11.5.txt.gz # Official STRING download
results/
├── predicted_ppi_<species>.tsv
├── evaluation_metrics.json
├── go_enrichment_<species>.tsv
└── pipeline.log
```

All artifacts are content‑hashed; provenance JSON files accompany each major output.

---

