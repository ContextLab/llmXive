# Implementation Plan: Predict Protein‑Protein Interactions from Co‑expression Networks in Public Plant Databases

**Branch**: `PROJ-185-predict-ppi-coexpression` | **Date**: 2026‑07‑30 | **Spec**: [spec.md](../spec.md)  
**Input**: Feature specification from `specs/PROJ-185-predict-ppi-coexpression/spec.md`

## Summary
The pipeline will (1) download public *Arabidopsis thaliana* RNA‑seq count matrices from GEO, (2) normalize, filter, and batch‑correct the data, (3) compute pairwise gene‑gene correlations, (4) map genes to STRING protein IDs, (5) retain edges with correlation ≥ 0.80, (6) evaluate the edge set against high‑confidence STRING interactions, (7) perform GO enrichment on the predicted interactome, and (8) generate per‑species and final summary reports. All steps are orchestrated by a GNU Makefile and run on a fresh GitHub Actions runner within the 6‑hour wall‑clock limit.

## Technical Context
- **Language/Version**: Python 3.11, R 4.2 (via `renv` environment)  
- **Primary Dependencies**  
  - Python: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `networkx==3.2.*`, `goatools==1.4.*`, `datasets==2.18.*`, `pyarrow==15.*`, `rpy2==3.5.*`  
  - R (Bioconductor): `DESeq2`, `org.At.tair.db`, `limma`, `sva`, `edgeR` (via `renv`)  
- **Storage**: Files on the runner’s temporary filesystem (`/tmp/data/`). All intermediate files are streamed or gzipped to stay < 7 GB RAM.  
- **Testing**: `pytest==8.*` for Python; `testthat==3.*` for R.  
- **Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner (Multiple CPUs, 7 GB RAM, 14 GB disk).  
- **Compute Strategy**: CPU‑first; no GPU‑only methods are required.  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Random seed exposed via `--seed`; external datasets fetched from canonical URLs (see `research.md`). |
| II. Verified Accuracy | Citations limited to verified dataset sources; no invented URLs. |
| III. Data Hygiene | Raw GEO and STRING files stored under `data/raw/` unchanged; checksums recorded in `data/checksums.txt`. |
| IV. Single Source of Truth | Every statistic in the final report derives from a single row in the corresponding TSV/JSON output file. |
| V. Versioning Discipline | All artifacts hashed; hashes recorded in `state/artifact_hashes.yaml`. |
| VI. Biological Data Provenance | GEO accession IDs retained in metadata columns of each sample file. |
| VII. Evaluation Benchmarking | Evaluation follows high‑confidence STRING (> 700) exclusion rule; AUROC/AUPRC thresholds enforced per SC‑001. |

## Project Structure
```text
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
│   ├── species.yaml               # species‑specific GEO accession lists
│   └── parameters.yaml            # default thresholds, seed, etc.
├── data/
│   ├── raw/                       # downloaded GEO & STRING files (read‑only)
│   └── processed/                 # normalized matrices, mappings, etc.
├── pipelines/
│   ├── download.py
│   ├── normalize.R
│   ├── batch_correct.R
│   ├── correlate.py
│   ├── map_ids.R
│   ├── select_edges.py
│   ├── evaluate.py
│   ├── enrich_go.py
│   └── summarize.py
├── utils/
│   └── logger.py
├── Makefile
└── requirements.txt
```

## Phase‑wise Mapping of Functional Requirements (FR) & Success Criteria (SC)

| Phase | FR IDs | Description | Key Tasks (Make targets) |
|-------|--------|-------------|--------------------------|
| **Phase 1 – Data Acquisition** | FR‑001, FR‑047 | Download GEO series per species; discard series with < 30 samples; abort if total < 50. | `make download` |
| **Phase 2 – Normalization & Filtering** | FR‑002, FR‑003, FR‑014, FR‑010 | Apply VST (DESeq2) or TPM; filter genes CPM < 1 in > 80 % samples; batch‑effect correction (ComBat) or SVA fallback; regress expression‑level & gene‑length confounds; **log all actions in JSON‑Line format** (FR‑010). | `make normalize` |
| **Phase 3 – Correlation Computation** | FR‑004, FR‑020, FR‑025, FR‑045 | Compute Pearson (or Spearman for TPM) correlations; stream pairwise calculations; write block‑wise gzipped `raw_correlations_<species>.tsv.gz`; run sensitivity analysis across a range of moderate to high thresholds.. | `make correlate` |
| **Phase 4 – Identifier Mapping** | FR‑005 | Map TAIR IDs → STRING protein IDs using `org.At.tair.db` (fallback to Ensembl BioMart). Log unmapped genes. | `make map_ids` |
| **Phase 5 – Edge Selection & Thresholding** | FR‑004, FR‑045, FR‑011, FR‑012, FR‑013 | Retain edges r ≥ threshold (default 0.80, never < 0.75); write `predicted_ppi_<species>.tsv`; **validate** against `predicted_edges.schema.yaml` (FR‑013); **global `--seed` flag** ensures reproducibility (FR‑012). | `make select_edges` |
| **Phase 6 – Evaluation** | FR‑006, FR‑007, FR‑016, FR‑032, FR‑018, FR‑019, FR‑012, FR‑017, FR‑048 | Score all gene‑pair correlations against STRING high‑confidence (≥ 700, exclude co‑expression evidence); generate balanced negative set; compute AUROC/AUPRC; degree‑preserving random‑graph baseline; record `baseline_p`; **run pilot benchmark** on held‑out Arabidopsis data; **post‑target verification** of required outputs (FR‑017). | `make evaluate` |
| **Phase 7 – Functional Enrichment** | FR‑008, FR‑022, FR‑023, FR‑024, **SC‑002** | GO enrichment on genes in predicted edges using GOATOOLS; BH correction; write `go_enrichment_<species>.tsv`; handle “no significant enrichment” case. **SC‑002 requires at least one GO term with adjusted p‑value < 0.05**. | `make enrich` |
| **Phase 8 – Reporting & Summary** | FR‑021, FR‑028, FR‑030, FR‑034, FR‑035, FR‑010, FR‑026, FR‑017 | Create per‑species `summary_<species>.txt` (edge count, metrics, top GO terms, construct‑validity justification); aggregate into `final_report.txt`; **log command‑line, software versions, seed** (FR‑035); **verification** of all outputs (FR‑017). | `make summary` and `make final_report` |
| **Phase 9 – Orchestration & Runtime** | **FR‑009**, FR‑010, FR‑017 | GNU Makefile orchestrates `all`, `evaluate`, `enrich`, `summary`, `clean`; ensures total wall‑clock ≤ 6 h on CI; integrates logging (FR‑010) and verification (FR‑017). | `make all` |
| **Phase 10 – Verification** | FR‑017 | After each Make target, `make verify` validates all output files against their contracts; aborts on any schema violation. | `make verify` |

All FRs and SCs from the specification are explicitly covered; no FR/SC is omitted.

## Timeline (estimated wall‑clock on GitHub Actions runner)
| Week | Milestone |
|------|-----------|
| 1 | Scaffold repo, create `renv.lock`, CI workflow skeleton. |
| 2 | Implement Phase 1 & Phase 2 scripts; unit tests for download & normalization. |
| 3 | Implement Phase 3 streaming correlation; schema for raw correlations. |
| 4 | Implement Phase 4 mapping; logging utilities. |
| 5 | Implement Phase 5 edge selection; contract validation tests. |
| 6 | Implement Phase 6 evaluation (AUROC/AUPRC, baseline, pilot benchmark). |
| 7 | Implement Phase 7 GO enrichment; ensure BH correction. |
| 8 | Implement Phase 8 reporting; final CI integration; documentation & quickstart. |
| 9 | Full pipeline end‑to‑end test on CI; performance tuning to stay ≤ 6 h. |
| 10| Release candidate & handoff to Implementation Agent. |

## Compute Feasibility
- All heavy numeric work runs on CPU; pairwise tests ≤ 12.5 M (≤ 5 k genes) streamed, fitting ≤ 6 GB RAM.  
- No GPU required; the pipeline runs entirely on a multi‑CPU GitHub Actions runner.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient GEO samples after filtering (FR‑001) | Biological relevance loss | Abort with clear error if < 50 samples (FR‑047). |
| Batch‑effect correction fails due to missing metadata | Biased correlations | Fallback to SVA; warnings logged. |
| Memory blow‑up during correlation computation | Job failure | Block‑wise streaming; gene‑set cap at ≤ 5 k. |
| STRING file format mismatch | Evaluation failure | Verify required columns after download; abort with clear error. |
| Reproducibility drift | Non‑reproducible results | All random generators seeded from `--seed`; logs capture seed, versions, command line. |

---



