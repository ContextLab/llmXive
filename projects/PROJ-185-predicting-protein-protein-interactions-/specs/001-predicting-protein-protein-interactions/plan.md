# Implementation Plan: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

**Branch**: `PROJ-185-predict-ppi-coexpression` | **Date**: 2026‑06‑24 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `specs/PROJ-185-predict-ppi-coexpression/spec.md`

## Summary
The pipeline will (1) download bulk RNA‑seq count matrices for each target plant species from GEO, (2) normalize (TPM or DESeq2 VST), (3) filter low‑expression genes, (4) pre‑select a subset of the most variable genes (on the order of several thousand) by median absolute deviation (MAD) to keep the correlation matrix tractable, (5) compute pairwise Pearson (or alternative) correlations and retain edges with *r* ≥ 0.8 (never below), (6) map gene identifiers to STRING protein IDs, (7) output per‑species edge lists, (8) evaluate against STRING high‑confidence interactions (combined ≥ 700) **and** an independent experimental‑only benchmark, (9) generate a degree‑preserving random‑graph baseline, (10) perform GO enrichment, (11) orchestrate everything via a reproducible Makefile with full logging, a global `--seed` flag, and explicit performance‑benchmarking, and (12) validate all outputs against schema contracts.

## Power Analysis
A minimum of **20 RNA‑seq samples** per GEO series is required (FR‑001). With *n* = 20, the smallest detectable Pearson correlation at α = 0.05 (two‑tailed) is ≈ 0.44 (Cohen, 1988). This establishes a lower bound on statistical power; larger sample sets improve stability of correlation estimates. The limitation is documented in the manuscript and reflected in the success‑criterion discussion.

## Computational Feasibility
Typical plant transcriptomes contain 20‑30 k genes, leading to > 200 M pairwise tests. To respect the 6‑hour wall‑clock budget on a GitHub Actions runner (2 CPU, 7 GB RAM), we **pre‑select the top 5 000 most variable genes** (by MAD) before correlation (Phase 4). Correlation is computed with `joblib` parallelisation across available cores, and memory‑mapped NumPy arrays are used to avoid excessive RAM consumption.

## Phase‑by‑Phase Implementation Plan & Task Mapping

| Phase | Description (FR / SC) | Output Artifacts | Tasks (IDs) |
|-------|-----------------------|------------------|-------------|
| **0. Power & Feasibility** | Document power limitation (see above). | N/A | T000 (documentation note) |
| **1. Repository & Environment Setup** | Create repo skeleton, pin Python & R dependencies, add linting config, CI workflow. | Repo layout, `requirements.txt`, `renv.lock`, `.github/workflows/ci.yml` | T001, T002, T003, T004, T005 |
| **2. Data Acquisition** | **FR‑001** – download GEO series per species; abort if < 20 samples. | `data/raw/<accession>.counts.tsv` | T006 (download_gse.py) + `test_download.py` |
| **3. Normalization & Optional Batch Correction** | **FR‑002** – TPM or DESeq2 VST (CLI flag). Optional batch correction via limma (`--batch-correct`). | `data/processed/<species>_norm.tsv` | T008 (normalize.py) + `test_normalization.py` |
| **4. Gene Filtering & Variable‑Gene Pre‑selection** | **FR‑003** – CPM < 1 in > 80 % samples filter. **FR‑004** – retain top 5 000 MAD genes before correlation (memory budget). | `data/processed/<species>_filtered.tsv` | T009 (filter_genes.py) + `test_filter.py`; T010 (select_variable_genes.py) + `test_variable_selection.py` |
| **5. Correlation & Edge Generation** | **FR‑004** – compute pairwise correlation (default Pearson, selectable), apply Benjamini–Hochberg FDR, retain edges with *r* ≥ THRESHOLD (default 0.8, never below). | `results/edges/<species>_raw_edges.tsv` | T011 (correlation.py) + `test_correlation.py`; **Contract Validation** – T012 validates this TSV against `contracts/predicted_edges.schema.yaml`. |
| **6. Identifier Mapping** | **FR‑005** – map TAIR IDs via `org.At.tair.db`; fallback to Ensembl BioMart; log unmapped genes. | `results/predicted_ppi_<species>.tsv` (final edge list) | T013 (map_ids.py) + `test_mapping.py`; **Contract Validation** – T014 validates final TSV against `contracts/predicted_ppi.schema.yaml`. |
| **7. Evaluation Against STRING (Primary Benchmark)** | **FR‑006** – compare to STRING high‑confidence (combined ≥ 700) and compute AUROC/AUPRC. **SC‑001** – require AUROC > 0.70 and AUPRC ≥ 0.65. | `evaluation_metrics.json` (primary metrics) | T015 (evaluate.py) + `test_metrics.py` (AUROC > 0.70, AUPRC ≥ 0.65) |
| **8. Independent Experimental Benchmark** | **FR‑006** – evaluate against STRING interactions whose `evidence_type == "experimental"` (no co‑expression evidence). | `evaluation_metrics.json` (adds `experimental_auroc`, `experimental_auprc`) | T016 (evaluate_experimental.py) + `test_experimental_metrics.py` |
| **9. Baseline Random Graph** | **FR‑007** – generate multiple degree‑preserving rewiring iterations, compute baseline AUROC/AUPRC, empirical p‑value. | Baseline scores added to `evaluation_metrics.json` | T017 (baseline.py) + `test_baseline.py` |
| **10. GO Enrichment** | **FR‑008** – GOATOOLS Fisher’s exact test on union of genes in predicted PPIs; Benjamini–Hochberg FDR ≤ 0.05. **SC‑002** – at least one GO term with adjusted p < 0.05. | `go_enrichment_<species>.tsv` | T018 (enrichment.py) + `test_go.py` |
| **11. Orchestration & Logging** | **FR‑009** – Makefile with targets `all`, `evaluate`, `enrich`, `clean`, `validate`, `benchmark`, `reproducibility-check`. **FR‑010** – central logger with ISO‑8601 timestamps. **SC‑003** – benchmark target records wall‑clock time; CI fails if > 6 h. | `pipeline.log`, `Makefile` | T019 (Makefile) + `test_make_targets.py`; T020 (logger.py) + `test_logger.py`; T023 (`benchmark` target) + `test_benchmark.py` |
| **12. Reproducibility & Seed Handling** | **FR‑012** – global `--seed` flag; all stochastic steps respect it. **SC‑004** – `make reproducibility-check` re‑runs pipeline with same seed and asserts identical SHA‑256 hashes of `evaluation_metrics.json` and `go_enrichment_<species>.tsv`. | `results/validation_report.json` | T022 (seed.py) + `test_seed.py`; T024 (`reproducibility-check`) + `test_reproducibility.py` |
| **13. Output Presence & Parsability** | **SC‑005** – ensure required files exist and are parsable after a successful run for each species. | All output files listed in SC‑005 | T025 (`test_outputs.py`) |
| **14. Contract Validation** | Validate raw edge list and final PPI files against contracts. | Schema‑validated TSVs | T012, T014 (see above) |
| **15. CI & Citation Checks** | Ensure CI workflow triggers correctly and runs all verification tests, including citation validation via Reference‑Validator Agent. | CI run logs | T005 (CI file) + `test_ci_trigger.py`; T026 (citation validator) + `test_citation_validator.py` |
| **16. Documentation Build** | Build MkDocs site; ensure generated HTML contains expected sections. | `site/` | T027 (documentation build) + `test_docs.py` |

### Task List (Unique IDs)

| ID | Module / File | Description | Verification Artifact |
|----|----------------|-------------|-----------------------|
| T000 | docs/power.md | Power‑analysis note (no code). | `test_power_note.py` |
| T001 | repo_setup/ | Create directory hierarchy (`code/`, `data/`, `results/`, `specs/`, `contracts/`). | `test_repo_structure.py` |
| T002 | requirements.txt & pyproject.toml | Pin exact versions of all Python packages. | `test_requirements.py` |
| T003 | renv.lock | Initialise R environment with DESeq2, org.At.tair.db, biomaRt, limma. | `test_renv.py` |
| T004 | lint_config/ | Add ruff, black, styler configs. | `test_lint.py` |
| T005 | .github/workflows/ci.yml | CI workflow that runs `make validate`. | `test_ci_trigger.py` |
| T006 | code/data/download_gse.py | GEO downloader (FR‑001). | `test_download.py` |
| T007 | code/cli/main.py | Click entry point with argument parsing (`--norm-method`, `--threshold`, `--seed`, `--species`). | `test_cli.py` |
| T008 | code/data/normalize.py | TPM/VST normalization (FR‑002). | `test_normalization.py` |
| T009 | code/data/filter_genes.py | CPM < 1 filter (FR‑003). | `test_filter.py` |
| T010 | code/data/select_variable_genes.py | Top‑MAD 5 000 gene selection (computational feasibility). | `test_variable_selection.py` |
| T011 | code/data/correlation.py | Correlation calculation, FDR, threshold enforcement (FR‑004). | `test_correlation.py` |
| T012 | validation/raw_edge_schema.py | Validate `results/edges/*_raw_edges.tsv` against `contracts/predicted_edges.schema.yaml`. | `test_schema_raw_edges.py` |
| T013 | code/data/map_ids.py | Gene → STRING ID mapping (FR‑005). | `test_mapping.py` |
| T014 | validation/final_ppi_schema.py | Validate `results/predicted_ppi_*.tsv` against `contracts/predicted_ppi.schema.yaml`. | `test_schema_final_ppi.py` |
| T015 | code/data/evaluate.py | AUROC/AUPRC vs STRING high‑confidence (FR‑006). | `test_metrics.py` (AUROC > 0.70, AUPRC ≥ 0.65) |
| T016 | code/data/evaluate_experimental.py | AUROC/AUPRC vs STRING experimental‑only subset (independent benchmark). | `test_experimental_metrics.py` |
| T017 | code/data/baseline.py | Degree‑preserving random‑graph baseline (FR‑007). | `test_baseline.py` |
| T018 | code/data/enrichment.py | GO enrichment (FR‑008). | `test_go.py` (≥ 1 GO term adj p < 0.05) |
| T019 | Makefile | Orchestration targets (`all`, `evaluate`, `enrich`, `clean`, `validate`, `benchmark`, `reproducibility-check`). | `test_make_targets.py` |
| T020 | utils/logger.py | Central logger with ISO‑8601 timestamps (FR‑010). | `test_logger.py` |
| T021 | code/data/predicted_ppi_output.py | Writes `predicted_ppi_<species>.tsv` per species (FR‑011). | `test_output_files.py` |
| T022 | utils/seed.py | Global seed handling (FR‑012). | `test_seed.py` |
| T023 | benchmarks/benchmark.py | Records wall‑clock time; fails if > 6 h (SC‑003). | `test_benchmark.py` |
| T024 | reproducibility/check.py | Re‑run with same seed, compare SHA‑256 hashes (SC‑004). | `test_reproducibility.py` |
| T025 | validation/outputs.py | Checks presence & parsability of all required output files (SC‑005). | `test_outputs.py` |
| T026 | citation/validator.py | Invoke Reference‑Validator Agent on repository citations. | `test_citation_validator.py` |
| T027 | docs/build_check.py | Build MkDocs site and verify key headings exist. | `test_docs.py` |

All FR‑0XX and SC‑0XX now have a concrete plan phase/step that names the id it addresses. The plan respects the 6‑hour runtime budget, includes power‑analysis justification, mitigates circular validation by adding an experimental‑only benchmark, and validates all outputs against schema contracts.

## Constitution Check
| Principle | Reference |
|-----------|-----------|
| I. Reproducibility | All scripts accept `--seed`, deterministic random graph generation, and full environment pinning (`requirements.txt`, `renv.lock`). |
| II. Verified Accuracy | No new external citations introduced; all dataset URLs are verified (see `research.md`). |
| III. Data Hygiene | Raw GEO files stored under `data/raw/`; each transformation writes a new file and records a SHA‑256 checksum in `data/checksums.yaml`. |
| IV. Single Source of Truth | Every figure/table in the eventual manuscript will be generated from the JSON/TSV artifacts produced by the pipeline. |
| V. Versioning Discipline | All artifacts are hashed; `state/projects/PROJ-185-...yaml` will be updated automatically by CI. |
| VI. Biological Data Provenance | GEO accession IDs and download timestamps are logged in `pipeline.log`. |
| VII. Evaluation Benchmarking | STRING high‑confidence set (combined score ≥ 700) and experimental‑only subset are used; AUROC > 0.70, baseline significance reported, and GO enrichment follows Benjamini–Hochberg (FDR ≤ 0.05). |

--- 
