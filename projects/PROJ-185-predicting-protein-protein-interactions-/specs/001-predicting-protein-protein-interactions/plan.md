# Implementation Plan: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

**Branch**: `PROJ-185-predict-ppi-coexpression` | **Date**: 2026‑08‑03 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `/specs/PROJ-185-predict-ppi-coexpression/spec.md`

## Summary
The pipeline will (1) download publicly available Arabidopsis thaliana RNA‑seq count matrices from GEO, (2) normalize (VST or TPM), filter low‑expression genes, retain a substantial set of the most variable genes, (3) correct batch effects, (4) compute pairwise Pearson or Spearman correlations, (5) retain edges with r ≥ 0.80 (never below 0.75), (6) map gene IDs to STRING protein IDs, (7) output a TSV edge list per species, (8) evaluate the full correlation set against STRING high‑confidence interactions (combined ≥ 700, excluding co‑expression evidence channels) producing AUROC/AUPRC and a degree‑preserving random‑graph baseline, (9) perform GO enrichment on the predicted interactome, and (10) generate per‑species and final summary reports. All steps are orchestrated by a Makefile and are fully reproducible via a pinned random seed.

## Technical Context
- **Language/Version**: Python 3.11, R 4.2 (via `rpy2` where needed)  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `networkx`, `goatools`, `torch` (CPU‑only), `GEOparse`, `biopython`, `rpy2`, `DESeq2` (Bioconductor), `org.At.tair.db` (Bioconductor), `limma`, `sva`, `pyarrow` (for streaming HuggingFace datasets)  
- **Storage**: Files under `data/` (raw GEO series, processed matrices, STRING network) and `results/` (edges, scores, logs)  
- **Testing**: `pytest` + `pytest-jsonschema` for contract validation; `rpytest` for R scripts  
- **Target Platform**: Linux GitHub Actions runner (2 CPU, 7 GB RAM) – **CPU‑first**; no GPU required.  
- **Performance Goals**: End‑to‑end wall‑clock ≤ 6 h; memory ≤ 7 GB at any point.  
- **Constraints**: Correlation threshold ≥ 0.75, total samples per species ≥ 50, gene set ≤ 5 000.  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random processes accept `--seed`; `pipeline.log` records seed, command line, and software versions. |
| II. Verified Accuracy | All citations (e.g., Zhang et al., Nat Commun. 2020) will be validated by the Reference‑Validator before acceptance. |
| III. Data Hygiene | Raw GEO files are stored unchanged under `data/raw/`; each file is checksummed and the checksum recorded in `state/artifact_hashes.yaml`. |
| IV. Single Source of Truth | Every statistic in the final report is derived directly from a row in a validated output file (`evaluation_metrics.json`, `go_enrichment_*.tsv`, etc.). The **master_results.json** file aggregates all per‑species metrics and serves as the project‑wide SSoT artifact. |
| V. Versioning Discipline | All artifacts (code, data, schemas) are content‑hashed; changes update the project state file automatically. |
| VI. Biological Data Provenance | GEO accession identifiers are preserved in `data/metadata/`. Normalization steps are logged with provenance tags. |
| VII. Evaluation Benchmarking | STRING high‑confidence edges (combined ≥ 700, co‑expression evidence excluded) are the sole benchmark; AUROC/AUPRC targets are documented in SC‑001. |

## Project Structure
```
specs/PROJ-185-predict-ppi-coexpression/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── predicted_edges.schema.yaml
    ├── evaluation.schema.yaml
    ├── threshold_sensitivity.schema.yaml
    └── pipeline_log.schema.yaml

src/
├── config/
│   ├── species.yaml            # species‑to‑GEO accession list
│   └── parameters.yaml        # default thresholds, seed, etc.
├── data/
│   ├── raw/                    # GEO .tar files (unchanged)
│   ├── processed/              # normalized matrices, gene‑protein map
│   └── string/                 # STRING protein.links.v11.5.txt.gz
├── logs/
│   └── pipeline.log
├── results/
│   ├── raw_correlations_*.tsv.gz
│   ├── predicted_ppi_*.tsv
│   ├── evaluation_metrics.json
│   ├── go_enrichment_*.tsv
│   ├── threshold_sensitivity_*.tsv
│   └── summary_*.txt
├── utils/
│   ├── logger.py
│   ├── geo_loader.py
│   ├── normalization.py
│   ├── batch_correction.py
│   ├── correlation.py
│   ├── mapping.py
│   ├── evaluation.py
│   └── enrichment.py
├── Makefile
└── requirements.txt
```

## Complexity Tracking
No constitution violations remain after the redesign; all constraints are satisfied with the chosen CPU‑first approach.

## Phase‑wise Implementation Plan (covers every FR & SC)

| Phase | Target FR/SC | Action(s) | Output |
|-------|--------------|-----------|--------|
| **Phase 1 – Data Acquisition** | FR‑001, FR‑047 | • Parse `species.yaml` for GEO series per species.<br>• Use `GEOparse` to download each series (skip series with < 30 samples).<br>• Verify total sample count ≥ 50; abort otherwise (log error). | Raw GEO tarballs in `data/raw/`; `pipeline.log` entry. |
| **Phase 2 – Normalization & Filtering** | FR‑002, FR‑003, FR‑014 | • If `--norm vst` → call DESeq2 VST via `rpy2`; else compute TPM in Python.<br>• Apply CPM filter (CPM < 1 in > 80 % samples).<br>• Compute per‑gene variance; keep the top high‑variance genes (approximately a few thousand).<br>• When > 1 series → run ComBat; fallback to SVA if metadata missing.<br>• Regress out expression‑level & gene‑length confounds.<br>**Power justification**: With ≥ 50 samples, detecting a true correlation of r = 0.8 at α = 0.05 yields > 80 % power (Cohen, 1992). For smaller effect sizes power drops; we will report this limitation in the summary.<br>**Multiple‑testing note**: Adjusted p‑values are recorded (FR‑045) but not used for edge selection. | Normalized matrices (`processed/normalized_*.csv`); batch‑corrected matrices; logs. |
| **Phase 3 – Correlation Computation** | FR‑004, FR‑020, FR‑025, FR‑045 | • Compute Pearson (VST) or Spearman (TPM) correlations on the 5 000‑gene set.<br>• Stream pairwise computation block‑wise; write gzipped TSV `raw_correlations_<species>.tsv.gz` (gene_id_1, gene_id_2, correlation, p_value, adjusted_p_value).<br>• Record adjusted p‑values for reporting (no edge selection).<br>• For thresholds 0.60‑0.90 compute edge counts and store in `threshold_sensitivity_<species>.tsv`. | Raw correlation files; sensitivity tables. |
| **Phase 4 – Identifier Mapping** | FR‑005 | • Load `org.At.tair.db` (Bioconductor) or Ensembl BioMart via `biopython`.<br>• Map retained gene IDs to STRING protein IDs; unmapped genes are logged (`mapping_warnings_<species>.log`). | Mapping table (`processed/gene_to_protein_<species>.csv`). |
| **Phase 5 – Edge Selection & Thresholding** | FR‑004, FR‑045, FR‑011, FR‑012, FR‑013, FR‑009 | • Apply default threshold r ≥ 0.80 (never below 0.75).<br>• **Data‑driven selection**: The sensitivity analysis (Phase 3) and pilot hold‑out (Phase 6) are consulted; users may override the default to the threshold that maximizes balanced F1 or Youden’s J.<br>• Write `predicted_ppi_<species>.tsv` (protein_id_1, protein_id_2, correlation).<br>• Validate against `contracts/predicted_edges.schema.yaml`.<br>• Seed is set via CLI `--seed`. | Edge list files; validation step. |
| **Phase 6 – Evaluation** | FR‑006, FR‑007, FR‑016, FR‑032, FR‑018, FR‑019, FR‑048, FR‑017, FR‑012 | • **Independent test split**: After batch correction, split samples per species into training (majority) and test (remainder). The co‑expression network (correlations, edge selection) is built on the training set only.<br>• Load STRING `protein.links.v11.5.txt.gz`; keep high‑confidence (combined ≥ 700) **experimental** or **database** evidence only (explicitly exclude co‑expression, transcriptomics, text‑mining channels).<br>• Score **all** gene‑pair correlations from the *test* set against this STRING set → compute AUROC, AUPRC (full, imbalanced).<br>• Sample a balanced negative set (size = positive) uniformly from the complement.<br>• Generate degree‑preserving random graph via `networkx.double_edge_swap` (a multiple of the edge count).<br>• Compute baseline AUROC/AUPRC and p‑value (`baseline_p`).<br>• Run pilot benchmark on a *held‑out* Arabidopsis GEO series (not used in training) → store `pilot_validation_Arabidopsis.json` (precision ≥ 0.60, recall ≥ 0.40).<br>• Validate `evaluation_metrics.json` against `contracts/evaluation.schema.yaml`.<br>• Verification script checks presence & parsability of all evaluation outputs. | `evaluation_metrics.json`; `pilot_validation_*.json`; logs. |
| **Phase 7 – Functional Enrichment** | FR‑008, FR‑023, FR‑024, FR‑022, SC‑002 | • Extract gene set participating in predicted edges.<br>• Run GOATOOLS Fisher’s exact test with Benjamini–Hochberg correction using the filtered‑gene universe as background.<br>• Write `go_enrichment_<species>.tsv`; if no term passes FDR < 0.05 write “No significant enrichment”. | GO enrichment tables. |
| **Phase 8 – Reporting & Summary** | FR‑021, FR‑028, FR‑030, FR‑034, FR‑035, FR‑010, FR‑026, SC‑001, SC‑003, SC‑004, SC‑005, SC‑006 | • Assemble `summary_<species>.txt` (edge count, AUROC/AUPRC, baseline p, top GO terms, construct‑validity justification with literature citations).<br>• Concatenate per‑species summaries into **`master_results.json`** (the SSoT artifact) and `final_report.txt` with overall statistics.<br>• Log final summary creation (JSON‑Line schema).<br>• Validate `threshold_sensitivity_<species>.tsv` via `contracts/threshold_sensitivity.schema.yaml`. | Summary files; `master_results.json`; final report. |

All Makefile targets (`all`, `evaluate`, `enrich`, `summary`, `clean`) invoke the corresponding phases in the order above, guaranteeing that data acquisition precedes any downstream computation, models are fitted before evaluation, and figures are generated before being embedded in the paper.

---


## Additional Notes
* The pipeline aborts early if any FR/SC validation fails (see FR‑017, FR‑019, FR‑030, FR‑034).  
* All random‑seed‑controlled steps use the same seed supplied via `--seed`.  
* The `master_results.json` file is the definitive source of truth for all downstream reporting, satisfying the constitution’s Single Source of Truth principle.  
