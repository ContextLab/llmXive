# Implementation Plan: Single-Cell Trajectories of T-Cell Exhaustion

**Branch**: `001-single-cell-trajectories-t-cell-exhaustion` | **Date**: 2026-10-10 | **Spec**: `specs/001-single-cell-trajectories-of-t-cell-exhaustion/spec.md`
**Input**: Feature specification from `/specs/001-single-cell-trajectories-of-t-cell-exhaustion/spec.md`

## Summary

A reproducible, CPU-only Python/R pipeline that (1) attempts programmatic acquisition of the four GEO datasets stipulated by FR-012 via NCBI GEO programmatic endpoints (GEO accession REST API + `https` supplementary-file URLs discovered from the accession metadata — **no fabricated URLs**; see Data Availability), (2) performs Seurat-v4 QC and normalization with a **fixed mitochondrial-gene annotation step** (the prior failure: `MT-` prefix never matched because gene symbols were not loaded), (3) isolates CD3+ T-cells, (4) estimates RNA velocity and pseudotime with scVelo on CPU, (5) detects statistically significant fork-points via a permutation null, (6) ranks fork-point genes by timing, (7) validates against a therapy-response signature with bootstrap resampling, BH correction, and a power analysis, and (8) generates a final HTML report with the associational disclaimer. This revision specifically repairs the four rejected tasks (T001–T004): the missing `data/results/` layout, the failing downloader, the non-functional QC filter, and the failing velocity script.

## Technical Context

- **Language/Version**: Python 3.11, R 4.3 (Seurat v4)
- **Primary Dependencies**: `scanpy>=1.9,<1.11`, `scvelo>=0.2.5,<0.3`, `anndata>=0.9`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`, `psutil`, `pytest`, `ruff`, `black`; R: `Seurat==4.x`
- **Storage**: Local filesystem under `data/` (raw, processed, results)
- **Testing**: `pytest` (unit + integration, tests must call the real module functions, not re-implement logic); `ruff check . && black --check .` must pass and be evidenced in CI logs
- **Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, ≤6 h)
- **Performance Goals**: scVelo ≤45 min/dataset (FR-003); full pipeline ≤6 h; peak RAM <7 GB (logged via `psutil`, wall-clock via `time` — SC-001)
- **Constraints**: CPU-only, pinned seeds, no manual authentication for downloads
- **Project Type**: reproducible research pipeline (CLI scripts)

## Constitution Check

| Principle | Status | Action |
|-----------|--------|--------|
| **I. Reproducibility** | PASS | Pinned `code/requirements.txt`; fixed seeds in every stochastic step; downloads via canonical GEO accession endpoints resolved at run time from NCBI metadata (never hard-coded guessed URLs). |
| **II. Verified Accuracy** | PASS | No dataset URL is cited that has not been verified. The verified-datasets block confirms **no verified source exists** for GSE136103/GSE127465/GSE111075/GSE138852; research.md states this explicitly and cites no URL for them. GEO accession pages are referenced by accession ID only. |
| **III. Data Hygiene** | PASS | SHA-256 checksums recorded per raw file under `data/`; raw files immutable; every derivation writes a new file with documented provenance. |
| **IV. Single Source of Truth** | PASS | Every figure/statistic in the report is generated directly from `data/results/` artifacts by `code/report.py`; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes of artifacts recorded in the project state YAML; `updated_at` bumped on each artifact change. |
| **VI. Biological Trajectory Consistency** | PASS | The therapy-response signature used for enrichment is derived from response labels, not from the velocity signal used to build trajectories; predictor/predicted distinction maintained; all claims framed as associational (FR-009). |
| **VII. Clinical Relevance Grounding** | PASS | Fork-point genes are interpreted against checkpoint-therapy responsiveness; therapeutic-window implications and limitations discussed in the report. |

## Project Structure

```text
specs/001-single-cell-trajectories-of-t-cell-exhaustion/
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
│   ├── download_data.py      # GEO accession-metadata-driven downloader (T002 fix)
│   ├── preprocess.R          # Seurat QC & normalization
│   ├── preprocess.py         # Wrapper; MT-gene annotation fix (T003 fix)
│   ├── subset_tcells.py
│   ├── velocity.py           # scVelo CPU pipeline (T004 fix)
│   ├── forkpoint.py
│   ├── enrichment.py
│   ├── validate.py
│   ├── power_analysis.py     # FR-011
│   └── report.py
├── data/
│   ├── raw/.gitkeep
│   ├── processed/.gitkeep
│   └── results/              # T001 fix: REQUIRED directory, committed with .gitkeep
│       ├── fork_points/.gitkeep
│       ├── validation/.gitkeep
│       └── report/.gitkeep
├── logs/                     # execution logs incl. lint evidence
└── tests/
    ├── unit/
    │   ├── test_download.py
    │   ├── test_preprocess.py   # calls real preprocess module (T003 fix)
    │   ├── test_velocity.py
    │   └── test_forkpoint.py
    └── integration/
        └── test_pipeline.py
```

**Structure Decision**: single-project layout; the `data/results/` subtree is part of the committed skeleton so the required layout exists before any task runs (T001).

## Phase Order & FR/SC Mapping

| Phase | Description | FR | SC |
|------|-------------|----|----|
| **0 – Environment & Layout** | Create `data/results/{fork_points,validation,report}`; verify `ruff check . && black --check .` passes and record output in `logs/lint.txt`. | — | T001 repair |
| **1 – Data Acquisition (T002)** | `download_data.py` queries the NCBI GEO accession endpoint (`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<ACCESSION>&targ=self&form=text`) to discover supplementary file URLs at run time, downloads via `curl -L --retry 5`, verifies SHA-256, checks marker-gene presence (≥80%, FR-010), emits Dataset artifacts. On failure: log, mark dataset `unavailable`, continue — never fabricate a mirror. | FR-001, FR-010, FR-012 | SC-005 |
| **2 – Preprocessing (T003)** | `preprocess.py`/`preprocess.R`: load counts with **correct gene-symbol assignment** (read `genes.tsv`/features file; if var names are generic, map via the features file; if the dataset supplies gene IDs only, annotate mitochondrial genes via a bundled HGNC symbol map keyed on Ensembl IDs). Filter >20% mt reads, log-normalize, 2,000 HVGs. Unit tests call the real module. | FR-002 | — |
| **3 – T-Cell Subsetting** | CD3D/E/G expression threshold; skip datasets <1,000 cells with warning + "partial" status (edge case). | FR-002 | — |
| **4 – Velocity & Pseudotime (T004)** | `velocity.py`: scVelo stochastic model, `device` CPU, moments → velocities → velocity graph → Markov-chain pseudotime; retry alignment with higher regularization (up to 2) on convergence failure; "Alignment Failed" status halts cross-dataset validation for that dataset. Emits Trajectory artifacts. Wall-clock + `psutil` memory logged. | FR-003 | SC-001 |
| **5 – Fork-Point Detection** | `forkpoint.py`: per-cell divergence; 1,000-permutation null (topology shuffled, splicing kinetics preserved); significance p<0.01; low-confidence flag when divergence <1.5 SD of null; cluster significant cells into branch_ids; extract genes; timing rank with differential timing >0.1 pseudotime units; output CSV (gene_symbol, branch_id, timing_rank). | FR-004, FR-005 | — |
| **6 – Power Analysis** | `power_analysis.py`: simulation-based power for divergence and enrichment tests (80% power, α=0.05); abort with explicit report if insufficient. | FR-011 | SC-007 |
| **7 – Enrichment & Validation** | `enrichment.py`: Fisher's exact test + two-sided t-test of fork-point-gene enrichment in the therapy-response signature (derived from GSE138852 response labels if available; if the label column is absent at run time, the step reports the gap rather than fabricating), BH correction, p<0.01. `validate.py`: 1,000 bootstrap resamples, 95% CIs, Spearman cross-dataset correlation of timing ranks. | FR-006, FR-008 | SC-002, SC-003, SC-006 |
| **8 – Reporting** | `report.py`: heatmap of top fork-point genes across datasets with bootstrap CIs, ranked gene table, enrichment statistics, runtime/memory table, and the FR-009 associational disclaimer. | FR-007, FR-009 | SC-004 |

## Data Availability & Feasibility (honest statement)

- **No verified source exists** for GSE136103, GSE127465, GSE111075, or GSE138852 in the verified-datasets block. The plan therefore does NOT hard-code any download URL for them. Instead, Phase 1 resolves supplementary-file URLs at run time from the official NCBI GEO accession metadata endpoint. If a dataset cannot be fetched that way, it is marked `unavailable`, the run proceeds with the remainder, and the report records the gap — the implementer must never substitute a fabricated mirror or synthetic stand-in (fabrication gate).
- **Variable fit**: FR-010's marker check (PD-1, metabolic markers, exhaustion signatures, therapy-response labels, ≥80% present) is executed on the real downloaded data; the therapy-response label is expected only in GSE138852 per the spec's assumption, and its actual presence is verified, not assumed.
- **Compute**: all steps CPU-only; largest dataset processed in chunks to stay under 7 GB RAM; scVelo ≤45 min/dataset; total ≤6 h.
- **Scope-escalation path**: if zero of the four datasets are retrievable, the mismatch is reported for scope revision rather than answered with different data.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GEO supplementary files unreachable/unauthenticated | Fatal for that dataset | Run-time URL discovery from accession metadata; retry ×5; mark `unavailable`; report gap; never fabricate. |
| Gene symbols not loaded (T003 root cause) | QC filter no-ops | Explicit features-file loading + Ensembl→symbol MT-gene map; integration test asserts the filter actually removes cells on a fixture with MT genes. |
| scVelo failure (T004) | Pipeline halt | Stochastic model, bounded retries, informative traceback logged; per-dataset isolation so other datasets still complete. |
| Missing therapy-response labels | Enrichment impossible | Report the gap explicitly; restrict validation to available labels; do not synthesize labels. |
| Multiple-testing inflation | False positives | BH correction at gene and enrichment levels. |
| Power insufficient | Invalid inference | FR-011 power analysis aborts with explicit message. |

## Decision / Rationale

- **No fabricated URLs**: the verified-datasets block found no verified source for any of the four GSE accessions; the plan resolves real URLs from NCBI's own accession endpoint at run time and reports failures honestly.
- **CPU-first**: scVelo stochastic + scanpy run faithfully on CPU; no GPU escape hatch needed.
- **Repairs T001–T004** by committing `data/results/`, fixing the downloader, fixing gene-symbol/MT annotation, fixing the velocity script, and making unit tests exercise the real modules with lint evidence recorded in `logs/`.

---
