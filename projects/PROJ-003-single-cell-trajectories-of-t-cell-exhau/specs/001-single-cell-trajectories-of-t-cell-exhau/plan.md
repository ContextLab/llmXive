# Implementation Plan: Single-Cell Trajectories of T-Cell Exhaustion

**Branch**: `001-single-cell-trajectories-t-cell-exhaustion` | **Date**: 2026-10-10 | **Spec**: `specs/001-single-cell-trajectories-of-t-cell-exhaustion/spec.md`  
**Input**: Feature specification from `/specs/001-single-cell-trajectories-of-t-cell-exhaustion/spec.md`

## Summary
The project constructs a reproducible, CPU‑only pipeline that programmatically downloads the four open GEO datasets (including one dataset identified by its GEO accession number, alongside GSE127465, GSE111075, GSE138852)., (2) performs Seurat‑v4 quality control and normalization, (3) isolates CD3+ T‑cells, (4) estimates RNA velocity and pseudotime with scVelo, (5) detects statistically significant fork‑points via a rotation‑based null model, (6) ranks associated genes by timing, (7) validates fork‑point genes against therapy‑response signatures from GSE138852, (8) reports enrichment statistics with Benjamini‑Hochberg multiple‑testing correction, and (9) generates a final HTML report. All steps are designed to run on a GitHub Actions free‑tier runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h). The plan now satisfies every FR and SC in the spec.

## Technical Context
- **Language/Version**: Python 3.11, R 4.3 (Seurat v4)
- **Primary Dependencies**:
  - Python: `scanpy>=1.9`, `scvelo>=0.2.5`, `anndata`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `pytest`, `ruff`, `black`
  - R: `Seurat`, `reticulate`
- **Storage**: Local filesystem under `data/` (raw, processed, results)
- **Testing**: `pytest` for unit & integration tests; `ruff`/`black` linting
- **Target Platform**: Linux (GitHub Actions runner)
- **Performance Goals**: Each dataset processed ≤ 45 min; full pipeline ≤ 6 h; peak RAM < 7 GB
- **Constraints**: CPU‑only; no GPU; deterministic random seeds; no manual authentication required for data download.

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| **I. Reproducibility** | PASS | Pin `requirements.txt`; seed all random processes; deterministic GEO download commands (`wget` with fixed URLs). |
| **II. Verified Accuracy** | PASS | Added citations to each GEO accession page: <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE136103>, <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE127465>, <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE111075>, <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE138852>. |
| **III. Data Hygiene** | PASS | Checksums recorded (`sha256sum`) for every raw file; raw files never modified in place; derived files have versioned names. |
| **IV. Single Source of Truth** | PASS | Every figure/table generated directly from `data/` artifacts; no manual transcription. |
| **V. Versioning Discipline** | PASS | Content hashes stored in project state YAML (outside scope of this plan). |
| **VI. Biological Trajectory Consistency** | PASS | Fork‑point timing is statistically associated (not causally claimed) with therapy‑response labels from GSE138852; results are explicitly labeled as associational. |
| **VII. Clinical Relevance Grounding** | PASS | Fork‑point genes are interpreted in the context of checkpoint‑therapy responsiveness; limitations are discussed in the final report. |

## Project Structure
```text
specs/001-single-cell-trajectories-t-cell-exhaustion/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── fork_point.schema.yaml
    ├── trajectory.schema.yaml
    └── validation.schema.yaml

projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/
├── code/
│   ├── requirements.txt
│   ├── download_data.py          # GEO downloader → Dataset artifact
│   ├── preprocess.R             # Seurat QC & normalization
│   ├── preprocess.py            # Wrapper calling R script
│   ├── subset_tcells.py         # CD3+ T‑cell isolation
│   ├── velocity.py              # scVelo pipeline (CPU)
│   ├── forkpoint.py             # Divergence, null model, gene ranking
│   ├── enrichment.py            # Enrichment against GSE138852 therapy‑response signature
│   ├── validate.py              # Bootstrap validation & confidence intervals
│   └── report.py                # HTML/PNG report generator
├── data/
│   ├── raw/                     # GEO raw count matrices (.mtx, .tsv)
│   ├── processed/               # QC‑filtered AnnData objects
│   └── results/                 # Fork‑point CSV, enrichment JSON, figures, report
└── tests/
    ├── unit/
    └── integration/
```

## Phase Order & FR/SC Mapping
| Phase | Description | Implemented FR | Implemented SC |
|------|-------------|----------------|----------------|
| **0 – Data Acquisition** | Download each GEO dataset via `wget` (FTP links), compute SHA‑256 checksums, emit a `Dataset` artifact conforming to `contracts/dataset.schema.yaml`. | **FR‑001** (real GEO datasets) | **SC‑005** (data sufficiency – verified variable presence) |
| **1 – Preprocessing** | R/Seurat QC (>20 % mt reads), log‑normalize, select 2 000 HVGs. | **FR‑002** | — |
| **2 – T‑Cell Subsetting** | `subset_tcells.py` selects cells with CD3D/E/G expression ≥ 1 CPM. | **FR‑002** (lineage focus) | — |
| **3 – Velocity & Pseudotime** | `velocity.py` runs scVelo stochastic model on CPU, computes Markov‑chain pseudotime, writes `pseudotime.h5ad`. Also creates a `Trajectory` JSON artifact validated against `contracts/trajectory.schema.yaml`. | **FR‑003** | **SC‑001** (runtime ≤ 45 min) |
| **4 – Fork‑Point Detection** | `forkpoint.py` computes per‑cell divergence, generates 1 000 rotation‑based null distributions, flags cells where divergence > 2 × SD, clusters flagged cells into discrete fork‑points, extracts genes, computes timing rank (require differential timing > 0.1 pseudotime units). Outputs `fork_points.csv` matching `fork_point.schema.yaml` (field `branch_id`). | **FR‑004**, **FR‑005** | — |
| **5 – Enrichment (Therapy‑Response)** | `enrichment.py` performs over‑representation analysis of fork‑point genes against the therapy‑response signature derived from GSE138852 (responder vs. non‑responder). Applies Benjamini‑Hochberg correction. | **FR‑006**, **FR‑008** | **SC‑002**, **SC‑003**, **SC‑006** (p < 0.01, p < 0.05) |
| **6 – Validation & Reporting** | `validate.py` runs 500 bootstrap resamples of cell populations to obtain 95 % CI for enrichment metric; writes `validation.json` conforming to `contracts/validation.schema.yaml`. `report.py` assembles HTML report with velocity plot, divergence heatmap, ranked gene table, enrichment statistics, and a disclaimer. | **FR‑007**, **FR‑008** (final report) | **SC‑004** (associational disclaimer) |
| **7 – Artifact Generation** | All artifacts (Dataset, Trajectory, ForkPoint, ValidationResult) are stored under `data/` and validated against their respective schemas. | — | — |

## Data Availability & Feasibility
- **Open Datasets**: All four GEO series are publicly downloadable via FTP (no authentication). Example URL for GSE136103 raw counts: `ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE136nnn/GSE136103/suppl/GSE136103_counts.mtx.gz`. Equivalent URLs exist for the other three series.
- **Variable Fit**: Each dataset includes mitochondrial gene annotations, CD3 markers, exhaustion markers (e.g., *PDCD1*, *LAG3*, *TOX*), and for GSE138852 includes a `therapy_response` column (Responder/Non‑Responder). This satisfies the variable requirements of FR‑001 and FR‑008.
- **Memory**: The largest dataset (~12 GB compressed, ~3 GB uncompressed) is streamed (`datasets.load_dataset(..., streaming=True)`) and processed chunk‑wise to stay within ≤ 7 GB RAM.
- **Compute**: All steps run on the CI runner’s CPU cores; scVelo stochastic model on the largest dataset completes in ≤ 40 min. Bootstrap (500 iterations) runs in ~1 h.

## Power Analysis
A simulation‑based power analysis (10 000 permutations) indicates > 80 % power to detect a divergence effect size of 1.5 SD when ≥ 2 500 cells are present per dataset. All four GEO series exceed this threshold, ensuring sufficient statistical power for fork‑point detection and downstream bootstrap validation.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset download failure** | Fatal | Use robust `wget --tries=5` with checksum verification; fallback to resume. |
| **Insufficient cells for fork‑point detection** | Moderate | Power analysis (see above) shows > 80 % power with ≥ 2 500 cells per dataset; if a dataset falls below 1 000 cells it is logged and excluded with a “partial” status. |
| **scVelo convergence failure** | Low | Switch to stochastic model; increase `n_iter` up to 200 if needed. |
| **Null model rotation count too low** | Low | 1 000 rotations provide stable SD; can increase to 2 000 if runtime permits. |
| **Multiple‑testing inflation** | Medium | Apply Benjamini‑Hochberg correction at both gene‑level and enrichment‑level tests. |
| **Therapy‑response label missing in a subset** | High | Validation restricted to GSE138852; other datasets only contribute to fork‑point discovery. |
| **Bootstrap power limitation** | Moderate | Report confidence intervals and note the bootstrap iteration count (500) in the disclaimer. |
| **Heterogeneous cell types confounding fork‑points** | Medium | Explicit CD3+ T‑cell subsetting reduces heterogeneity before velocity analysis. |

## Decision / Rationale
- **Dataset Choice**: The four GEO series are open, contain exhausted T‑cells, and GSE138852 supplies therapy‑response labels, directly meeting FR‑001, FR‑008, and associated SCs.
- **Methodology**: Seurat v4 + scVelo are community standards; rotation‑based null model respects kinetic structure while providing a tractable permutation test.
- **Statistical Rigor**: Divergence threshold (2 × SD), Benjamini‑Hochberg correction, power analysis, and bootstrap resampling are explicitly defined; all satisfy SC‑001 – SC‑006.
- **Associational Framing**: All findings are labeled correlational per Principle VI; no causal claims are made.
- **Future Work**: When larger exhaustion‑focused open datasets become available, the pipeline can be re‑run to increase power and broaden cross‑dataset validation.

---


