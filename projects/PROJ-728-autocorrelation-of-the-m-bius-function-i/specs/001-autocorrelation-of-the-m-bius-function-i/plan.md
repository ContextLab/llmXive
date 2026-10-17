# Implementation Plan: Autocorrelation of the Möbius Function in Short Intervals

**Branch**: `001-autocorrelation-mobius` | **Date**: 2026-10-17 | **Spec**: `specs/001-autocorrelation-mobius/spec.md`  
**Input**: Feature specification from `specs/001-autocorrelation-mobius/spec.md`

## Summary
The pipeline will (1) generate the Möbius sequence μ(n) for 1 ≤ n ≤ 10⁷ using a deterministic linear sieve, (2) compute normalized autocorrelations for sliding windows of lengths L ∈ {10³, 10⁴, 10⁵} and all lags h ≤ ⌊L/2⌋ using an FFT‑based convolution, (3) construct a null distribution via **exactly 5,000 full random‑sign permutations** per window while preserving zero positions, (4) derive two‑sided p‑values, 95 % confidence intervals, and Benjamini‑Hochberg FDR‑adjusted p‑values, (5) perform an **inline sensitivity analysis** (±5 % / ±10 % zero‑density perturbations) within the same permutation loop, (6) visualise the results as heatmaps with a correctly placed zero line and confidence‑band overlays, and (7) output reproducible CSV/JSON/PNG artefacts. All steps run on CPU only and are guaranteed to finish within the 6 h GitHub Actions free‑tier limit; a tiered fallback reduces the number of windows and/or permutations if intermediate timing checkpoints are exceeded.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy==1.26.4`, `pandas==2.2.2`, `scipy==1.13.0`, `matplotlib==3.9.0`, `pytest==8.2.2` (pinned in `requirements.txt`).  
- **Storage**: `int8` NumPy array for μ(n) (~10 MB); CSV/JSON for results; PNG for figures.  
- **Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ~7 GB RAM, ≤ 6 h).  
- **Constraints**: Exact integer arithmetic for sieve & sums; deterministic RNG (`seed=20231017`); no GPU required.

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Fixed seeds, deterministic sieve, `requirements.txt`. |
| II. Verified Accuracy | ✅ | Uses the established density expressed as a constant multiple of the reciprocal of π² (source: arXiv 1211.0189). |
| III. Data Hygiene | ✅ | Raw Möbius array immutable; all transforms write new files; checksums recorded. |
| IV. Single Source of Truth | ✅ | Every statistic in `autocorrelation_stats.csv` and every figure trace to a single CSV row. |
| V. Versioning Discipline | ✅ | Content hashes recorded in project state file. |
| VI. Deterministic Arithmetic | ✅ | Sieve uses integer ops; autocorrelation sums use `int64` before conversion to `float64`. |
| VII. Statistical Null Validation | ✅ | 5,000 full random‑sign permutations per window, p‑values/CI derived from them. |

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
│   ├── autocorrelation.py     # FFT‑based sliding‑window computation
│   ├── permutation.py         # Full random‑sign permutations + inline sensitivity
│   ├── viz.py                 # Heatmap creation (zero line at y=0)
│   └── main.py                # Orchestrates all stages with robust error handling and tiered fallback
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
*Structure Decision*: A single‑module Python project; all artefacts live under `data/` and `outputs/` as required by the constitution.

## Mapping of Functional Requirements (FR) & Success Criteria (SC)

| Phase | Tasks | FR(s) | SC(s) |
|-------|-------|-------|-------|
| **Phase 1 – Data Generation** | Run `code/sieve.py` → `mobius_array.npy` | FR‑001 | SC‑003, SC‑004 |
| **Phase 2 – Autocorrelation** | Compute autocorrelation for sampled windows using FFT | FR‑002 | SC‑001 |
| **Phase 3 – Null Distribution + Sensitivity** | `code/permutation.py` (5,000 full random‑sign permutations **with inline** ±5 % / ±10 % zero‑density analysis) | FR‑003, FR‑004, FR‑007 | SC‑002, SC‑005 |
| **Phase 4 – Multiple‑Comparison** | Benjamini‑Hochberg FDR correction | FR‑004 | SC‑005 |
| **Phase 5 – Uniformity Validation** | KS test on all raw p‑values | — | SC‑005 |
| **Phase 6 – Visualization** | `code/viz.py` → heatmaps with zero line at 0 and confidence‑band shading | FR‑005 | — |
| **Phase 7 – Output Consolidation** | Write CSV, JSON, PNGs | FR‑006 | — |

## Detailed Implementation Phases

### Phase 1 – Möbius Sieve
| Task | Description |
|------|-------------|
| 1.1 | `code/sieve.py` implements the classic O(N) linear sieve, writing `data/raw/mobius_array.npy` as `int8`. |
| 1.2 | Verify via unit test that `np.unique` returns a set containing a negative element, zero, and a positive element. and that known values (μ(1)=1, μ(2)=−1, μ(4)=0, μ(30)=−1) match. |
| 1.3 | Record SHA‑256 checksum in the project state file for data‑hygiene compliance. |

### Phase 2 – Window Sampling & Autocorrelation
| Task | Description |
|------|-------------|
| 2.1 | Using `seed=20231017`, select **50** non‑overlapping start indices per L (total 150 windows). The indices are deterministic (see Research section for the first three per L). |
| 2.2 | For each window compute `r_{k,L}(h)` for all `h = 1…⌊L/2⌋` using an FFT‑based convolution: `autocorr = ifft(fft(window) * conj(fft(window)))`. Summations are performed in `int64` then divided to `float64`. |
| 2.3 | Edge‑case: if a window contains only zeros, log a warning, write `nan` for autocorrelation, and skip permutation testing (recorded in CSV). |
| 2.4 | **Runtime checkpoint** – after processing each L, if cumulative CPU time > 3 h, automatically drop to **30** windows per L; if > 4 h, drop to **20** windows per L. This tiered fallback guarantees completion within the 6 h limit. |

### Phase 3 – Full Random‑Sign Permutation + Inline Sensitivity
| Task | Description |
|------|-------------|
| 3.1 | Extract indices of non‑zero entries and their signs for the current window. |
| 3.2 | Generate **[deferred]** independent random sign shuffles (preserving zero positions) using `np.random.default_rng(seed=20231017)`. |
| 3.3 | For each permutation **(a)** compute autocorrelation for all lags via the same FFT routine, **(b)** store the null distribution, **(c)** compute the two‑sided p‑value `p = (count(|r_perm|≥|r_obs|)+1)/(5000+1)`. |
| 3.4 | **Inline Sensitivity** – using the same 5,000 permutations, recompute quantiles after inflating/deflating the observed zero count by ±5 % and ±10 % (rounded). If any perturbed adjusted p‑value crosses the α = 0.05 threshold, set `sensitivity_flag="sensitive"`; otherwise `"stable"`. Windows with all zeros get `"not_applicable"`. |
| 3.5 | Write per‑window rows to `data/processed/autocorrelation_stats.csv`. |

### Phase 4 – Multiple‑Comparison Correction
| Task | Description |
|------|-------------|
| 4.1 | Apply Benjamini‑Hochberg (BH) across **all** raw p‑values (≈ 2.78 M tests) using `statsmodels.stats.multitest.multipletests`. Store `adjusted_p_value` in the CSV. |
| 4.2 | Record the BH‑adjusted α‑threshold (α = 0.05) for downstream interpretation. |

### Phase 5 – Uniformity Validation
| Task | Description |
|------|-------------|
| 5.1 | Perform a Kolmogorov‑Smirnov test of the raw p‑value vector against Uniform[0,1] (`scipy.stats.kstest`). |
| 5.2 | Write `{ "ks_statistic": …, "ks_pvalue": … }` to `data/processed/uniformity_test.json`. |

### Phase 6 – Visualization (heatmaps)
| Task | Description |
|------|-------------|
| 6.1 | `code/viz.py` loads the CSV, groups rows by `interval_length`. |
| 6.2 | For each L, create a heatmap (`plt.imshow`) where X‑axis = lag h, Y‑axis = window start position (ordered). |
| 6.3 | **Zero line**: `plt.axhline(y=0, color='black', linewidth=2, linestyle='--')` (exactly at autocorrelation = 0). |
| 6.4 | **Confidence band**: For each lag, shade between `ci_lower` and `ci_upper` using `plt.fill_between` aligned with the heatmap axes. |
| 6.5 | **Significance markers**: Overlay a red circle (`plt.scatter`) on cells where `adjusted_p_value < 0.05`. |
| 6.6 | Save PNGs at **≥ 1200 × 1200 px**, `dpi=150`, `bbox_inches='tight'`. Filenames: `heatmap_L1000.png`, `heatmap_L10000.png`, `heatmap_L100000.png`. |
| 6.7 | Verify file existence and resolution programmatically (unit test). |

### Phase 7 – Output Consolidation
| Task | Description |
|------|-------------|
| 7.1 | CSV schema enforced by `contracts/mobius_stats.schema.yaml`. |
| 7.2 | JSON schema (implicit) for `uniformity_test.json`. |
| 7.3 | All artefacts checksum‑recorded; reproducibility checklist satisfied. |

## Compute Feasibility
- **Memory**: < 200 MB total (mobius array ≈ 10 MB; per‑window buffers ≤ 5 MB). Well under 7 GB.
- **Disk**: < 50 MB (raw + processed + figures). Well under 14 GB.
- **Runtime Estimate**:  
  - Sieve ≈ 0.2 s.  
  - Autocorrelation (FFT) ≈ [deferred] total.  
  - 5,000 full random‑sign permutations + inline sensitivity ≈ 4.5 h (vectorised NumPy + FFT) with 50 windows per L.  
  - BH correction ≈ 10 s.  
  - KS test ≈ 5 s.  
  - Visualization ≈ [deferred]  
  - **Total** ≈ 5 h < 6 h.  

If the wall‑clock time exceeds **4 h**, `main.py` automatically reduces the number of windows per L from 50 to 30; if it exceeds **5 h**, it further reduces to 20 windows and drops permutation count to 2,000 (still above the 0.001 p‑value resolution threshold). This guarantees completion within the runner limit.

## Risk Mitigation & Fallback
- **Timeout guard**: See above tiered fallback to 30/20 windows and optional reduction to 2,000 permutations.  
- **Memory guard**: All large arrays are processed in streaming fashion; no full L × L matrix is ever materialised.  
- **Determinism**: All random operations use a single `np.random.Generator` with a fixed seed; the same seed is used across modules, guaranteeing identical outputs on repeated runs.  
- **Verification**: Unit tests cover sieve correctness, FFT‑based autocorrelation, permutation p‑value calculation, sensitivity flag logic, CSV schema compliance, and figure resolution.

## Deliverables Overview
| File | Purpose |
|------|---------|
| `plan.md` | This implementation plan (current document). |
| `research.md` | Full methodological write‑up with precise row/figure linking. |
| `data-model.md` | Schemas, file formats, and data‑flow description. |
| `quickstart.md` | End‑user instructions to run the pipeline. |
| `contracts/mobius_stats.schema.yaml` | JSON‑Schema for `autocorrelation_stats.csv`. |

---


