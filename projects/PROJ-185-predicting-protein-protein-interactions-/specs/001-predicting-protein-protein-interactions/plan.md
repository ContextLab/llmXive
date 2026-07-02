# Implementation Plan: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

**Branch**: `PROJ-185-predict-ppi-coexpression` | **Date**: 2026‑07‑01 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `specs/PROJ-185-predict-ppi-coexpression/spec.md`

## Summary
The pipeline will (1) download bulk RNA‑seq count matrices for each target plant species from GEO, (2) normalize (VST default; TPM optional with log‑transform) and filter low‑expression genes, (3) correct batch effects and adjust covariates (including a surrogate hidden‑batch correction when metadata are missing), (4) compute pairwise Pearson (mandatory) and optional Spearman correlations, (5) retain edges **only** with Pearson (or Spearman) coefficient ≥ 0.8 for *edge generation* (the threshold never goes below 0.8, satisfying FR‑004), (6) map gene IDs to STRING protein IDs, (7) output a validated edge list per species, (8) evaluate predictions against STRING high‑confidence interactions (AUROC, AUPRC) **using all raw correlation scores** (FR‑020), (9) perform a degree‑preserving random‑graph baseline, (10) conduct a **threshold‑sensitivity analysis** at 0.75, 0.80, 0.85 **only on the raw scores** (edges remain at 0.8), (11) run GO enrichment on the predicted interactome, and (12) produce reproducible summary reports. All steps are orchestrated by a Makefile and run within a ≤ 6 hour wall‑clock budget on a GitHub Actions free‑tier runner (2 CPU, ≈ a few GB RAM).

## Technical Context
- **Language/Version**: Python 3.11, R 4.2 (called via Rscript)  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `networkx`, `scikit-learn`, `goatools`, `pybiomart`, `biopython`, `rpy2`, `limma`/`sva` (R), `DESeq2`, `org.At.tair.db` (Bioconductor)  
- **Storage**: Flat files under `data/` and `results/` (TSV/JSON/YAML)  
- **Testing**: `pytest` for Python modules, `testthat` for R scripts, schema validation via `jsonschema`/`cerberus`  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Constraints**: CPU‑only, no GPU, correlation threshold never below 0.8 for edge generation, runtime ≤ 6 h.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random processes accept `--seed`; versions pinned in `requirements.txt`; external data fetched from the same canonical sources on each run. |
| II. Verified Accuracy | Citations (e.g., Zhang et al., Nat Commun. 2020) will be validated by the Reference‑Validator before inclusion. |
| III. Data Hygiene | Raw GEO files stored unchanged under `data/raw/`; checksums recorded in `state/...yaml`; every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | Every statistic in the summary report is derived directly from the TSV/JSON artifacts produced by the pipeline. |
| V. Versioning Discipline | All artifacts are content‑hashed; changes trigger updates to the project state file. |
| VI. Biological Data Provenance | GEO accession identifiers and version metadata retained in file names and provenance logs. |
| VII. Evaluation Benchmarking | Evaluation follows the exact STRING high‑confidence criteria (combined ≥ 700, co‑expression channel excluded) and reports baseline random‑graph performance and GO enrichment FDR‑corrected p‑values. |
| **Construct‑Validity Disclaimer** | High‑threshold co‑expression is used as an *associational* proxy for physical PPIs (supported by Zhang et al., Nat Commun.). The pipeline generates hypothesis sets, not definitive binding evidence. |

## Project Structure
```text
specs/PROJ-185-predict-ppi-coexpression/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── predicted_edges.schema.yaml
    ├── predicted_ppi.schema.yaml   # updated to match output column names
    ├── evaluation.schema.yaml
    ├── go_enrichment.schema.yaml
    ├── pipeline_log.schema.yaml
    ├── raw_correlations.schema.yaml
    └── threshold_sensitivity.schema.yaml
src/
├── config/
│   └── species_config.yaml          # GEO list, thresholds, flags
├── download/
│   └── fetch_geo.py                 # GEO downloader (GEOparse)
├── preprocess/
│   ├── normalize.py                 # TPM or DESeq2 VST
│   ├── filter_genes.py              # CPM filter
│   └── batch_correct.py             # ComBat / limma
├── covariate/
│   └── adjust_covariates.py         # regress out or surrogate PCA correction
├── correlation/
│   └── compute_corr.py              # Pearson / Spearman, bootstrap CI
├── mapping/
│   └── gene_to_string.py            # TAIR → STRING mapping
├── evaluation/
│   ├── evaluate_predictions.py
│   └── random_baseline.py
├── enrichment/
│   └── go_enrichment.py
├── summary/
│   └── generate_summary.py
├── verification/
│   └── verify_outputs.py            # schema validation after each target
└── Makefile
```

## Phase Overview & FR/SC Mapping
| Phase | Primary Tasks | FR(s) Addressed | SC(s) Addressed |
|-------|---------------|------------------|-----------------|
| **0. Setup** | Create virtualenv, install pinned deps, set `--seed`. | FR‑012, FR‑009, FR‑010 | SC‑003 |
| **1. Data Acquisition** | Download GEO series per species; checksum; abort if < 50 samples. | FR‑001, FR‑024, FR‑010 | SC‑003 |
| **2. Normalization & Filtering** | TPM (log2‑transform) **or** DESeq2 VST (default). Log a compositional‑bias warning if TPM is chosen. CPM < 1 in > 80 % samples removed. | FR‑002, FR‑003, FR‑010 | SC‑003 |
| **3. Batch‑Effect & Covariate Adjustment** | Detect multiple GEO series → ComBat; if metadata present → linear regression; **if metadata missing** → surrogate hidden‑batch correction via PCA (logged as warning). | FR‑014, FR‑022, FR‑010 | SC‑003 |
| **4. Gene‑to‑Protein Mapping** | Map TAIR IDs via `org.At.tair.db`; fallback to Ensembl BioMart; log unmapped genes. | FR‑005, FR‑010, FR‑013 | SC‑006 |
| **5. Correlation Computation** | Pairwise Pearson (mandatory) & optional Spearman; save `raw_correlations_<species>.tsv`; retain edges with **r ≥ 0.8** (threshold never below 0.8 for edge generation). | FR‑004, FR‑020, FR‑010, FR‑015 (optional bootstrap) | SC‑003 |
| **6. Bootstrap CI (optional)** | For the top set of edges, 200 resamples; flag non‑robust edges. | FR‑015, FR‑010 | SC‑003 |
| **7. Edge List Generation** | Apply threshold (and optional bootstrap filter) → `predicted_ppi_<species>.tsv` with columns `protein_id_1`, `protein_id_2`, `correlation`, `method`, optional CI fields. | FR‑011, FR‑010, FR‑013 | SC‑001, SC‑006 |
| **8. Schema Validation (Edge List)** | Validate `predicted_ppi_<species>.tsv` against `contracts/predicted_ppi.schema.yaml`. Abort on violation. | FR‑013, FR‑017 | SC‑005 |
| **9. Evaluation** | Score **all** raw correlation scores against STRING high‑confidence positives (≥ 700, excluding co‑expression channel). Sample a **balanced** negative set equal to the number of positives (or up to 10 × if positives are very few). Compute AUROC, AUPRC; bootstrap CIs (200 resamples). | FR‑006, FR‑016, FR‑018, FR‑019, FR‑010 | SC‑001 |
| **10. Random‑Graph Baseline** | Degree‑preserving rewiring (10 000 swaps per iteration) generates a null AUROC/AUPRC distribution; a one‑sample KS test yields `baseline_p`. | FR‑007, FR‑010 | SC‑001 |
| **11. Threshold Sensitivity** | Re‑evaluate **only for performance metrics** at thresholds 0.75, 0.80, 0.85 **using raw scores**, not altering the edge list (preserves FR‑004). Write `threshold_sensitivity_<species>.tsv`. | FR‑023, FR‑010 | SC‑001 |
| **12. GO Enrichment** | GOATOOLS Fisher’s exact test on genes in `predicted_ppi_<species>.tsv` versus filtered‑gene universe; BH correction; write `go_enrichment_<species>.tsv`. | FR‑008, FR‑010 | SC‑002 |
| **13. Summary Report** | Compile total edges, evaluation metrics, top‑10 GO terms into `summary_<species>.txt`. | FR‑021, FR‑010 | SC‑004 |
| **14. Verification** | Run `verification/verify_outputs.py` after each Make target; validate all contract‑bound files (predicted edges, raw correlations, evaluation JSON, GO enrichment TSV, threshold sensitivity TSV, pipeline log). Abort on failure. | FR‑017, FR‑019, FR‑010 | SC‑005 |
| **15. Clean (optional)** | Remove intermediate files while preserving raw GEO data and final artifacts. | FR‑009 | — |

All phases respect the 6‑hour wall‑clock limit by (i) chunked correlation computation, (ii) limiting bootstrap to a large number of edges, (iii) using efficient NumPy/Numba operations, and (iv) sampling negatives rather than enumerating the full pairwise space.

## Validation & Verification (New Section)
- **Edge List**: `predicted_ppi_<species>.tsv` → `contracts/predicted_ppi.schema.yaml`  
- **Raw Correlations**: `raw_correlations_<species>.tsv` → `contracts/raw_correlations.schema.yaml`  
- **Evaluation Metrics**: `evaluation_metrics.json` → `contracts/evaluation.schema.yaml`  
- **GO Enrichment**: `go_enrichment_<species>.tsv` → `contracts/go_enrichment.schema.yaml`  
- **Threshold Sensitivity**: `threshold_sensitivity_<species>.tsv` → `contracts/threshold_sensitivity.schema.yaml`  
- **Pipeline Log**: `pipeline.log` → `contracts/pipeline_log.schema.yaml`  

The `make verify` target invokes `verification/verify_outputs.py`, which loads each contract with `jsonschema` (or `cerberus` for TSV) and raises an error if any check fails, satisfying FR‑017 and SC‑005.

## Compute Feasibility on GitHub Actions
- **Memory**: Gene‑gene correlation matrix is computed in blocks (e.g., 5 000 × 5 000 chunks) to keep peak RAM ≤ 5 GB.  
- **CPU**: All heavy loops are vectorised; optional Numba JIT for speed.  
- **Runtime Estimate**:  
  - GEO download & QC: a brief, network‑bound duration.  
  - Normalization & filtering: a brief processing step.  
  - Correlation (full matrix for ≤ 5 000 genes): [deferred].  
  - Bootstrap (optional) + baseline rewiring: ≤ 60 min.  
  - Evaluation & GO enrichment: ≤ 30 min.  
  - Summary & verification: ≤ 10 min.  
  Total ≈ a few hours, well under the 6 h ceiling (SC‑003).  
- **No GPU**: All libraries used have pure‑CPU wheels; `torch` is **not** required.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient samples (< 50) after merging series | Pipeline abort (FR‑024) | Pre‑run sample count check; abort early with clear error. |
| Missing covariate metadata | Covariate adjustment skipped (no‑op) | Apply surrogate PCA‑based hidden‑batch correction; log warning. |
| Gene‑to‑STRING mapping failures | Unmapped genes omitted, warning logged (FR‑005) | Record unmapped IDs; continue with mapped subset. |
| High memory usage for large gene sets | Job OOM | Chunked correlation; limit to top‑most‑variable set of genes as needed (documented). |
| STRING file corruption | Abort with explicit error (FR‑006) | Verify MD5 checksum after download; abort on mismatch. |
| Imbalanced evaluation set | Inflated AUROC/AUPRC | Use balanced negative sampling (equal to positives, up to 10×) and report class‑balance statistics. |
| TPM compositional bias | Spurious correlations | Default to VST; if TPM chosen, log caution and apply log2‑transform; document limitation. |

---



