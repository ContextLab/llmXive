# Implementation Plan: Autocorrelation of the Möbius Function in Short Intervals

**Branch**: `001-autocorrelation-mobius` | **Date**: 2026-10-17 | **Spec**: `specs/001-autocorrelation-mobius/spec.md`
**Input**: Feature specification from `specs/001-autocorrelation-mobius/spec.md`

> **Re-plan note (R1)**: This revision repairs four rejected tasks (T012 sensitivity timeout, T014 broken viz zero-line / missing PNGs, T016 non-concrete claim links, T017 main.py failure), corrects two spec deviations (1,000 permutations per FR-003; 100 windows per L per FR-002), and addresses the R1 methodology panel: (a) SC-005 uniformity validation is now run on **simulated random-sign windows** (null calibration), separate from a labeled empirical check on real data; (b) the discrete p-value lattice is handled with a chi-square binned test plus a subsample KS; (c) FR-001's **2-bit encoding** is now implemented via a packed ternary artifact; (d) the FFT/int64 contradiction is resolved by an exact integer cross-validation step; (e) the σ² constant is corrected to an approximately constant value on the order of a few tenths. All working artifacts (sieve, autocorrelation module, CSV schema) are preserved.

## Summary
The pipeline will (1) generate the Möbius sequence μ(n) for 1 ≤ n ≤ 10⁷ using a deterministic linear sieve and store it as a **2-bit packed ternary array** (FR-001) alongside an int8 working copy, (2) compute normalized autocorrelations for **100 non-overlapping windows per length** L ∈ {10³, 10⁴, 10⁵} and all lags h ≤ ⌊L/2⌋ using an FFT-based convolution **cross-validated against exact int64 direct summation**, (3) construct a null distribution via **exactly 1,000 random-sign permutations per window** preserving zero positions, (4) derive two-sided p-values, 95 % confidence intervals, and Benjamini–Hochberg FDR-adjusted p-values, (5) validate the permutation test's calibration on **simulated random-sign windows** (SC-005) and separately report an empirical uniformity check on the real data, (6) perform the zero-density sensitivity analysis (±5 % / ±10 %) as a separate, budgeted, vectorized stage with an explicitly documented degradation policy, (7) render heatmaps whose zero line is a contour at autocorrelation = 0 with confidence bands aligned to the heatmap axes, and (8) output reproducible CSV/JSON/PNG artifacts. All stages run CPU-only on the GitHub Actions free-tier runner within 6 h.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `numpy==1.26.4`, `pandas==2.2.2`, `scipy==1.13.0`, `matplotlib==3.9.0`, `pillow==10.3.0`, `statsmodels==0.14.2`, `pytest==8.2.2` (pinned in `requirements.txt`).
- **Storage**: 2-bit packed `uint8` array for μ(n) (~2.5 MB, FR-001) + `int8` working copy (~10 MB); CSV/JSON for results; PNG for figures.
- **Target Platform**: Linux runner on GitHub Actions (2 CPU cores, ~7 GB RAM, ≤ 6 h).
- **Constraints**: Deterministic RNG (`seed=20231017`); no GPU required; every stage idempotent and independently runnable (T017 root cause: monolithic `main.py` aborted on first failure — now each stage is fault-isolated and writes partial checkpoints).

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Fixed seeds, deterministic sieve, pinned `requirements.txt`; re-running `code/main.py` on a fresh runner reproduces identical CSV/PNG (verified by checksum in tests). |
| II. Verified Accuracy | ✅ | The square-free density, a well-established constant cited in the literature, characterizes the asymptotic proportion of square-free integers. |
| III. Data Hygiene | ✅ | `data/raw/mobius_2bit.npy` and `data/raw/mobius_array.npy` immutable; all transforms write new files; SHA-256 checksums recorded. |
| IV. Single Source of Truth | ✅ | Every statistic and figure traces to one row of `data/processed/autocorrelation_stats.csv`; research.md lists exact row identifiers. |
| V. Versioning Discipline | ✅ | Content hashes of all artifacts recorded in project state file; `updated_at` bumped on change. |
| VI. Deterministic Arithmetic | ✅ | Sieve uses pure integer ops and the μ-array is bit-identical across runs. Autocorrelation sums are computed via float64 FFT for speed and **cross-validated exactly**: for a seeded random sample of (window, lag) pairs per L, the sum Σμ(k+i)μ(k+i+h) is recomputed by direct `int64` summation and asserted to agree with the FFT result within float64 round-off tolerance (Phase 2.3). |
| VII. Statistical Null Validation | ✅ | Exactly 1,000 random-sign permutations per window (per FR-003 and constitution VII); p-values and CIs derived solely from the permutation envelope. |

## Project Structure
```text
specs/001-autocorrelation-mobius/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── mobius_stats.schema.yaml

projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/
├── code/
│   ├── __init__.py
│   ├── sieve.py               # Linear sieve + 2-bit packing (FR-001)
│   ├── autocorrelation.py     # FFT-based window autocorrelation + int64 cross-validation
│   ├── permutation.py         # 1,000 zero-preserving sign permutations + p-values/CIs
│   ├── calibration.py         # SC-005: null calibration on simulated random-sign windows
│   ├── sensitivity.py         # Chunked, vectorized, checkpointed (fixes T012 timeout)
│   ├── viz.py                 # Contour zero-line at autocorrelation=0, axis-aligned CI bands (fixes T014)
│   └── main.py                # Fault-isolated stage orchestration with checkpoints (fixes T017)
├── data/
│   ├── raw/{mobius_2bit.npy, mobius_array.npy}
│   └── processed/
│       ├── window_index.csv
│       ├── autocorrelation_stats.csv
│       ├── sensitivity_summary.csv
│       ├── calibration_test.json
│       └── empirical_uniformity.json
├── outputs/figures/
│   ├── heatmap_L1000.png
│   ├── heatmap_L10000.png
│   └── heatmap_L100000.png
├── tests/
│   ├── unit/{test_sieve.py, test_autocorrelation.py, test_calibration.py, test_sensitivity.py, test_viz.py}
│   └── integration/test_pipeline.py
├── requirements.txt
└── pyproject.toml
```
**Structure Decision**: single-module Python project; all artifacts under `data/` and `outputs/figures/`.

## Mapping of Functional Requirements (FR) & Success Criteria (SC)

| Phase | Tasks | FR(s) | SC(s) |
|-------|-------|-------|-------|
| Phase 1 – Sieve & 2-bit packing | 1.1–1.4 | FR-001 | SC-003, SC-004 |
| Phase 2 – Autocorrelation | 2.1–2.4 | FR-002, FR-006 | SC-001, SC-003, SC-004 |
| Phase 3 – Permutation null | 3.1–3.4 | FR-003, FR-004 | SC-001, SC-002 |
| Phase 4 – Multiple comparison | 4.1 | FR-004 | SC-002 |
| Phase 5 – Null calibration & empirical uniformity | 5.1–5.2 | (US-2 AS-3) | SC-005 |
| Phase 6 – Sensitivity analysis | 6.1–6.4 | FR-007 | — |
| Phase 7 – Visualization | 7.1–7.5 | FR-005 | SC-006 |
| Phase 8 – Consolidation & claim links | 8.1–8.3 | FR-006 | SC-003 |

## Detailed Implementation Phases

### Phase 1 – Möbius Sieve & 2-Bit Packing (FR-001) — preserved, working; packing added
| Task | Description |
|------|-------------|
| 1.1 | `code/sieve.py` linear O(N) sieve → `data/raw/mobius_array.npy` (`int8`, shape (10⁷,)) — in-memory working representation. |
| 1.2 | **2-bit packing (FR-001)**: pack the int8 array into a ternary 2-bit-per-entry `uint8` array (2 values per byte, little-endian nibble order; code 0→μ=0, 1→μ=1, 2→μ=−1) → `data/raw/mobius_2bit.npy` (~2.5 MB). This packed array is the FR-001-compliant stored artifact. |
| 1.3 | Unit tests: μ(1)=1, μ(2)=−1, μ(4)=0, μ(30)=−1, μ(3025)=0; values ∈ {−1,0,1}; **pack/unpack round-trip is exact** over the full array and over random slices. |
| 1.4 | Record SHA-256 of both raw files in the project state file. |

### Phase 2 – Window Sampling & Autocorrelation (FR-002, FR-006)
| Task | Description |
|------|-------------|
| 2.1 | With `seed=20231017`, select **100 non-overlapping windows per L** (step = L; contiguous tiling from a seeded random offset within the first L positions), total 300 windows. Deterministic; the exact start indices are emitted to `data/processed/window_index.csv` so research.md can cite them concretely. |
| 2.2 | Per window, compute r(h) for all h = 1…⌊L/2⌋ via FFT (`ifft(fft(w)·conj(fft(w)))`) in `float64`, normalization by L−h. **The FFT path is float64 by nature; exactness is guaranteed by the cross-validation in 2.3, not by the FFT itself.** |
| 2.3 | **Exact int64 cross-validation (Constitution VI)**: for a seeded random sample of ≥ 100 (window, lag) pairs per L, recompute Σμ(k+i)μ(k+i+h) by direct `int64` summation and assert agreement with the FFT value within float64 round-off tolerance (relative error < 1e−9); failures abort the stage. Results logged to `data/processed/pipeline_status.json`. |
| 2.4 | Edge cases: all-zero window → `autocorrelation=nan`, `sensitivity_flag="not_applicable"`, skip permutation; p-value edge cases reported as p < 0.001 / p > 0.999 bounds (spec Edge Cases). Write per-(window, lag) rows with `p_value`/CI placeholders to the CSV (checkpointed incrementally). |

### Phase 3 – Permutation Null (FR-003, FR-004)
| Task | Description |
|------|-------------|
| 3.1 | Per window: fix zero positions, uniformly shuffle the non-zero signs. |
| 3.2 | Generate **exactly 1,000** permutations per window (`np.random.default_rng`, per-window seed derived deterministically as `20231017 + window_id`). |
| 3.3 | Per permutation compute all lags via the same FFT routine (batched: all 1,000 permutations of a window in one vectorized FFT call over a (1000, L) matrix). |
| 3.4 | Two-sided p-value `p = (#{|r_perm| ≥ |r_obs|} + 1) / 1001`; CI = 2.5th/97.5th percentiles of the null. |

### Phase 4 – Multiple-Comparison Correction (FR-004)
| Task | Description |
|------|-------------|
| 4.1 | BH FDR at α = 0.05 across all raw p-values (≈ 5.56 M tests: 300 windows × (500+[deferred]+[deferred]) lags) via `statsmodels.multipletests`; store `adjusted_p_value`. |

### Phase 5 – Null Calibration & Empirical Uniformity (SC-005)
SC-005 requires uniformity of p-values **"under the null hypothesis (simulated on random data)"** — i.e., validation of the TEST on data known to satisfy the null. This is deliberately separated from the empirical result on real μ data.
| Task | Description |
|------|-------------|
| 5.1 | **Null calibration (SC-005)**: `code/calibration.py` generates synthetic random-sign windows (zero positions fixed at the observed density 6/π², non-zero signs i.i.d. uniform ±1, seeded), runs the FULL permutation test (1,000 permutations) on e.g. 200 synthetic windows per L, and tests uniformity of the resulting p-values. Because 1,000-permutation p-values live on a discrete 1/1001 lattice (≈ 501 attainable two-sided values), a plain KS against continuous Uniform[0,1] is invalid at large n; the calibration therefore uses (a) a **chi-square goodness-of-fit test on binned p-value counts** (equal-probability bins on the lattice) and (b) the spec's "approximate Kolmogorov–Smirnov test" on a **small subsample of independent windows** (one window per L, all its lags) where the lattice discreteness is negligible. Both results → `data/processed/calibration_test.json` (`chi2_statistic`, `chi2_pvalue`, `ks_statistic`, `ks_pvalue`, `n_simulated_windows`). Success criterion: chi-square p > 0.05 and subsample KS p > 0.05. |
| 5.2 | **Empirical uniformity check (labeled, NOT test validation)**: the same two tests are applied to the raw p-values from the REAL μ windows and written to `data/processed/empirical_uniformity.json`. This is reported as a research result about the random-sign heuristic on real data; a rejection here means the null may be false for μ, not that the test is broken. Both files are kept distinct and clearly labeled. |

### Phase 6 – Sensitivity Analysis (FR-007) — redesigned (fixes T012 timeout)
| Task | Description |
|------|-------------|
| 6.1 | Per window, build adjusted zero counts z±5 %, z±10 % (rounded). Realize each adjustment by randomly converting \|μ\|=1 entries to 0 (insertion) or 0 entries to ±1 (deletion, signs drawn from the observed sign ratio), preserving length L; re-shuffle non-zero signs. |
| 6.2 | For each of the 4 adjustments, generate 1,000 permutations and compute all lags in **one batched FFT over a (1000, L) matrix**; process windows in chunks of 10 with per-chunk timing checkpoints. |
| 6.3 | Compare per-lag significance between original and each adjusted run using the **raw p < 0.05 threshold — this is deliberate**: FR-007 specifies "p < 0.05" verbatim, so the sensitivity criterion is intentionally the raw threshold, which is more sensitive than the FDR-governed main analysis; consequently `significant_change` may flag lags that were never significant after BH adjustment. To keep this interpretable, the affected-lags summary reports BOTH `p_raw` and `adjusted_p_value` status for every affected lag, so readers can distinguish raw-threshold flips from FDR-significant flips. **Acknowledged limitation (MC noise)**: with 1,000 permutations, p-values near 0.05 carry Monte Carlo noise of ≈ ±0.007, so borderline lags can flip by resampling chance alone; the `significant_change` flag therefore partly measures resampling noise in addition to zero-density robustness. Tightening the criterion (e.g., requiring flips exceeding the permutation resolution) would deviate from FR-007's literal text and is flagged for spec kickback. Write `data/processed/sensitivity_summary.csv` (columns: `interval_start`, `interval_length`, `adjustment`, `significant_change`, `affected_lags`, `affected_lags_fdr_significant`). |
| 6.4 | **Documented degradation guard**: if cumulative elapsed time exceeds 4 h, the sensitivity stage restricts to the L = 10³ and L = 10⁴ subsets. This is an explicit, logged degradation of FR-007-mandated scope (recorded in `pipeline_status.json` and reported in research.md); the **full-scope run over all three L remains the deliverable** whenever runtime permits, and the guard never reduces the 1,000-permutation count (FR-003). |

### Phase 7 – Visualization (FR-005, SC-006) — redesigned (fixes T014)
| Task | Description |
|------|-------------|
| 7.1 | `code/viz.py` loads the CSV, groups by `interval_length`; heatmap via `plt.imshow` (X = lag, Y = window index ordered by start, color = autocorrelation, symmetric vmin/vmax). |
| 7.2 | **Zero line**: overlay `plt.contour(X, Y, Z, levels=[0.0], colors='black', linewidths=2, linestyles='--')` on the heatmap — a contour at color-value 0, i.e., a genuine horizontal line at autocorrelation = 0 in data space. |
| 7.3 | **Confidence band**: per lag, plot `ci_lower`/`ci_upper` (averaged over windows) as a shaded band on a twin panel directly below the heatmap sharing the X (lag) axis, using `plt.fill_between(lags, ci_lower, ci_upper, alpha=0.3)` — axes aligned by construction. |
| 7.4 | **Significance annotation**: red circles (`plt.scatter`) on heatmap cells where `adjusted_p_value < 0.05`. |
| 7.5 | Save `heatmap_L{1000,10000,100000}.png` at ≥ 1200 × 1200 px (dpi=150, `bbox_inches='tight'`, `matplotlib.use('Agg')`); unit test verifies resolution ≥ 1000 × 1000 px, PNG format, presence of the zero contour (checked by re-plotting with a recorded artist list) and of the CI band artists. |

### Phase 8 – Consolidation & Claim Links (FR-006; fixes T016)
| Task | Description |
|------|-------------|
| 8.1 | `code/main.py` **rewritten as a fault-isolated orchestrator**: each stage runs in a `try/except`, logs the failure, writes a per-stage status to `data/processed/pipeline_status.json`, and continues with dependent stages skipped gracefully (exit 0 with a non-empty failure list only if a core stage — sieve/autocorrelation/permutation — fails; this fixes T017's exit=1 abort). |
| 8.2 | Enforce `contracts/mobius_stats.schema.yaml` on the CSV; checksum all artifacts. |
| 8.3 | After the run completes, `research.md` is regenerated/annotated with **concrete row identifiers**: exact `(interval_start, interval_length, lag)` triples for every cited claim (read from the CSV, never hand-typed), the full list of windows flagged `sensitive`, and figure file names — satisfying the single-source-of-truth and claim-link requirements. |

## Compute Feasibility
- **Memory**: 2-bit packed μ-array ≈ 2.5 MB; int8 working copy ≈ 10 MB; batched permutation matrix (1000 × 10⁵) ≈ 400 MB `int8`/`float32` — well under 7 GB. No L × L matrix is materialized.
- **Disk**: < 500 MB (CSV ≈ 5.56 M rows ≈ 400 MB; figures < 10 MB). Under 14 GB.
- **Runtime estimate** (2-core runner): sieve + packing ≈ 2 s; autocorrelation + int64 cross-validation ≈ [deferred]; permutation null: 300 windows × 1 batched FFT of (1000, L) ≈ 2–3 h; calibration [deferred]; sensitivity: 4 adjustments × same cost ≈ 1.5 h with the 4 h documented-degradation guard; BH ≈ 30 s; viz ≈ [deferred]. Total ≈ 4–5 h < 6 h.
- **CPU-first**: all methods are classical NumPy/SciPy; no GPU escape hatch needed.

## Risk Mitigation
- **T012 recurrence**: sensitivity stage is batched, chunked, and checkpointed; a unit test runs it on L = 10³ with a wall-clock assertion (< 60 s) to catch regressions.
- **T014 recurrence**: viz unit test asserts the contour artist at level 0.0 exists and CI band shares the lag axis.
- **T017 recurrence**: `main.py` stage isolation + status JSON; integration test injects a failing stage and asserts graceful continuation.
- **Determinism**: single seeded RNG scheme; identical outputs verified by checksum in the integration test.

## Deliverables Overview
| File | Purpose |
|------|---------|
| `plan.md` | This document. |
| `research.md` | Methodology + concrete claim-to-artifact row links. |
| `data-model.md` | Schemas, formats, data flow. |
| `quickstart.md` | Run instructions. |
| `contracts/mobius_stats.schema.yaml` | Schema for `autocorrelation_stats.csv`. |