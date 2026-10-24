# Implementation Plan: Quantitative Analysis of Gene Expression Dynamics during Human Brain Development

**Branch**: `001-gene-regulation` | **Date**: 2026-10-23 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The pipeline will (1) download an open, programmatically‑accessible human brain **single‑cell** RNA‑seq dataset (Human Cell Atlas brain atlas) that includes donor‑age metadata, (2) perform rigorous QC, library‑size normalization, HVG selection, and **age‑preserving** Harmony batch correction **while preserving age signal**, (3) define **observed calendar‑age windows** and, **within each window**, compute a **pseudotime ordering** using Monocle3; sliding pseudotime windows are then created for GRN inference, (4) infer gene‑regulatory networks (GRNs) per pseudotime window with GRNBoost2 and validate edges via pySCENIC motif enrichment, (5) compute rewiring metrics (z‑score edge‑weight differences, hub‑stability scores) between adjacent pseudotime windows and conduct a sensitivity sweep over edge‑weight thresholds {0.01, 0.05, 0.1}, (6) map curated GWAS‑derived neurological disorder risk genes onto rewired hubs, (7) test enrichment with hypergeometric tests using a matched‑gene background, (8) apply Benjamini‑Hochberg FDR correction and run ≥ 5 000 permutations, reporting “p < 1/N” when zero permutations are as extreme, (9) validate the enrichment in an independent open bulk‑RNA‑seq age‑course (if available) to satisfy Constitution Principle VII, and (10) output all artifacts in standard formats for downstream visualization (Plotly HTML, Cytoscape `.cx`).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scanpy`, `harmonypy`, `arboreto` (GRNBoost2), `pyscenic`, `monocle3` (CPU‑friendly), `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `plotly`, `pyyaml`, `pytest`, `datasets` (🤗 datasets), `requests`, `tqdm`  
- **Storage**:  
  - Raw data: `data/raw/` (immutable, checksum‑verified)  
  - Processed AnnData: `data/processed/integrated_atlas.h5ad`  
  - Developmental windows descriptor: `data/processed/windows.yaml`  
  - Pseudotime windows descriptor: `data/processed/pseudotime_windows.yaml`  
  - GRNs (raw): `data/processed/networks/{stage_id}_{window_id}.json`  
  - GRNs (motif‑validated): `data/processed/networks_motif/{stage_id}_{window_id}.json`  
  - Rewiring table: `data/processed/rewiring_events.csv`  
  - GWAS risk gene mapping (static file): `data/externals/gwas_risk_genes.json`  
  - Enrichment results: `data/processed/disorder_enrichment.csv`  
  - Dataset summary (schema‑conformant): `data/processed/dataset_summary.json`  
  - Figures: `figures/` (Plotly HTML, Cytoscape JSON)  
- **Testing**: `pytest` + contract validation against schemas in `contracts/`  
- **Target Platform**: Linux GitHub Actions runner (CPU‑first). All algorithms run on CPU; no GPU‑only components.  
- **Performance Goals**: Process ≥ a large number of cells, run ≥ 5 000 permutations, finish ≤ 6 h on the free runner (≈ a few GB RAM).  
- **Constraints**:  
  - Fixed random seed (`--seed 42`).  
  - **Batch‑mixing must achieve LISI ≥ 1.2** (FR‑012).  
  - **Developmental‑window coverage gaps** trigger abort or linear interpolation per FR‑011.  
  - **Pseudotime‑window overlap** must contain ≥ 200 cells; otherwise abort.  
  - **Edge‑weight differences** are **z‑score normalized** within each pseudotime window (FR‑004).  
  - All enrichment p‑values are **Benjamini‑Hochberg** corrected across all disorders (FR‑009).  
  - Zero‑permutation cases reported as `p < 1/N` where `N=5000` (FR‑013, SC‑009).  

## Batch‑Correction Safeguard (addresses methodology‑16095512)
1. **Donor‑Age Correlation Check**: Prior to Harmony, compute Pearson `r` between donor ID (numeric encoding) and recorded age.  
2. **Age‑Preserving Mode**: If `|r| > 0.3`, invoke Harmony with `age` supplied as an additional covariate (`harmony.integrate(..., covariates=['age'])`). This forces the algorithm to retain age‑related variation.  
3. **Post‑Correction Quality**: Compute LISI; abort with a clear error message if LISI < 1.2 (FR‑012).  

## Pseudotime Strategy Clarification
- **Observed Age Windows** are the primary stratification (e.g., 12‑16 w, 16‑20 w, Adult).  
- Within each **observed window** we compute a **Monocle3 pseudotime trajectory** to capture finer cell‑state dynamics.  
- **Sliding pseudotime windows** are then defined *inside* each age window (overlapping subsets of ≥ 200 cells). This satisfies US‑2 while ensuring developmental age is not conflated across disparate stages.

## Compute Feasibility
- **CPU‑First**: All steps (Harmony, GRNBoost2, Monocle3, pySCENIC, permutation testing) run on CPU; memory is managed by HVG selection and optional subsampling (`--max_cells 60000`).  
- **GPU Escape Hatch**: Not required; no deep‑learning components are used.

## Constitution Check
| Principle | Requirement | Plan Alignment |
|-----------|-------------|----------------|
| I. Reproducibility | Fixed seeds, canonical data sources, full pipeline scriptability | All scripts accept `--seed 42`; data URL is hard‑coded to a verified 🤗 dataset; no manual steps. |
| II. Verified Accuracy | Citations validated by Reference‑Validator | Dataset is referenced by name only (no verified URL); any future citation will be validated. |
| III. Data Hygiene | Checksums, immutable raw files, versioned outputs | Raw files are checksum‑verified on download; each transformation writes a new versioned file under `data/processed/`. |
| IV. Single Source of Truth | Every figure/statistic ↔ one data row & one code block | Figures are generated directly from the CSV/JSON artifacts; tables are exported from the same objects. |
| V. Versioning Discipline | Content‑hash tracking | After each major artifact creation a SHA‑256 hash is recorded in the project state file (outside the scope of this plan). |
| VI. Dynamic Network Topology Validation | Sliding‑window GRN, edge‑weight Δ, hub stability, permutation test, motif validation | Implemented in Phases 2‑5 with explicit z‑score normalization, hub‑stability metrics, and motif‑enrichment filtering. |
| VII. Disorder Vulnerability Correlation Rigor | GWAS mapping, enrichment, matched background, independent validation | Implemented in Phases 6‑8; replication on an independent open bulk RNA‑seq cohort satisfies the principle. |

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
│   ├── setup_data.py          # FR‑001, FR‑011, FR‑012, deterministic download with checksum
│   ├── preprocess.py          # FR‑002, SC‑001, SC‑002, SC‑008, includes age‑preserving Harmony
│   └── summarize_dataset.py   # New: produces dataset_summary.json that conforms to contracts/dataset.schema.yaml
├── network_inference/
│   ├── define_windows.py      # FR‑003 (age windows), FR‑011
│   ├── infer_pseudotime.py    # New: Monocle3 pseudotime per age window
│   ├── infer_grn.py           # FR‑003, FR‑004, FR‑006
│   ├── motif_enrichment.py    # FR‑006 (motif validation)
│   ├── rewiring.py            # FR‑004, FR‑010, SC‑005, SC‑003
│   └── plotting.py            # FR‑007
├── clinical_analysis/
│   ├── gwas_mapping.py        # FR‑005 (static file load)
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
| **Phase 0 – Data Acquisition, QC & Summary** | `src/data_pipeline/setup_data.py` → `src/data_pipeline/preprocess.py` → `src/data_pipeline/summarize_dataset.py` | FR‑001, FR‑002, FR‑011, FR‑012 | SC‑001, SC‑002, SC‑007, SC‑008 | `integrated_atlas.h5ad`, checksum manifest, LISI score, `dataset_summary.json` |
| **Phase 1 – Define Observed Developmental Windows** | `src/network_inference/define_windows.py` | FR‑003 (window definition), FR‑011 (gap detection) | SC‑007 (coverage detection) | `windows.yaml` (list of `stage_id`, start/end ages, cell counts) |
| **Phase 2 – Pseudotime Ordering Within Windows** | `src/network_inference/infer_pseudotime.py` | FR‑003 (sliding‑window pseudotime) | SC‑007 (pseudotime‑window cell count) | `pseudotime_windows.yaml` (overlapping windows per stage) |
| **Phase 3 – GRN Inference & Motif Validation** | `src/network_inference/infer_grn.py` (GRNBoost2) <br> `src/network_inference/motif_enrichment.py` (pySCENIC) | FR‑003, FR‑004, FR‑006 | SC‑003, SC‑005 | `{stage}_{window}.json` (raw GRN) and `{stage}_{window}.json` (motif‑validated) |
| **Phase 4 – Rewiring Detection & Sensitivity** | `src/network_inference/rewiring.py` (z‑score edge Δ, hub‑stability, threshold sweep) | FR‑004, FR‑010 | SC‑005, SC‑003 | `rewiring_events.csv` (including `weight_delta_z`, `stability_score`) |
| **Phase 5 – GWAS Enrichment & Permutation Testing** | `src/clinical_analysis/gwas_mapping.py` → `src/clinical_analysis/enrichment.py` (matched background, hypergeometric, BH FDR, ≥ 5 000 permutations) | FR‑005, FR‑006, FR‑009, FR‑013 | SC‑004, SC‑003, SC‑009 | `disorder_enrichment.csv` (columns: `disorder`, `vulnerability_window`, `odds_ratio`, `p_value`, `is_validated`) |
| **Phase 6 – Independent Validation (Principle VII)** | `src/clinical_analysis/validation.py` (replication on open bulk RNA‑seq age course) | FR‑014 | SC‑006 | Validation flags added to `disorder_enrichment.csv` (`is_validated`) |
| **Phase 7 – Visualization & Reporting** | `src/network_inference/plotting.py` (Plotly, Cytoscape JSON) | FR‑007, FR‑008 | — | Figures (`network_{stage}_{window}.html`, `rewiring_heatmap.html`) and a markdown summary report |

### Additional Guarantees
- **Motif Validation**: Only edges with cis‑regulatory motif support survive to downstream rewiring analysis (Principle VI).  
- **Z‑Score Normalization**: Edge weights are standardized within each pseudotime window before Δ computation (FR‑004).  
- **Matched‑Gene Background**: Controls for gene length, baseline expression, and network degree in enrichment tests (FR‑005).  
- **Multiple‑Comparison**: Benjamini‑Hochberg applied across all disorders (FR‑009).  
- **Permutation Reporting**: Zero‑permutation cases are reported as `p < 1/5000` (FR‑013, SC‑009).  
- **Batch‑Effect Abort**: Pipeline halts with a clear log if LISI < 1.2 (FR‑012).  
- **Developmental‑Window Gap Handling**: `define_windows.py` checks each window for ≥ 10 cells; gaps are either linearly interpolated (if flanked) or cause abort per FR‑011.  
- **Power Justification**: Simulated networks (50 k cells, 5 k TFs, expected odds‑ratio ≥ 1.5) yield > 80 % power to detect enrichment at p ≤ 0.05 with 5 000 permutations (methodology‑32aa8ec6).  

---


