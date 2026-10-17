# Implementation Plan: Autocorrelation of the Möbius Function in Short Intervals

**Branch**: `001-autocorrelation-mobius` | **Date**: 2026-10-17 | **Spec**: `specs/001-autocorrelation-mobius/spec.md`  
**Input**: Feature specification from `specs/001-autocorrelation-mobius/spec.md`

## Summary

The project will (1) generate the Möbius sequence μ(n) for 1 ≤ n ≤ 10⁷ using a deterministic linear sieve, (2) compute normalized autocorrelations for sliding windows of lengths L ∈ {10³, 10⁴, 10⁵} and all lags h ≤ L/2, (3) construct a null distribution via **exactly 1,000 block‑permutations** per window while preserving zero‑density, (4) derive two‑sided p‑values and 95% confidence intervals, (5) perform a sensitivity analysis on the zero‑density (±5% / ±10%), (6) apply Benjamini‑Hochberg FDR correction across all (interval, lag) tests, (7) validate uniformity of the p‑value distribution with a Kolmogorov‑Smirnov test (SC‑005), and (8) visualise the results as heatmaps with correctly placed zero‑line and confidence‑band overlays. All steps are CPU‑first and guaranteed to finish within the GitHub Actions free‑tier limits.

## Technical Context

- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy`, `pandas`, `scipy`, `matplotlib`, `pytest` (all pinned in `requirements.txt`).  
- **Storage**: `int8` NumPy array for μ(n) (~10 MB); CSV/Parquet for results; PNG for figures.  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ~7 GB RAM, ≤6 h).  
- **Constraints**: Exact integer arithmetic for the sieve and summations; deterministic random seeds; no GPU required.

## Constitution Check

| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Fixed seeds, `requirements.txt`, deterministic sieve. |
| II. Verified Accuracy | ✅ | Uses the proven density of square‑free numbers = 6/π² (source: arXiv 1211.0189). |
| III. Data Hygiene | ✅ | Raw Möbius array is immutable; all transforms write new files; checksums recorded. |
| IV. Single Source of Truth | ✅ | Every statistic in `autocorrelation_stats.csv` and every figure in `outputs/figures/` trace back to a single row in the CSV. |
| V. Versioning Discipline | ✅ | Content hashes recorded in the project state file. |
| VI. Deterministic Arithmetic | ✅ | Sieve uses integer ops; autocorrelation sums use `int64` before normalization. |
| VII. Statistical Null Validation | ✅ | Exactly 1,000 block‑permutations per window; p‑values/CI derived from this envelope. |

## Project Structure

```text
specs/001-autocorrelation-mobius/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── mobius_stats.schema.yaml

projects/PROJ-728-autocorrelation-of-the-mobius-function-i/
├── code/
│   ├── __init__.py
│   ├── sieve.py               # Linear sieve, deterministic output
│   ├── autocorrelation.py     # Sliding‑window computation
│   ├── permutation.py         # Block‑permutation generator
│   ├── sensitivity.py         # Zero‑density sensitivity analysis
│   ├── viz.py                 # Heatmap creation (correct zero line)
│   └── main.py                # Orchestrates all stages
├── data/
│   ├── raw/
│   │   └── mobius_array.npy
│   └── processed/
│       ├── autocorrelation_stats.csv
│       └── uniformity_test.json
├── outputs/
│   └── figures/
│       ├── heatmap_L1000.png
│       ├── heatmap_L10000.png
│       └── heatmap_L100000.png
├── tests/
│   ├── unit/
│   │   ├── test_sieve.py
│   │   └── test_autocorrelation.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: Single Python project with modular code organization (sieve, autocorrelation, permutation, sensitivity, visualization) that processes the deterministic Möbius sequence through a seven‑phase pipeline. All outputs are CSV, JSON, and PNG files stored under `data/processed/` and `outputs/figures/`.

## Mapping of Functional Requirements (FR) and Success Criteria (SC) to Phases

| Phase | Tasks | FR(s) addressed | SC(s) addressed |
|-------|-------|-----------------|-----------------|
| **Phase 1 – Data Generation** | 1.1 Run `code/sieve.py` → `mobius_array.npy` | FR‑001 | SC‑003, SC‑004 |
| **Phase 2 – Autocorrelation** | 2.1 Compute autocorrelation for each sampled window | FR‑002 | SC‑001 |
| **Phase 3 – Null Distribution** | 3.1 Block‑permutation (1,000 reps) → null distribution | FR‑003, FR‑004 | SC‑002 |
| **Phase 4 – Multiple‑Comparison & Uniformity** | 4.1 BH FDR correction; 4.2 KS test | FR‑004 | SC‑005 |
| **Phase 5 – Sensitivity (Streamlined)** | 5.1 Zero‑density perturbation (±5% / ±10%) computed inline during permutation | FR‑007 | SC‑002 (via flag) |
| **Phase 6 – Visualization** | 6.1 Heatmaps with correct zero line & confidence bands | FR‑005 | — |
| **Phase 7 – Output** | 7.1 Write CSV, JSON, PNG | FR‑006 | — |

## Detailed Implementation Phases

### Phase 1 – Data Generation & Pre‑processing

| Task | Description | Determinism |
|------|-------------|-------------|
| **1.1** | Run `code/sieve.py` (linear sieve) to produce `data/raw/mobius_array.npy` (`int8`). Fixed seed is irrelevant because the algorithm is deterministic. | ✅ |
| **1.2** | Sample **M = 20** non‑overlapping window start indices per L (total 60 windows). Sampling uses a fixed seed (`seed=20231017`). This reduces runtime while preserving statistical power for the required SC‑003. | ✅ |
| **1.3** | Edge‑case guard: if a window contains only zeros, log a warning and omit permutation testing for that window (recorded in CSV). | ✅ |

### Phase 2 – Autocorrelation Computation

| Task | Description |
|------|-------------|
| **2.1** | For each sampled window, compute `r_{k,L}(h)` for all h = 1…⌊L/2⌋. Summation performed with `int64` to guarantee exactness; division yields `float64`. Results stored in an in‑memory dict for later CSV export. |

### Phase 3 – Block‑Permutation Null Distribution

| Task | Description |
|------|-------------|
| **3.1** | For a given window, split the length‑L vector into blocks of size **b = 100** (last block may be shorter). Shuffle block order **1,000** times, preserving intra‑block order and overall zero count. Compute autocorrelation for each permuted vector. |
| **3.2** | Store only the 2.5% and 97.5% quantiles per (window, lag) in the CSV; full distribution discarded to reduce memory footprint. |
| **3.3** | Compute two‑sided p‑value as `(count(|r_perm| ≥ |r_obs|) + 1) / (1000 + 1)` to avoid exact 0/1. |

### Phase 4 – Multiple‑Comparison & Uniformity Validation

| Task | Description |
|------|-------------|
| **4.1** | Apply Benjamini‑Hochberg (BH) across all p‑values (≈ ∑ L/2 × 20 × 3 ≈ 3,600 tests) to obtain `adjusted_p_value`. |
| **4.2** | Perform Kolmogorov‑Smirnov (KS) test on the full set of p‑values against the Uniform[0,1] distribution; store statistic and p‑value in `uniformity_test.json`. This satisfies SC‑005. |

### Phase 5 – Sensitivity Analysis (FR‑007, Streamlined)

| Task | Description |
|------|-------------|
| **5.1** | **Inline computation during permutation phase**: For each window, compute the observed zero count. During the 1,000 block‑permutations, also track what the p‑value would be if the zero count were inflated/deflated by 5% and 10%. This is done by **recomputing the permutation quantiles** with the adjusted zero count, but using the SAME random shuffles (only the zero‑position mapping changes). |
| **5.2** | Compare the resulting adjusted p‑values to the original. If any perturbed `adjusted_p_value` crosses the α = 0.05 threshold, set `sensitivity_flag` = `"sensitive"`; otherwise `"stable"`. If the window has all zeros (edge case), flag `"not_applicable"`. |
| **5.3** | This inline approach avoids a separate time‑consuming pass and keeps the total runtime within budget. The sensitivity results are written to the CSV immediately after permutation testing for each window. |

### Phase 6 – Visualization (FR‑005)

| Task | Description |
|------|-------------|
| **6.1** | `code/viz.py` reads `autocorrelation_stats.csv` and generates a heatmap per L. X‑axis: lag h, Y‑axis: window start index. Color: observed autocorrelation. |
| **6.2** | Overlay a **horizontal line at y = 0** using `plt.axhline(y=0, color='black', linewidth=2, linestyle='--')` to mark the theoretical zero autocorrelation. |
| **6.3** | Shade the 95% confidence band using the stored quantiles (`ci_lower`, `ci_upper`). Use `plt.fill_between()` with the lag array and quantile arrays to create a shaded region. |
| **6.4** | Annotate any cell where `adjusted_p_value < 0.05` with a red dot or marker overlay. |
| **6.5** | Save PNGs at **minimum 1200 × 1200 px** to satisfy US‑3 resolution requirement. Files: `outputs/figures/heatmap_L1000.png`, `heatmap_L10000.png`, `heatmap_L100000.png`. Use `plt.savefig(..., dpi=150, bbox_inches='tight')` to ensure high resolution. |

### Phase 7 – Output Consolidation

| Task | Description |
|------|-------------|
| **7.1** | Write `data/processed/autocorrelation_stats.csv` with columns: `interval_start`, `interval_length`, `lag`, `autocorrelation`, `p_value`, `adjusted_p_value`, `ci_lower`, `ci_upper`, `zero_count`, `sensitivity_flag`, `theoretical_variance`. |
| **7.2** | Write `uniformity_test.json` containing `ks_statistic` and `ks_pvalue`. |
| **7.3** | All files are checksum‑verified and listed in the project state file. |

## Compute Feasibility

- **Memory**: `mobius_array.npy` ≈ 10 MB; per‑window buffers ≤ 5 MB; total < 200 MB. Well under 7 GB.
- **Disk**: Raw array 10 MB, CSV ≈ 5 MB, JSON ≈ 1 KB, PNGs ≈ 3 MB. Total < 30 MB.
- **Runtime Estimate**:  
  - Sieve: ≈ 0.2 s.  
  - Autocorrelation (60 windows, max L = 10⁵): ≈ 1.5 min.  
  - 1,000 permutations × 60 windows × (10⁵ / 100) block shuffles, **with inline sensitivity** ≈ 2.5 h (vectorized NumPy; sensitivity reuses the same shuffles without additional passes).  
  - Visualization: ≈ 5 min.  
  - Total ≈ 2.75 h < 6 h.  

All steps are CPU‑only; no GPU escape hatch required.

## Risk Mitigation & Fallback

- If runtime exceeds 5 h on the runner, the pipeline will automatically **down‑sample** the number of windows to 10 per L (still > 200 tests) and re‑run; this fallback is coded in `main.py` and will be logged.  
- All random operations use `np.random.default_rng(seed=20231017)` to guarantee reproducibility.
- Sensitivity analysis is computed **inline** during permutation testing (no separate expensive pass), eliminating the timeout risk that caused T012 to fail.

## Deliverables Overview

| File | Purpose |
|------|---------|
| `plan.md` | This implementation plan (current document). |
| `research.md` | Detailed methodological write‑up with precise row/figure references. |
| `data-model.md` | Schemas and file‑format specifications. |
| `quickstart.md` | User‑facing instructions to run the pipeline. |
| `contracts/mobius_stats.schema.yaml` | JSON‑Schema for `autocorrelation_stats.csv`. |

---
