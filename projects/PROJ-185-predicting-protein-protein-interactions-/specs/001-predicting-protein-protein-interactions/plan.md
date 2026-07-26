# Implementation Plan: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

**Branch**: `PROJ-185-predict-ppi-coexpression` | **Date**: 2026‑07‑25 | **Spec**: [spec.md](../spec.md)
**Input**: Feature specification from `/specs/PROJ-185-predict-ppi-coexpression/spec.md`

## Summary
Develop a reproducible, CI‑compatible pipeline that (1) downloads publicly available *Arabidopsis thaliana* (and optionally other plant) RNA‑seq count matrices from NCBI GEO, (2) normalizes and filters the data, (3) builds a high‑threshold (r ≥ 0.80, never < 0.75) co‑expression network, (4) maps gene IDs to STRING protein IDs, (5) exports undirected edge lists per species, (6) evaluates the predictions against STRING high‑confidence interactions while generating a degree‑preserving random‑graph baseline, (7) performs GO enrichment on the predicted interactome, (8) assembles per‑species and aggregate reports, and (9) runs comprehensive schema‑validation and logging checks. All steps are orchestrated by a Makefile and satisfy every FR/SC listed in the spec.

## Technical Context
| Item | Detail |
|------|--------|
| **Language / Version** | Python 3.11 (primary), R 4.2 (via `rpy2` for DESeq2) |
| **Primary Dependencies** | `pandas`, `numpy`, `scipy`, `statsmodels`, `networkx`, `goatools`, `biopython`, `pybiomart`, `bioconductor-org.At.tair.db` (via `rpy2`), `scikit‑learn`, `click`, `tqdm`, `pytest`, `ruff`, `black`, `pyproject‑toml` |
| **Storage** | Flat files under `data/` (raw GEO matrices, STRING file, intermediate TSV/TSV.GZ) |
| **Testing** | `pytest` + `pytest‑cov`; schema validation via `jsonschema` |
| **Target Platform** | Linux (Ubuntu) GitHub Actions runner (multi‑core CPU, several GB RAM) |
| **Constraints** | Correlation threshold ≥ 0.75; total retained samples per species ≥ 50; gene set ≤ 5 000 after variance‑based selection |
| **Scale / Scope** | Default species: *Arabidopsis thaliana* (≥ 50 samples). Extensible to additional plant species via `species.yaml`. |

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | All random processes are seeded via `--seed`; `pipeline.log` records seed, command line, and software versions; the Makefile fully automates the workflow; CI script (`.github/workflows/ci.yml`) runs `make all` on a fresh runner. |
| **II. Verified Accuracy** | All external citations (e.g., STRING evidence‑channel exclusion, co‑expression literature) will be validated by the Reference‑Validator Agent before PR merge. |
| **III. Data Hygiene** | Raw GEO files are stored under `data/raw/` with SHA‑256 checksums recorded in `state/artifact_hashes.yaml`. No in‑place mutation; each transformation writes a new file with a provenance header. |
| **IV. Single Source of Truth** | Every statistic in the final report is derived from a single source file (e.g., `raw_correlations_<species>.tsv.gz` for AUROC; `go_enrichment_<species>.tsv` for GO terms). Derived numbers are never hand‑typed. |
| **V. Versioning Discipline** | All artifacts (code, data, schemas) are tracked with content hashes; any change updates the project state file. |
| **VI. Biological Data Provenance** | GEO accession IDs are retained in file names (`GSEXXXXX_series.tsv`) and logged; normalization method and parameters are recorded in `metadata/<species>_norm.json`. |
| **VII. Evaluation Benchmarking** | Evaluation follows the exact STRING high‑confidence definition (score ≥ 700, co‑expression channels excluded) and reports AUROC, AUPRC, precision@K=1000, F1, and a degree‑preserving random‑graph baseline with `baseline_p`. GO enrichment uses Fisher’s exact test + Benjamini‑Hochberg. |

## Phase Mapping & Work Breakdown (covers every FR/SC)

| Phase | FR(s) addressed | Core Tasks (mapped to Make targets) |
|-------|----------------|--------------------------------------|
| **Phase 1 – Data Acquisition** | FR‑001, FR‑047 | `make download` → GEO series list per species → skip series < 30 samples → abort if total < 50. |
| **Phase 2 – Normalization & Filtering** | FR‑002, FR‑003, FR‑014 | `make normalize` → DESeq2 VST *or* TPM; CPM filter; batch‑effect correction (ComBat) or SVA fallback; **Batch‑Effect QC**: run PCA on corrected data, compute variance explained by batch, log to `pipeline.log`; abort if residual batch variance > 5 % (new diagnostic). |
| **Phase 3 – Correlation Computation** | FR‑004, FR‑020, FR‑025, FR‑045 | `make correlate` → block‑wise Pearson (or Spearman for TPM) on ≤ 5 000 genes; compute *p‑value* for each correlation; adjust p‑values with Benjamini‑Hochberg (FDR); write `raw_correlations_<species>.tsv.gz` with columns `gene_id_1`, `gene_id_2`, `correlation`, `p_value`, `adjusted_p_value`; compute bootstrap confidence intervals at a conventional confidence level; retain edges only if lower CI ≥ threshold **and** (optional `--fdr` flag) `adjusted_p_value` ≤ 0.05. |
| **Phase 4 – Identifier Mapping** | FR‑005 | `make map_ids` → map TAIR/Ensembl IDs to STRING protein IDs; log unmapped genes (`mapping_warnings_<species>.log`). |
| **Phase 5 – Edge Selection & Thresholding** | FR‑004, FR‑045, FR‑011, FR‑013, FR‑012 | `make select_edges` → filter `raw_correlations` by chosen threshold (default 0.80, CLI enforces ≥ 0.75) **and** (if `--fdr` used) adjusted p‑value ≤ 0.05; write `predicted_ppi_<species>.tsv`; **Validate** against `contracts/predicted_ppi.schema.yaml` *and* `contracts/predicted_edges.schema.yaml`. |
| **Phase 6 – Evaluation** | FR‑006, FR‑007, FR‑016, FR‑032, FR‑018, FR‑019, FR‑012, FR‑048 | `make evaluate` → score all gene‑pair correlation scores against STRING high‑confidence set (exclude co‑expression evidence); generate balanced negative set; compute **AUROC**, **AUPRC**, **precision@K=1000**, **F1** on balanced set; generate degree‑preserving random‑graph baseline (a number of swaps proportional to the number of edges); compute baseline AUROC/AUPRC and `baseline_p`; **Pilot benchmark**: run held‑out GEO series for each species (or a second species when available) → store `pilot_validation_<species>.json` and cite in construct‑validity paragraph. |
| **Phase 7 – Functional Enrichment** | FR‑008, FR‑023, FR‑024, FR‑022 | `make enrich` → GOATOOLS Fisher test + BH correction on genes in predicted PPIs; write `go_enrichment_<species>.tsv`; **Validate** against `contracts/go_enrichment.schema.yaml`. |
| **Phase 8 – Reporting & Summary** | FR‑021, FR‑028, FR‑030, FR‑034, FR‑035, FR‑010, FR‑026 | `make summary` → assemble `summary_<species>.txt` (edge count, evaluation metrics, top GO terms, construct‑validity paragraph citing pilot results); `make final_report` → aggregate per‑species summaries; **Validate** `pipeline.log` against `contracts/pipeline_log.schema.yaml` after each target (`validate_log`); `make verify` runs all schema checks (edges, evaluation, GO, threshold sensitivity, log). |
| **Verification (cross‑cutting)** | FR‑017, FR‑013, FR‑019, FR‑030, FR‑034, FR‑035, FR‑004, FR‑045 | `make verify` → schema validation, checksum integrity, reproducibility assertions (identical seeds → identical checksums). |

### Success‑Criteria Mapping
| SC | Where verified |
|----|----------------|
| SC‑001 | `evaluation_metrics.json` AUROC ≥ 0.70 & AUPRC ≥ 0.65 (checked by CI). |
| SC‑002 | At least one GO term with adjusted p < 0.05 in `go_enrichment_<species>.tsv`. |
| SC‑003 | CI runtime log reports total wall‑clock ≤ 6 h. |
| SC‑004 | Re‑run with identical `--seed` → identical output file checksums (validated by `make verify`). |
| SC‑005 | `make verify` ensures presence & parsability of all required files. |
| SC‑006 | All schema validations (`predicted_ppi`, `evaluation`, `threshold_sensitivity`, `pipeline_log`, `go_enrichment`) must pass. |

## Timeline (CI‑friendly)
| Week | Milestone |
|------|-----------|
| 1 | Scaffold repo, CI workflow, environment files, schema definitions. |
| 2 | Implement Phase 1 & Phase 2 (download, normalization, batch‑effect QC). |
| 3 | Implement Phase 3 (streaming correlation, bootstrap CI, FDR) + Phase 4 (ID mapping). |
| 4 | Implement Phase 5 (edge selection, schema validation). |
| 5 | Implement Phase 6 (evaluation, baseline, multi‑metric, pilot benchmark). |
| 6 | Implement Phase 7 (GO enrichment) + Phase 8 (summary, final report, log validation). |
| 7 | Full end‑to‑end CI run, performance tuning, documentation, final review. |

---


## projects/PROJ-185-predicting-protein-protein-interactions-/specs/001-predicting-protein-protein-interactions/research.md===
# Research: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

## Dataset Strategy

| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| **RNA‑seq counts** | NCBI GEO (public) | `datasets.load_dataset("geo", data_dir="data/raw", split="train", streaming=False)` via `geo-downloader` CLI | Series list supplied in `species.yaml`. Series with < 30 samples are omitted (FR‑043). |
| **STRING protein‑protein interactions** | STRING (v11.5) | Direct download from verified HuggingFace parquet: ` | Only edges with combined score ≥ 700 *and* without evidence channels `coexpression`, `transcriptomics`, `gene_expression` are retained (FR‑006). |
| **GO ontology** | GO (released via GOATOOLS at runtime) | Automatic download by GOATOOLS (`goatools.obo_parser.GODag`) | No external URL needed; GOATOOLS caches the OBO file. |

*No other external datasets are required.* All downloads are fully scriptable on a fresh GitHub Actions runner.

## Methodological Decisions & Rationale

| Decision | Rationale | Compute Placement |
|----------|-----------|-------------------|
| **Normalization** | Default VST (DESeq2) preserves variance for count data; TPM option supported for compositional data (FR‑002). | CPU (R via `rpy2` runs on 2 cores). |
| **Correlation** | Pearson for VST, Spearman for TPM (FR‑004). Block‑wise streaming to keep RAM < 6 GB. | CPU – pure NumPy/SciPy. |
| **Threshold** | Default 0.80; CLI enforces lower bound 0.75 (FR‑012, T012). | CPU – enforced in `run_pipeline.py`. |
| **Batch‑effect correction** | ComBat (limma) when > 1 GEO series; fallback to SVA if metadata missing (FR‑014). **Batch‑Effect QC**: after correction, PCA is performed, variance explained by batch is computed, and if residual batch variance > 5 % the pipeline aborts (new diagnostic). | CPU – R implementation via `rpy2`. |
| **Multiple‑testing correction** | Correlation *p*‑values are adjusted with Benjamini‑Hochberg FDR; an optional `--fdr` flag can restrict edges to adjusted *p* ≤ 0.05, reducing false positives (addresses methodology‑6a3d3df5). | CPU – `statsmodels.stats.multitest`. |
| **Negative sampling** | Uniform sampling from complement of STRING high‑confidence set, size = |positive| (FR‑032). | CPU – `numpy.random`. |
| **Random‑graph baseline** | Degree‑preserving edge rewiring (on the order of |E| swaps) (FR‑007). | CPU – NetworkX. |
| **Evaluation metrics** | Primary: AUROC, AUPRC. Additional: precision@K=1000, F1 on the balanced subset, PR‑curve (addresses methodology‑5465e67e). | CPU – `sklearn.metrics`. |
| **Pilot benchmark** | Held‑out GEO series per species (or a second representative plant species) not used for model building; compute precision ≥ 0.60, recall ≥ 0.40 for default threshold (FR‑048). Results stored in `pilot_validation_<species>.json` and cited in construct‑validity paragraph for each species (addresses methodology‑d150c1da). | CPU – same pipeline, separate config. |
| **Sensitivity analysis** | Evaluate thresholds across a low‑to‑high range (spanning from lower to higher values) (FR‑025). | CPU – repeated correlation filtering. |
| **Power & Multiple‑testing** | Minimum 50 samples per species (FR‑001) gives > 80 % power for a single correlation r = 0.8 (Cohen, 1992). Because millions of tests are performed, we complement this with bootstrap confidence intervals and FDR control to mitigate inflated false‑positive rates (addresses methodology‑09d0cdf1). | CPU – bootstrap implementation. |
| **GPU Escape Hatch** | None required – all steps are fully tractable on CPU within a practical time budget. No GPU offload planned. |

## Statistical Rigor

* **Multiple‑testing** – GO enrichment p‑values corrected via Benjamini‑Hochberg (FR‑008). Correlation p‑values also FDR‑adjusted (new step).
* **Power justification** – Minimum 50 samples per species (FR‑001) ensures > 80 % power to detect a true Pearson r = 0.8 at α = 0.05 (Cohen, 1992). This is documented in `metadata/power_analysis.txt`. Because millions of pairwise tests are performed, we additionally use bootstrap confidence intervals and FDR control to protect against false discoveries (methodology‑09d0cdf1).
* **Causal inference** – All claims are associational; co‑expression is not assumed causal (Constitution Principle VII).
* **Measurement validity** – DESeq2 VST and TPM are standard; STRING high‑confidence edges are experimentally curated.
* **Collinearity** – Edge list is undirected; no regression on correlated predictors, so collinearity is not an issue.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient GEO samples (< 50) | Abort (FR‑047) | Provide fallback species list; log clear error. |
| STRING file format change | Evaluation failure | Pin to specific STRING release version (v11.5) and verify header fields at download time. |
| Memory blow‑up for a substantial number of genes | > 6 GB RAM | Stream correlations in large gene blocks; use `np.memmap` for intermediate storage. |
| Batch‑effect metadata missing | SVA fallback may be slower | Log warning, proceed with SVA; benchmark time budget. |
| False‑positive inflation from multiple testing | Reduced precision | Apply Benjamini‑Hochberg FDR to correlation *p*‑values; optional `--fdr` edge filter. |
| AUROC optimism in imbalanced data | Misleading performance | Report precision@K=1000, F1, and PR‑curve alongside AUROC/AUPRC. |

---


## projects/PROJ-185-predicting-protein-protein-interactions-/specs/001-predicting-protein-protein-interactions/data-model.md===
# Data Model: Predict Protein‑Protein Interactions from Co‑expression Networks

## Core Entities

| Entity | Attributes | Description |
|--------|------------|-------------|
| **RNASeqSample** | `accession_id` (string), `species` (string), `raw_counts_path` (path), `metadata` (JSON) | One GEO series (after filtering for ≥ 30 samples). |
| **Gene** | `gene_id` (TAIR or Ensembl), `cpm` (float), `variance` (float), `string_protein_id` (string, optional) | After CPM filtering and variance selection. |
| **RawCorrelation** | `gene_id_1`, `gene_id_2`, `correlation` (float), `p_value` (float), `adjusted_p_value` (float) | Produced by block‑wise correlation; stored in `raw_correlations_<species>.tsv.gz`. |
| **ProteinCorrelation** | `protein_id_1`, `protein_id_2`, `correlation` (float) | After identifier mapping; used for edge export. |
| **PredictedEdge** | `protein_id_1`, `protein_id_2`, `correlation` (float) | Rows of `predicted_ppi_<species>.tsv`. |
| **EvaluationMetric** | `species`, `auroc`, `auprc`, `baseline_auroc`, `baseline_auprc`, `baseline_p` (float) | Stored in `evaluation_metrics.json`. |
| **GOEnrichmentRecord** | `go_id`, `description`, `raw_p`, `adjusted_p`, `gene_count` | Rows of `go_enrichment_<species>.tsv`. |
| **ThresholdSensitivityRecord** | `threshold`, `edge_count`, `auroc`, `auprc` | Rows of `threshold_sensitivity_<species>.tsv`. |
| **PipelineLogEntry** | `timestamp`, `level`, `message`, `schema_version`, `seed`, `command` | JSON‑Line entries in `pipeline.log`. |

## Relationships

* Each **RNASeqSample** belongs to a **Species** (captured in `species.yaml`).
* **Gene** objects are derived from the union of all samples for a species after CPM filtering.
* **RawCorrelation** is computed for every unordered pair of retained **Gene** objects.
* **ProteinCorrelation** is a filtered view of **RawCorrelation** where both genes have a valid `string_protein_id`.
* **PredictedEdge** ⊆ **ProteinCorrelation** (edges satisfying the correlation threshold and, optionally, the FDR filter).
* **EvaluationMetric** consumes the full set of **ProteinCorrelation** scores plus the STRING positive/negative label sets.
* **GOEnrichmentRecord** is computed from the set of genes appearing in **PredictedEdge** against the background gene universe.

## Storage Layout (relative to project root)

```
data/
├── raw/ # GEO series TSV/CSV files (unchanged)
├── processed/
│ ├── normalized/<species>.tsv
│ ├── raw_correlations_<species>.tsv.gz
│ ├── predicted_ppi_<species>.tsv
│ ├── go_enrichment_<species>.tsv
│ └── threshold_sensitivity_<species>.tsv
├── external/
│ └── string_highconf.parquet # verified STRING dataset (see research.md)
└── checksums.yaml # SHA‑256 hashes for all raw files
logs/
└── pipeline.log
results/
├── evaluation_metrics.json
├── summary_<species>.txt
└── final_report.txt
state/
└── artifact_hashes.yaml
```

All TSV files are UTF‑8, tab‑delimited, with a header row. Gzipped files are streamed with `gzip.open(..., 'rt')`.

---


## projects/PROJ-185-predicting-protein-protein-interactions-/specs/001-predicting-protein-protein-interactions/quickstart.md===
# Quickstart: Predict Plant Protein‑Protein Interactions from Co‑expression

These instructions assume a fresh GitHub Actions runner (or a local Linux environment with similar resources).

## 1. Clone the repository
```bash
git clone
cd ppi-coexpression
```

## 2. Set up the Python environment
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt # pins all Python deps
```

## 3. Set up the R environment (DESeq2, org.At.tair.db)
```bash
Rscript scripts/install_bioc.R # installs DESeq2, limma, sva, org.At.tair.db
```

## 4. Configure species and parameters
Edit `config/species.yaml` to list GEO series per species (default includes a few *Arabidopsis* series).
Edit `config/parameters.yaml` to change any defaults (e.g., `threshold: 0.80`, `seed: 42`, `fdr: true` to enable FDR‑filtered edges).

## 5. Run the full pipeline
```bash
make all
```
* This executes the following Make targets in order: `download → normalize → correlate → map_ids → select_edges → evaluate → enrich → summary → final_report`.
* All major actions are logged to `logs/pipeline.log` (JSON‑Line format) and validated against the corresponding schemas after each step (including `pipeline.log`, `predicted_ppi_*.tsv`, `go_enrichment_*.tsv`, `evaluation_metrics.json`, `threshold_sensitivity_*.tsv`).

## 6. Verify outputs
```bash
make verify
```
* Runs `jsonschema` validation for `predicted_ppi_<species>.tsv`, `evaluation_metrics.json`, `go_enrichment_<species>.tsv`, `threshold_sensitivity_<species>.tsv`, and `pipeline.log`.
* Aborts with a clear error if any file violates its contract (fulfilling FR‑013, FR‑019, FR‑030, FR‑034).

## 7. Inspect results
```bash
# Predicted edges
ls data/processed/predicted_ppi_*.tsv

# Evaluation metrics
cat results/evaluation_metrics.json

# GO enrichment
head data/processed/go_enrichment_*.tsv

# Summary report
cat results/summary_*.txt
cat results/final_report.txt
```

## 8. Re‑run with a different threshold (example)
```bash
make all THRESHOLD=0.85
```
* The threshold is validated to be ≥ 0.75; lower values will abort with a clear error (FR‑012).

## 9. Clean intermediate files (optional)
```bash
make clean
```
* Removes all `data/processed/*` and intermediate logs but retains raw GEO downloads and final reports.

---


## projects/PROJ-185-predicting-protein-protein-interactions-/specs/001-predicting-protein-protein-interactions/contracts/predicted_ppi.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "Predicted PPI Edge List"
description: "Schema for the predicted protein‑protein interaction edge list produced by the pipeline."
type: object
required:
 - protein_id_1
 - protein_id_2
 - correlation
properties:
 protein_id_1:
 type: string
 description: "STRING protein identifier for the first node."
 protein_id_2:
 type: string
 description: "STRING protein identifier for the second node."
 correlation:
 type: number
 format: float
 description: "Pearson (or Spearman) correlation coefficient between the two proteins."
 minimum: -1.0
 maximum: 1.0
 method:
 type: string
 enum: ["pearson", "spearman"]
 description: "Correlation method used."
 bootstrap_ci_lower:
 type: number
 description: "Lower bound of the bootstrap confidence interval at a conventional confidence level for the correlation (optional)."
 bootstrap_ci_upper:
 type: number
 description: "Upper bound of the bootstrap confidence interval (optional)."
additionalProperties: false
example:
 protein_id_1: "AT1G01010"
 protein_id_2: "AT2G02020"
 correlation: 0.82
 method: "pearson"