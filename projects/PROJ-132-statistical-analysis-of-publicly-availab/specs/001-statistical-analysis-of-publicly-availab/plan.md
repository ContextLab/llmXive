# Implementation Plan: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

**Branch**: `001-bird-migration-climate-correlation` | **Date**: 2024-10-14 | **Spec**: `specs/001-bird-migration-climate-correlation/spec.md`  
**Input**: Feature specification from `/specs/001-bird-migration-correlation/spec.md`

## Summary
The project will deliver a fully reproducible pipeline that (1) **streams** the open eBird Basic Dataset (EBD) and PRISM climate data (no full raw files are persisted), (2) preprocesses them into a 0.5° × 0.5° grid with weekly phenology metrics, observer‑effort covariates, and climate averages, (3) fits Generalized Additive Mixed Models (GAMMs) with species‑level random slopes, a **temporal AR(1) year random effect**, and a Gaussian Process (Matérn) spatial random effect, (4) conducts hierarchical **block‑permutation**‑based FDR‑corrected hypothesis testing preserving the hierarchical and spatial structure, (5) performs discrete centroid trajectory analysis on a Riemannian manifold with temporally‑aware **block‑permutation** for route‑shift significance and block‑bootstrap uncertainty quantification, and (6) generates all required success‑criterion metrics and figures. Every step is mapped to a functional requirement (FR‑001 – FR‑007) and a success criterion (SC‑001 – SC‑005). **All reported results are derived from real observations; no fabricated placeholder values are used.**

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `polars`, `numpy`, `scipy`, `geopy`, `datasets`, `filelock`, `pygam` (for GAMMs), `statsmodels` (fallback), `scikit‑learn`, `matplotlib`, `seaborn`  
- **Storage**: All raw files are **streamed**; only derived CSV/JSON artifacts are persisted under `data/`.  
- **Testing**: `pytest` with synthetic validation fixtures; schema validation after each phase.  
- **Target Platform**: GitHub Actions free‑tier (2 CPU cores, ≈ 7 GB RAM, ≈ 14 GB disk). Heavy GPU work (block‑bootstrap if > 1 800 s) will automatically off‑load to a Kaggle free GPU via the built‑in off‑load mechanism.  
- **Constraints**: No authentication‑gated data; streaming avoids RAM overflow. Memory usage < 2 GB via chunked processing.  
- **Scale/Scope**: Streamed eBird ‑2024 sample (≈ 5 k grid‑cell‑years after filtering) + PRISM climate layers for the same period.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| **I. Reproducibility** | All scripts are deterministic (seed pinned in `src/config.py`). Data are fetched from versioned URLs; the pipeline can be re‑run on a fresh CI runner. |
| **II. Verified Accuracy** | Dataset URLs are taken from the verified list; a pre‑run checksum step validates integrity before any processing. |
| **III. Data Hygiene** | Raw streams are never written to disk; any persisted files have SHA‑256 checksums recorded in `state/projects/...yaml`. Every transformation writes a new file; provenance mapping (`data/provenance/row_mapping.json`) links processed rows back to original checklist IDs. |
| **IV. Single Source of Truth** | Every figure/table is generated directly from the CSV/JSON outputs in `data/output/`. No hand‑typed numbers are permitted. |
| **V. Versioning Discipline** | After each major phase the state file is updated with content hashes for all newly created artifacts. |
| **VI. Ecological Data Provenance** | Raw eBird and PRISM observations are streamed unchanged; filtering steps and grid aggregation are logged in provenance files. |
| **VII. Statistical Model Transparency** | GAMM formulae, random‑effect structures, spline bases, temporal AR(1) correlation, and GP hyper‑parameters are fully specified in `src/models/gamm.py`. Exact package versions are pinned in `requirements.txt`. |

## Project Structure
```text
specs/001-bird-migration-correlation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── phenology_metric.schema.yaml
│   ├── gamm_results.schema.yaml
│   ├── trajectory.schema.yaml
│   └── output.schema.yaml
└── tasks.md   # generated later by /speckit-tasks

src/
├── config.py                # seeds, paths, constants
├── data/
│   ├── download.py          # streams eBird & PRISM (no full raw files)
│   ├── preprocess.py        # filtering, grid aggregation, phenology & effort calc
│   └── stream_utils.py      # chunked readers for low‑memory operation
├── models/
│   ├── gamm.py              # GAMM fitting, diagnostics, GP inclusion, temporal AR(1)
│   └── manifold.py          # discrete centroid & trajectory analysis
├── analysis/
│   ├── correlation.py       # hierarchical block‑permutation, FDR correction, power
│   └── routes.py            # shift vectors, block‑bootstrap CI
├── utils/
│   ├── locks.py             # file‑based lock via `filelock`
│   └── logging.py
└── cli/
    └── run_pipeline.py      # orchestrates all phases

tests/
├── unit/
├── integration/
└── contract/
```

## Complexity Tracking
| Feature | Reason for Inclusion | Simpler Alternative Rejected |
|---------|----------------------|------------------------------|
| **Discrete centroid trajectory on S²** | Required by FR‑006 to detect non‑linear route shifts. | Linear Euclidean regression would ignore spherical geometry. |
| **File‑based locking** | Needed to avoid race conditions if CI re‑triggers while a previous run holds files. | No locking could corrupt intermediate CSVs. |
| **Streaming via `datasets`** | Prevents OOM on the 7 GB RAM limit (eBird > 10 GB). | Full in‑memory load would crash the runner. |
| **Temporal AR(1) random effect** | Addresses methodological concern about ignored temporal autocorrelation (methodology‑e1e72cf3). | Ignoring temporal structure would inflate Type I error. |
| **Block‑permutation scheme** | Guarantees valid p‑values for hierarchical data (methodology‑ec45e0fd). | Unrestricted permutations break exchangeability. |
| **Block‑bootstrap for route CI** | Preserves autocorrelation when estimating CI for route shifts (FR‑007). | Simple i.i.d. bootstrap would underestimate variance. |

## Phase Breakdown (mapping FR/SC)

| Phase | Tasks | FR addressed | SC addressed |
|-------|-------|--------------|--------------|
| **0 A Power Planning** | **0.A1** Perform an **a priori** power analysis using the expected sample size (≈ 5 k grid‑cell‑years) to compute Minimum Detectable Effect Size (MDES) for a 0.15 day/°C effect at **≥ 80 % power**; record target sample size. | — | **SC‑001** (a priori) |
| **0 Validation & Sync** | **0.1** Verify URLs & checksums; **0.2** Stream download eBird & PRISM (no full raw files persisted); **0.3** Update state hashes; **0.4** **Validate streamed raw schema against `contracts/dataset.schema.yaml`**; **0.5** Record provenance. | **FR‑001** (download & cache) | — |
| **1 Preprocessing** | **1.1** Stream eBird, filter migratory species (Cornell list), 2020‑2024, and extract observer effort fields (`checklist_duration`, `observer_count`). **1.2** Apply **effort weighting** (log‑duration × observer count) when aggregating counts. **1.3** Assign each observation to a 0.5° grid cell (C‑squares). **1.4** Aggregate to weekly counts per species‑grid‑week. **1.5** Compute phenology metrics (first, median, stopover) and effort‑adjusted counts. **1.6** Stream PRISM, compute weekly climate averages; impute missing cells via inverse‑distance weighting (flagged). **1.7** Join climate to phenology; write `data/processed/phenology_climate.csv`. **1.8** **Validate output against `contracts/phenology_metric.schema.yaml`**. **1.9** Generate provenance file linking processed rows to original checklist IDs. | **FR‑002**, **FR‑003** | **SC‑002** (data‑coverage) |
| **2 Modeling** | **2.1** Fit GAMMs per species‑year with smooth temperature & precipitation, random intercepts & slopes, **temporal AR(1) year effect**, and GP (Matérn) spatial effect (always included). **2.2** Compute Moran’s I on residuals (post‑hoc). **2.3** Perform **hierarchical block‑permutation**: observations are shuffled **within species‑grid blocks while preserving spatial adjacency and temporal order** for each coefficient; generate null distributions. **2.4** Apply Benjamini–Hochberg FDR correction (FR‑005). **2.5** Record convergence status, AIC, R², residual Moran’s I, and whether temporal effect was included. **2.6** **Validate results against `contracts/gamm_results.schema.yaml`**. | **FR‑004**, **FR‑005** | **SC‑001** (power), **SC‑003** (convergence) |
| **3 Route & Uncertainty** | **3.1** Compute weekly migration centroids per species‑year. **3.2** Represent centroids on the unit sphere \(S^2\); compute great‑circle displacement vectors. **3.3** Perform **temporally‑aware block‑permutation** of years (swap contiguous year blocks) with 10 000 shuffles for shift significance, preserving temporal autocorrelation. **3.4** Conduct **block bootstrap** (4‑week blocks, 1 000 resamples) for 95 % CI of shift magnitude. **3.5** **Validate trajectory output against `contracts/trajectory.schema.yaml`**. | **FR‑006**, **FR‑007** | **SC‑004** (CI width) |
| **4 Reporting** | **4.1** Summarize success metrics (SC‑001 – SC‑005). **4.2** Generate figures (phenology vs. temperature, route shift maps, residual Moran plots). **4.3** Write `pipeline_report.json`. | — | **SC‑005** (runtime) |
| **5 State Sync** | After each phase, hash new artifacts and update `state/projects/...yaml`. | — | — |

## Success Criteria & Fallbacks
| Metric | Target | Measurement |
|--------|--------|-------------|
| **SC‑001** – Power | ≥ 80 % power to detect 0.15 day/°C | A priori simulation (Phase 0 A) |
| **SC‑002** – Data Coverage | ≥ 95 % cells “sufficient” | Proportion after preprocessing |
| **SC‑003** – Convergence | ≥ 90 % GAMM fits converged ≤ 600 s | Log of convergence status |
| **SC‑004** – CI Width | ≤ 7 days 95 % CI for shift | Block‑bootstrap CI |
| **SC‑005** – Runtime | ≤ 6 h total pipeline | `pipeline_report.json` runtime field |

---



## 5 Compute Strategy
- **CPU‑First** – All streaming, preprocessing, GAMM fitting, and trajectory calculations run on the CI runner’s 2‑core CPU.  
- **GPU Offload** – Triggered only for the block‑bootstrap step when runtime > 1 800 s. The same Python code (with `device="cuda"`) will be executed on a Kaggle free GPU; no code duplication.  
- **Memory Management** – Streaming (`datasets` with `streaming=True`) ensures < 2 GB RAM at any point. Intermediate CSVs are written incrementally.  
- **Locking** – `filelock` protects concurrent writes to `data/processed/`.  

## 6 Decision Rationale
- **Dataset Choice** – PRISM is the only verified, land‑based climate source covering 2020‑2024; Daymet was omitted because it lacks a verified URL.  
- **Statistical Method** – GAMMs provide flexibility for non‑linear climate effects while accommodating random slopes, **temporal AR(1) correlation**, and spatial GP. The GP is included a priori to avoid post‑hoc model selection bias.  
- **Manifold Analysis** – Discrete centroid approach respects the spherical geometry of Earth and works with sparse grid data, unlike continuous Fréchet mean methods that assume dense sampling.  
- **Effort Adjustment** – Weighting by checklist duration and observer count mitigates observer‑effort bias, preserving construct validity.  
- **Reproducibility** – Every random process (e.g., bootstrap, permutation) is seeded; all library versions are pinned in `requirements.txt`.  

All results are derived from real observations; **no fabricated numbers** are used.  

---



## 7. Reproducibility Guarantees
- All random seeds are fixed in `src/config.py`.  
- Data are fetched from the exact URLs listed above; a checksum step validates integrity before any processing.  
- The pipeline is orchestrated by `src/cli/run_pipeline.py` and can be re‑run on a fresh GitHub Actions runner without manual intervention.  

---



## 8. Constitution Alignment
| Principle | Evidence in Plan |
|-----------|-----------------|
| I. Reproducibility | Deterministic scripts, seeded, streaming data, full CI reproducibility. |
| II. Verified Accuracy | URLs verified, checksum validation before processing. |
| III. Data Hygiene | Streaming only, provenance file, SHA‑256 hashes recorded. |
| IV. Single Source of Truth | All figures/tables generated directly from CSV/JSON outputs. |
| V. Versioning Discipline | State file updated with content hashes after each phase. |
| VI. Ecological Data Provenance | Raw eBird/PRISM streamed unchanged; filtering logged. |
| VII. Statistical Model Transparency | GAMM code fully specified, package versions pinned. |
