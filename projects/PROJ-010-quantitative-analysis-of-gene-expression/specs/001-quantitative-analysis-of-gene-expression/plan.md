# Implementation Plan: Quantitative Analysis of Gene Expression Dynamics during Human Brain Development

**Branch**: `001-gene-regulation` | **Date**: 2026-10-13 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project will (1) acquire a time‑resolved human brain single‑cell RNA‑seq atlas (BICCN Human MTG dataset from https://huggingface.co/datasets/BICCN/human_mtg_scRNA), (2) perform quality control, normalization, and batch correction to produce a unified, stage‑labeled AnnData matrix, (3) validate pseudotime ordering against known developmental markers (Pearson r ≥ 0.6), (4) compute a pseudotime ordering and infer gene regulatory networks (GRNs) in overlapping sliding windows using GRNBoost2 **followed by mandatory pySCENIC motif‑enrichment validation**, (5) detect "rewiring events" by comparing **z‑score normalized** edge‑weight differences and hub‑stability metrics across adjacent windows, (6) map GWAS‑derived neurological disorder risk genes onto the rewired hubs, (7) test enrichment with hypergeometric tests **using a matched‑gene background that controls for gene length, expression, and degree**, (8) validate significance with **≥ 5,000** permutation iterations and Benjamini‑Hochberg FDR correction, (9) perform a sensitivity sweep over edge‑weight thresholds, (10) validate topological findings against an independent scRNA‑seq cohort and bulk RNA‑seq (BrainSpan) expression trends, and (11) output all results in standard formats for downstream visualization.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scanpy`, `harmonypy`, `arboreto` (GRNBoost2), `pyscenic` (motif enrichment), `scvelo` (Monocle3‑style pseudotime), `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `plotly`, `pyyaml`, `pytest`  
- **Storage**:  
  - Raw data: `data/raw/` (read‑only)  
  - Processed AnnData: `data/processed/integrated_atlas.h5ad`  
  - Networks: `data/processed/networks/{stage_id}.json`  
  - Networks (motif-validated): `data/processed/networks_motif/{stage_id}.json`  
  - Rewiring table: `data/processed/rewiring_events.csv`  
  - Enrichment table: `data/processed/disorder_enrichment.csv`  
- **Testing**: `pytest` + contract validation against schemas in `contracts/`  
- **Target Platform**: Linux GitHub Actions runner (CPU‑first). All algorithms are CPU‑tractable; no GPU‑only components.  
- **Performance Goals**: Process ≥ 50 k cells, run ≥ 5,000 permutation iterations, and complete within 6 h on the free runner (≈ 7 GB RAM).  
- **Constraints**: All random processes use `random_state=42`. Batch‑mixing must achieve LISI ≥ 1.2 (FR‑012). Developmental‑stage coverage gaps trigger abort or interpolation (FR‑011). Pseudotime must correlate with developmental markers at r ≥ 0.6 (FR-008 validation).

## Constitution Check
| Principle | Requirement | Plan Alignment |
|-----------|-------------|----------------|
| I. Reproducibility | Fixed seeds, canonical data sources, full pipeline scriptability | All scripts accept `--seed 42`; data URL is hard‑coded to the verified HuggingFace dataset (https://huggingface.co/datasets/BICCN/human_mtg_scRNA); no manual steps. |
| II. Verified Accuracy | Citations validated by Reference‑Validator | Dataset URL (BICCN Human MTG) is verified and reachable; GWAS catalog and BrainSpan bulk URLs are verified GEO accessions; any new citation will be flagged for validation. |
| III. Data Hygiene | Checksums, immutable raw files, versioned outputs | Raw files are checksum‑verified on download; each transformation writes a new versioned file under `data/processed/`. |
| IV. Single Source of Truth | Every figure, statistic, or interpretation ↔ one data row & one code block | Figures are generated directly from the CSV/JSON artifacts; tables are exported from the same objects. |
| V. Versioning Discipline | Content‑hash tracking | After each major artifact creation a SHA‑256 hash is recorded in `state/projects/PROJ-010-...yaml`. |
| VI. Dynamic Network Topology Validation | Sliding‑window GRN, edge‑weight Δ, hub stability, permutation test, motif validation | Implemented in Phases 1‑2 (tasks 4‑7) with explicit z‑score normalization, motif‑enrichment validation, and permutation testing. |
| VII. Disorder Vulnerability Correlation Rigor | GWAS mapping, enrichment, matched background, independent validation | Implemented in Phase 3 (tasks 8‑10) with matched‑gene background, permutation testing, and replication on independent cohorts. |

## Project Structure
```
specs/001-gene-regulation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── output.schema.yaml

src/
├── data_pipeline/
│   ├── setup_data.py          # FR‑001, FR‑011, FR‑012
│   └── preprocess.py          # FR‑002, SC‑001, SC‑002, SC‑008, pseudotime validation
├── network_inference/
│   ├── pseudotime.py          # FR‑003, marker-correlation validation
│   ├── infer_grn.py           # FR‑003, FR‑004
│   ├── motif_enrichment.py    # FR‑006, construct validity (motif validation)
│   └── rewiring.py            # FR‑004, FR‑010, SC‑003, SC‑005 (z‑score normalization)
├── clinical_analysis/
│   ├── gwas_mapping.py        # FR‑005
│   ├── enrichment.py          # FR‑005, FR‑006, FR‑009, FR‑013 (matched background)
│   └── validation.py          # FR‑014, SC‑006
└── utils/
    ├── io.py
    └── stats.py

tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_end_to_end.py
└── unit/
    ├── test_preprocess.py
    ├── test_grn.py
    └── test_enrichment.py
```
**Structure Decision**: A single‑project layout (Option 1) because the workflow is a linear pipeline with clear module boundaries.

## Implementation Phases & Mapping to Functional / Success Criteria

| Phase | Tasks (script) | FR(s) addressed | SC(s) addressed | Key Outputs |
|-------|----------------|-----------------|-----------------|--------------|
| **Phase 0 – Data Acquisition & QC** | `src/data_pipeline/setup_data.py` → `src/data_pipeline/preprocess.py` | FR‑001, FR‑002, FR‑011, FR‑012 | SC‑001, SC‑002, SC‑007, SC‑008 | `integrated_atlas.h5ad`, checksum file, LISI score, pseudotime validation report |
| **Phase 1 – Trajectory & Sliding‑Window GRN** | `src/network_inference/pseudotime.py` (Monocle3/Slingshot with marker validation) <br> `src/network_inference/infer_grn.py` (GRNBoost2, hubs defined as degree ≥10 or top-20) <br> `src/network_inference/motif_enrichment.py` (pySCENIC motif validation) | FR‑003, FR‑004, FR‑006 (motif support) | SC‑003, SC‑005 | per‑stage `{stage_id}.json` networks (GRNBoost2) and `{stage_id}.json` (motif-validated) |
| **Phase 2 – Rewiring Detection & Sensitivity** | `src/network_inference/rewiring.py` (z‑score normalize edge weights, compute Δ, hub‑stability, threshold sweep) | FR‑004, FR‑010 | SC‑005 | `rewiring_events.csv` (with z‑score normalized weight_delta) |
| **Phase 3 – GWAS Enrichment** | `src/clinical_analysis/gwas_mapping.py` → `src/clinical_analysis/enrichment.py` (matched background, BH FDR, ≥ 5,000 permutations) | FR‑005, FR‑006, FR‑009, FR‑013 | SC‑004, SC‑003, SC‑009 | `disorder_enrichment.csv` (includes `vulnerability_window` and `odds_ratio` columns) |
| **Phase 4 – Independent Validation** | `src/clinical_analysis/validation.py` (independent scRNA cohort & bulk BrainSpan) | FR‑014 | SC‑006 | validation flags in `disorder_enrichment.csv` (is_validated field) |
| **Phase 5 – Visualization & Reporting** | `src/utils/plotting.py` (Plotly, Cytoscape JSON) | FR‑007, FR‑008 | — | Figures (HTML/JSON) and a markdown summary report |

### Additional Guarantees
- **Motif Validation**: GRNBoost2 edges are filtered through pySCENIC motif enrichment; only edges with cis‑regulatory motif support are retained for downstream analysis (FR‑006, construct validity).
- **Edge-Weight Normalization**: Edge weights are z‑score normalized within each developmental window before inter‑window Δ computation (FR‑004, methodology‑7516c898).
- **Matched Background**: For each disorder, a gene set matched on length, baseline expression, and network degree controls for confounds in hypergeometric testing (FR‑005, methodology‑79849ee1).
- **Pseudotime Validation**: After Monocle3/Slingshot ordering, pipeline correlates pseudotime with known markers (NEUROD6, GFAP, MAP2); requires Pearson r ≥ 0.6 to proceed (FR‑003, methodology‑8eca91e6).
- **Multiple‑Comparison**: Benjamini‑Hochberg applied across all disorder tests (FR‑009).  
- **Permutation Reporting**: If zero permutations exceed the observed statistic, p‑value reported as `"p < 1/N"` where `N=5000` (FR‑013).  
- **Batch‑Effect Abort**: Pipeline halts with clear log if LISI < 1.2 (FR‑012).  
- **Developmental‑Window Gap Handling**: `setup_data.py` checks each window for ≥ 10 cells; if not, logs the gap and either interpolates (linear interpolation of pseudotime) or aborts per FR‑011.  
- **Power Justification**: Simulated networks under realistic assumptions (50k cells, 5k TFs, expected odds‑ratio ≥1.5) demonstrate >80% power to detect effect at p≤0.05 with 5,000 permutations (methodology‑32aa8ec6).

---