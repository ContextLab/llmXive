# Implementation Plan: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

**Branch**: `feature/motif-rsfc` | **Date**: 2026-10-10 | **Spec**: `specs/feature/motif-rsfc/spec.md`
**Input**: Feature specification from `specs/feature/motif-rsfc/spec.md`

## Summary

Build a reproducible CPU-only pipeline that (1) retrieves real resting-state fMRI from the verified OpenNeuro parquet mirror, (2) computes rsFC matrices (Schaefer-100-equivalent parcellation) and global efficiency, (3) enumerates 3-node and 4-node motifs in structural connectomes with degree-preserving nulls and z-scores, (4) runs partial Pearson/Spearman correlations with Bonferroni correction, permutation tests, VIF/pairwise-collinearity diagnostics, and a power analysis, and (5) generates `results.pdf` with the mandatory disclaimer.

**Scope inconsistency (surfaced for correction, per stage rules):** The spec's Data Access section names OpenNeuro ds001734 retrieved via `datalad`, but **no verified source exists for OpenNeuroDatasets/ds001734** (see Verified datasets block). The only verified OpenNeuro source is the `clane9/openneuro-fslr64k` parquet mirror, which is a preprocessed fMRI derivative on the fsLR-64k surface and **does not contain diffusion tractography**. Consequently:

- **rs-fMRI**: obtained from the verified parquet (real data).
- **Diffusion/structural connectomes**: NO verified open source is available; HCP (named in the constitution's Principle VI) is access-gated and cannot be fetched on CI. The pipeline will **not fabricate or synthesize structural connectomes** (the prior plan's synthetic-graph approach is rejected as a fabrication stand-in). The structural/motif stages are implemented, tested on unit-test fixtures (clearly labeled test graphs, never reported as results), and **gated**: if no real structural connectomes are downloadable, the pipeline logs the gap, skips motif–rsFC association testing, and the report states that the structural half of the research question could not be answered with obtainable data. This mismatch should be resolved at the spec level (either name a verified open diffusion dataset or reframe the question) — the plan does not silently substitute a different question.

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies** (pinned in `code/requirements.txt`): `numpy`, `scipy`, `pandas`, `networkx`, `matplotlib`, `statsmodels`, `reportlab`, `datasets`, `pyarrow`, `jsonschema`, `pytest`, `flake8`, `black`
- **Storage**: local filesystem (`data/raw/`, `data/processed/`, `data/logs/`, `results/`)
- **Testing**: `pytest` (unit, integration, contract)
- **Target Platform**: GitHub Actions free runner (2 CPU, ~7 GB RAM, ~14 GB disk, ≤6 h)
- **Performance Goals**: motif enumeration ≤ 300 s/subject (SC-002); PDF ≤ 2 min and ≤ 5 MB (SC-004)
- **Constraints**: CPU-first (no GPU method needed anywhere); seed = 42; no fabricated data
- **Project Type**: research pipeline (CLI scripts)

## Constitution Check

| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | ✅ | Pinned `requirements.txt`, seed 42, data fetched from the same verified canonical URL each run |
| II. Verified Accuracy | ✅ | Citations limited to the Verified datasets block; no invented URLs |
| III. Data Hygiene | ✅ | Raw parquet checksummed under `data/`; all derivations are new files with provenance |
| IV. Single Source of Truth | ✅ | Every figure/statistic traces to one `data/processed/` row and one `code/` block |
| V. Versioning Discipline | ✅ | Content hashes recorded; `updated_at` maintained by platform |
| VI. Structural Data Integrity | ✅ | Principle VI names HCP, which is access-gated; the gating behavior above honors the principle (no in-place modification, provenance metadata on any derived connectome) while the dataset mismatch is surfaced for spec correction |
| VII. Statistical Transparency | ✅ | All test parameters, seeds, library versions logged; full p-value tables in outputs |

## FR/SC Traceability

| Requirement | Plan Element(s) |
|-------------|-----------------|
| FR-001 | T002 (ingestion from verified parquet; missing-data skip + warning) |
| FR-002 | T004 (parcellation → binary undirected adjacency; gated on real structural input) |
| FR-003 | T005 (rsFC Pearson matrices, global efficiency) |
| FR-004 | T006 (3- and 4-node enumeration, ≥1000 Maslov–Sneppen nulls, z-scores, 300 s guard) |
| FR-005 | T007 (partial Pearson+Spearman controlling global degree, Bonferroni over 13 motifs, VIF ≥ 5 warning, pairwise \|r\| ≥ 0.9 flag, all p-values reported) |
| FR-006 | T007 (≥1000 label permutations, empirical p) |
| FR-007 | T008 (PDF: scatter + CI, coefficients, corrected p, permutation outcome, collinearity diagnostics) |
| FR-008 | T001/T017 (directory + `pipeline.log` machine-readable logging) |
| FR-009 | T008 (disclaimer string inserted and verified by PDF text search) |
| FR-010 | T007 (power analysis: N=50, α=0.05/13, power=0.80 — power value 0.80 per Wikipedia "Power (statistics)"; min detectable r; Type II error statement) |
| SC-001 | T002 validation (`cohort_actual ≥ 0.95 × cohort_target` check in manifest) |
| SC-002 | T006 timeout guard |
| SC-003 | T007 outputs p-values for all 13 motifs to log + JSON |
| SC-004 | T008 (≤ 2 min, ≤ 5 MB, DPI fallback) |
| SC-005 | T007/T008 power section fields |

## Project Structure

```
specs/feature/motif-rsfc/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── motif_profile.schema.yaml
│   ├── output.schema.yaml
│   └── structural_connectome.schema.yaml
└── tasks.md

code/
├── __init__.py
├── config.py            # paths, seed=42, constants
├── requirements.txt     # pinned deps
├── data_loader.py       # parquet streaming download, parcellation, rsFC
├── motif_analysis.py    # 3/4-node enumeration, nulls, z-scores, timeout guard
├── correlation_analysis.py  # partial corr, Bonferroni, permutation, VIF, power
├── report_generator.py  # ReportLab PDF
├── utils.py             # logging, constant validation, metadata writer
└── main.py

tests/
├── unit/ (test_motif.py, test_correlation.py)
├── integration/test_pipeline.py
└── contract/test_schemas.py

data/{raw,processed,logs}/    results/
.flake8    pyproject.toml    .pre-commit-config.yaml
```

**Structure Decision**: single-project layout; no services or front-ends needed.

## Task List

| ID | Task | Deliverable | FR/SC |
|----|------|-------------|-------|
| T001 | Directory setup: create `code/`, `tests/{unit,integration,contract}/`, `data/{raw,processed,logs}/`, `results/`, `state/` with `__init__.py`/`.gitkeep` files committed | Folder hierarchy visible in repo | FR-001, FR-008 |
| T002 | Data ingestion: stream the verified OpenNeuro parquet (`datasets` / direct parquet URL), select up to 50 subjects, record checksums, write `manifest.json`, enforce SC-001, skip+warn on missing data | `data/raw/` files + `manifest.json` | FR-001, SC-001 |
| T003 | Lint/format config: `.flake8`, `pyproject.toml` (Black), `.pre-commit-config.yaml`; verify `flake8` and `black --check` pass on `code/` | Config files, clean lint run | FR-008 |
| T004 | Parcellation: map real structural inputs (if obtainable) to binary undirected 100-node adjacency with provenance metadata; if none obtainable, emit explicit gating log — no synthetic stand-in | `structural.npy` + `metadata.json` per subject, or gated skip | FR-002 |
| T005 | Functional metrics: Pearson rsFC matrices → `rsfc.npy`; mean strength; global efficiency | `rsfc.npy`, `subject_metrics.csv` | FR-003 |
| T006 | Motif quantification: enumerate 3- and 4-node motifs, ≥1000 degree-preserving nulls, z-scores, 300 s guard, zero-variance/disconnected-graph handling | `motif_profile.json` per subject | FR-004, SC-002 |
| T007 | Statistics: partial Pearson/Spearman vs. strength & efficiency controlling global degree, Bonferroni (13 motifs), ≥1000 permutations, VIF + pairwise \|r\| flags, power analysis (N=50, α=0.05/13, power=0.80) | `correlation_results.json` (schema-valid) | FR-005, FR-006, FR-010, SC-003, SC-005 |
| T008 | Reporting: `results.pdf`, one page per motif (scatter + 95% CI, coefficients, raw/corrected/empirical p, VIF, pairwise correlations), disclaimer string + text-search verification, power section, ≤5 MB / ≤2 min | `results/results.pdf` | FR-007, FR-009, SC-004 |
| T009 | Data-model documentation: `specs/feature/motif-rsfc/data-model.md` covering entities, relationships, file formats, manifest schema | `data-model.md` | FR-008 |
| T010 | Structural metadata: per-subject `metadata.json` conforming to `structural_connectome.schema.yaml` (provenance, seed, status) | `metadata.json` files | FR-002, FR-008 |
| T011 | Contract tests: `jsonschema` validation of manifest, motif profiles, correlation results, metadata | Passing test suite | FR-008 |
| T017 | Utils/logging: complete `utils.py` (constant validation of seed=42, Bonferroni α, permutation count, VIF threshold; library-version logging; structured logger) and a real `data/logs/pipeline.log` produced by a pipeline run | `utils.py`, `pipeline.log` | FR-008, FR-010 |

## Complexity Tracking

No constitution violations. The structural-data gating is not a simplification of the science: it is the honest handling of a data-availability mismatch that the spec must resolve.
