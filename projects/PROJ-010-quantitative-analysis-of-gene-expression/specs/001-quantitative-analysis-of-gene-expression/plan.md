# Implementation Plan: Quantitative Analysis of Gene Expression Dynamics during Human Brain Development

**Branch**: `001-gene-regulation` | **Date**: 2026-10-19 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project will (1) acquire an open, programmatically‑downloadable human brain single‑cell RNA‑seq dataset that includes explicit developmental‑stage metadata, (2) perform QC, normalization, and batch correction to produce a unified, stage‑labeled AnnData matrix, (3) define *observed* developmental windows (e.g., “Fetal 12‑16 w”, “Fetal 16‑20 w”, “Adult”) and infer gene‑regulatory networks (GRNs) within each window using GRNBoost2, (4) detect “rewiring events” by comparing edge‑weight differences and hub‑stability metrics across adjacent windows, (5) map GWAS‑derived neurological‑disorder risk genes onto rewired hubs, (6) test enrichment with hypergeometric tests using a matched‑gene background, (7) validate significance with ≥ 5,000 permutation iterations and Benjamini‑Hochberg FDR correction, (8) perform a sensitivity sweep over edge‑weight thresholds, (9) replicate the core findings in an independent open scRNA‑seq cohort, and (10) output all results in standard formats for downstream visualization.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scanpy`, `harmonypy`, `arboreto` (GRNBoost2), `pyscenic` (motif validation), `scvelo` (optional pseudotime within windows), `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `plotly`, `pyyaml`, `pytest`, `datasets` (🤗 datasets)  
- **Storage**:  
  - Raw data: `data/raw/` (immutable)  
  - Processed AnnData: `data/processed/integrated_atlas.h5ad`  
  - GRNs (raw): `data/processed/networks/{stage_id}.json`  
  - GRNs (motif‑validated): `data/processed/networks_motif/{stage_id}.json`  
  - Rewiring table: `data/processed/rewiring_events.csv`  
  - Enrichment table: `data/processed/disorder_enrichment.csv`  
- **Testing**: `pytest` + contract validation against schemas in `contracts/`  
- **Target Platform**: Linux GitHub Actions runner (CPU‑first). All algorithms are CPU‑tractable; no GPU‑only components.  
- **Performance Goals**: Process ≥ 50 k cells, run ≥ 5 000 permutation iterations, and finish ≤ 6 h on the free runner (≈ 7 GB RAM).  
- **Constraints**:  
  - Fixed random seed (`--seed 42`).  
  - Batch‑mixing must achieve LISI ≥ 1.2 (FR‑012).  
  - Developmental‑window coverage gaps trigger abort or linear interpolation (FR‑011).  
  - Edge‑weight differences are **z‑score normalized** within each window (FR‑004).  
  - All enrichment p‑values are Benjamini‑Hochberg corrected (FR‑009).  
  - Zero‑permutation cases reported as `p < 1/N` (FR‑013).  

## Constitution Check
| Principle | Requirement | Plan Alignment |
|-----------|-------------|----------------|
| I. Reproducibility | Fixed seeds, canonical data sources, full pipeline scriptability | All scripts accept `--seed 42`; data URL is hard‑coded to a verified 🤗 dataset; no manual steps. |
| II. Verified Accuracy | Citations validated by Reference‑Validator | Dataset URLs are from the verified list; any new citation will be flagged. |
| III. Data Hygiene | Checksums, immutable raw files, versioned outputs | Raw files are checksum‑verified on download; each transformation writes a new versioned file under `data/processed/`. |
| IV. Single Source of Truth | Every figure/statistic ↔ one data row & one code block | Figures are generated directly from the CSV/JSON artifacts; tables are exported from the same objects. |
| V. Versioning Discipline | Content‑hash tracking | After each major artifact creation a SHA‑256 hash is recorded in the project state file. |
| VI. Dynamic Network Topology Validation | Sliding‑window GRN, edge‑weight Δ, hub stability, permutation test, motif validation | Implemented in Phases 1‑2 (tasks 4‑7) with explicit z‑score normalization, motif‑enrichment filtering, and permutation testing. |
| VII. Disorder Vulnerability Correlation Rigor | GWAS mapping, enrichment, matched background, independent validation | Implemented in Phases 3‑4 (tasks 8‑10) with matched‑gene background, Benjamini‑Hochberg correction, and replication on an independent open cohort. |

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
│   ├── define_windows.py      # creates observed developmental windows
│   ├── infer_grn.py           # FR‑003, FR‑004, FR‑006 (motif validation)
│   ├── rewiring.py            # FR‑004, FR‑010, SC‑003, SC‑005
│   └── plotting.py            # FR‑007
├── clinical_analysis/
│   ├── gwas_mapping.py        # FR‑005
│   ├── enrichment.py          # FR‑005, FR‑006, FR‑009, FR‑013
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
**Structure Decision**: A single‑project layout (Option 1) because the workflow is a linear pipeline with clear module boundaries.

## Implementation Phases & Mapping to Functional / Success Criteria

| Phase | Script(s) | FR(s) addressed | SC(s) addressed | Key Outputs |
|-------|-----------|-----------------|-----------------|--------------|
| **Phase 0 – Data Acquisition & QC** | `src/data_pipeline/setup_data.py` → `src/data_pipeline/preprocess.py` | FR‑001, FR‑002, FR‑011, FR‑012 | SC‑001, SC‑002, SC‑007, SC‑008 | `integrated_atlas.h5ad`, checksum manifest, LISI score, QC report |
| **Phase 1 – Define Observed Developmental Windows** | `src/network_inference/define_windows.py` | FR‑003 (window definition), FR‑011 (gap detection) | SC‑007 (coverage detection) | `windows.yaml` (list of stage_id, start/end ages, cell counts) |
| **Phase 2 – GRN Inference & Motif Validation** | `src/network_inference/infer_grn.py` (GRNBoost2) <br> `src/network_inference/motif_enrichment.py` (pySCENIC) | FR‑003, FR‑004, FR‑006 | SC‑003, SC‑005 | `{stage_id}.json` (raw GRN) and `{stage_id}.json` (motif‑validated) |
| **Phase 3 – Rewiring Detection & Sensitivity** | `src/network_inference/rewiring.py` (z‑score edge Δ, hub stability, threshold sweep) | FR‑004, FR‑010 | SC‑005, SC‑003 | `rewiring_events.csv` (including `weight_delta_z`, `stability_score`) |
| **Phase 4 – GWAS Enrichment** | `src/clinical_analysis/gwas_mapping.py` → `src/clinical_analysis/enrichment.py` (matched background, hypergeometric, BH FDR, ≥ 5 000 permutations) | FR‑005, FR‑006, FR‑009, FR‑013 | SC‑004, SC‑003, SC‑009 | `disorder_enrichment.csv` (columns: disorder, vulnerability_window, odds_ratio, p_value, is_validated) |
| **Phase 5 – Independent Validation** | `src/clinical_analysis/validation.py` (independent open scRNA cohort + bulk BrainSpan proxy if available) | FR‑014 | SC‑006 | Validation flags added to `disorder_enrichment.csv` (`is_validated`) |
| **Phase 6 – Visualization & Reporting** | `src/network_inference/plotting.py` (Plotly, Cytoscape JSON) | FR‑007, FR‑008 | — | Figures (`network_{stage}.html`, `rewiring_heatmap.html`) and a markdown summary report |

### Additional Guarantees
- **Motif Validation**: Only edges with cis‑regulatory motif support survive to downstream rewiring analysis (FR‑006).  
- **Z‑Score Normalization**: Edge weights are standardized within each window before Δ computation (FR‑004).  
- **Matched Background**: Controls for gene length, baseline expression, and degree in enrichment tests (FR‑005).  
- **Pseudotime Within Windows**: Optional `scvelo`‑based pseudotime is computed *inside* each developmental window solely for cell‑type ordering; it is **not** used to define windows, addressing reviewer concerns about mixing calendar age with inferred trajectory.  
- **Multiple‑Comparison**: Benjamini‑Hochberg applied across all disorder tests (FR‑009).  
- **Permutation Reporting**: Zero‑permutation cases reported as `"p < 1/N"` where `N=5000` (FR‑013).  
- **Batch‑Effect Abort**: Pipeline halts with a clear log if LISI < 1.2 (FR‑012).  
- **Developmental‑Window Gap Handling**: `define_windows.py` checks each window for ≥ 10 cells; gaps are either linearly interpolated (if adjacent windows exist) or cause abort per FR‑011.  
- **Power Justification**: Simulated networks (50 k cells, 5 k TFs, expected odds‑ratio ≥ 1.5) yield > 80 % power to detect enrichment at p ≤ 0.05 with 5 000 permutations (methodology‑32aa8ec6).  

---
