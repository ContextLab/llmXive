# Tasks: Autocorrelation of the Möbius Function in Short Intervals

**Inputs**: `spec.md`, `plan.md` (R1 revision), original research idea, existing artifacts, and R1 reviewer/verifier feedback.

**Revision note (R2)**: This revision addresses the R1 convergence panel. Key changes: (1) T004 is corrected to the FR-002 window-sampling scheme and T023 is superseded by it (one authoritative producer); (2) the demo artifact moves to `data/processed/demo_autocorr.csv` and Phase 1 is reordered so the end-to-end evidence is produced against the final sampling contract; (3) T014 verifies the RENDERED PNG at the pixel level (SC-006(b)); (4) T026 and T012 are atomized into T031–T034 and T027–T030 respectively (umbrella IDs preserved as superseded markers); (5) T024 strengthens Constitution VI verification with exhaustive int64 checks at L = 10^3 and an honest deviation statement; (6) checksums cover `outputs/figures/*.png` and are written to BOTH `data/checksums/manifest.sha256` and the state file's `artifact_hashes` map; (7) T016 is scoped to measurement-only reporting for SC-001 because the spec's pass threshold is `[deferred]` (spec-root, flagged for kickback). Module paths are aligned to plan.md's Project Structure; residual plan/spec/data-model mismatches are flagged for kickback below.

**Kickback flags (root causes outside tasks.md)**:
- `spec.md:SC-001` — pass threshold is literally `[deferred]`; the spec must supply the threshold. Until then T016 reports the measured CI-coverage proportion without a pass/fail claim.
- `spec.md:SC-003` — runtime estimate `[deferred]`; tasks enforce the ≤ 6 h bound regardless.
- `data-model.md:Sensitivity Summary` — `adjustment` enum contains placeholders; tasks use the concrete values `{"+5%","-5%","+10%","-10%"}` per FR-007/T012. Data model must be updated to match.
- `plan.md:Project Structure` — plan lists no `generate_mobius.py`/`checksum.py`/`null_distribution.py`/`fdr_correction.py`; tasks below use the plan's authoritative module layout (sieve.py, autocorrelation.py, permutation.py, calibration.py, sensitivity.py, viz.py, main.py). Plan structure should be reconciled to name the window-sampling and checksum entry points.
- `plan.md:Phase 4.1` — lag-count placeholders `(500+[deferred]+[deferred])`; tasks use the concrete (500 + 5,000 + 50,000) ≈ 5.56 M tests.
- `spec.md:Assumptions` — SE 0.0032 at L = 10^5 is inconsistent with the σ²/L model (σ² ≈ 0.2384 → SE ≈ 0.0015); both support the qualitative power claim; spec should reconcile.
- `spec.md:Edge Cases` — p = 0 is unreachable under the (+1)/1001 correction; only the `p < 0.001` bound (at p = 1/1001) can trigger. Tasks implement the corrected semantics.
- `constitution.md:Principle VI` — mandates exact integer arithmetic for ALL sums; exhaustive int64 verification of ~5.5 M values at L = 10^5 is infeasible within SC-003. Tasks verify exhaustively at L = 10^3 and by seeded sampling elsewhere, and do NOT claim unconditional Principle VI compliance; the constitution needs an amendment sanctioning sampled cross-validation or the constraint must be relaxed.

---

## Phase 1: Setup and first end-to-end analysis

**Goal**: Run an executable analysis on real mathematical inputs early, proving the pipeline works end-to-end against the FINAL FR-002 sampling contract.

- [ ] T001 [P] [US1] Create a `quickstart.md` that documents the project layout, required Python version (3.11), pinned dependencies (`requirements.txt`), and the runnable demo command `python -m code.main --demo`.
  *Path*: `quickstart.md`

- [ ] T002 [] [US1] Implement a **linear-time Möbius sieve** that computes μ(n) for `1 ≤ n ≤ 10⁷` and stores the result as an `int8` NumPy array.
  *Path*: `code/sieve.py`

- [ ] T003 [] [US1] Add unit tests for the sieve verifying known values (μ(1)=1, μ(2)=−1, μ(4)=0, μ(30)=−1, μ(3025)=0) and that all values ∈ {−1, 0, 1}.
  *Path*: `tests/unit/test_sieve.py`

- [ ] T004 [] [US1] **Generation + FR-002 window sampling (corrected; supersedes the earlier "stratified random" wording and absorbs T023)**: extend `code/sieve.py` (generation entry point) to save the array to `data/raw/mobius_array.npy` and, with `seed=20231017`, select **100 non-overlapping windows per L ∈ {10³, 10⁴, 10⁵}** (step = L; contiguous tiling from a seeded random offset within the first L positions), total 300 windows. Emit the exact start indices to `data/processed/window_index.csv` (columns `interval_start`, `interval_length`, `window_id`). The demo path in `code/main.py --demo` uses this sampling from the start, so the early end-to-end run exercises the final contract.
  *Path*: `code/sieve.py`, `data/raw/mobius_array.npy`, `data/processed/window_index.csv`

- [ ] T005 [] [US1] Implement **autocorrelation computation** for a single sampled window (`L=10³`, lag `h=1`, window taken from `window_index.csv`) and write the normalized result to `data/processed/demo_autocorr.csv`, with a sanity check against a hand-computed reference for the chosen window.
  *Path*: `code/autocorrelation.py`, `data/processed/demo_autocorr.csv`

- [ ] T006 [] [US1] Add a focused integration test that runs the demo pipeline (sieve + window sampling → autocorrelation) and asserts that `data/processed/demo_autocorr.csv` exists and contains a numeric entry with at least six decimal places, and that `window_index.csv` contains exactly 300 rows (100 per L) with non-overlapping windows per L.
  *Path*: `tests/integration/test_demo_pipeline.py`

- [ ] T000 [] [US1] **Depends on T004.** Compute and record the SHA-256 checksum of `data/raw/mobius_array.npy` after generation, storing the result in `data/checksums/manifest.sha256` (created here; later writers must append/merge, never overwrite).
  *Path*: `code/main.py` (checksum helper), `data/checksums/manifest.sha256`

- [ ] T022 [] [US1] **2-bit packing (FR-001)**: extend `code/sieve.py` with pack/unpack functions producing `data/raw/mobius_2bit.npy` — a `uint8` array, 2 values per byte (little-endian nibble order; code 0→μ=0, 1→μ=1, 2→μ=−1), ~2.5 MB — as the FR-001-compliant stored ternary artifact, with the int8 array kept as the working copy. Unit tests must verify the pack/unpack round-trip is exact over the full array and over seeded random slices, and record SHA-256 of both raw files by **appending/merging into** `data/checksums/manifest.sha256` (must not overwrite T000's entry).
  *Path*: `code/sieve.py`, `tests/unit/test_sieve.py`, `data/raw/mobius_2bit.npy`

- [ ] T023 [] [US1] **SUPERSEDED by T004** (ID preserved for traceability). Its content — 100 non-overlapping windows per L via seeded contiguous tiling, `window_index.csv`, and the demo-path update — is fully absorbed into T004 above. Do not implement separately.

**Checkpoint**: The documented demo command executes and its numerical outputs (`demo_autocorr.csv`, `window_index.csv`) can be checked against manual calculation, using the final FR-002 sampling.

## Phase 2: Complete the study and validate its evidence

- [ ] T007 [] [US1] Extend `code/autocorrelation.py` to compute **all lags** `h ∈ {1,…,⌊L/2⌋}` for every sampled window of each length L, storing raw rows (`interval_start, interval_length, lag, autocorrelation`).
  *Path*: `code/autocorrelation.py`

- [~] T008 [] [US2] **Permutation engine per FR-003 (exactly 1,000 zero-preserving sign permutations per window)**: rewrite the permutation functions in `code/permutation.py` so that, for a given window, zero positions stay fixed and the non-zero signs are uniformly shuffled (preserving the exact zero count and the ±1 counts within the window), returning exactly 1,000 permutations via `np.random.default_rng` with per-window seed `20231017 + window_id`. Update `tests/unit/test_permutation.py` accordingly: each permutation must have the same zero count as the original window and the same count of non-zero entries with shuffled sign placement (not block shuffles).
  *Path*: `code/permutation.py`, `tests/unit/test_permutation.py`

- [~] T010 [] [US2] Build the **null distribution and statistics** (in `code/permutation.py`): for every window and lag, compute autocorrelations on the 1,000 permuted sequences (batched: all 1,000 permutations of a window in one vectorized FFT over a (1000, L) matrix), then calculate two-sided p-values `p = (#{|r_perm| ≥ |r_obs|} + 1)/1001` and the 95 % CI (2.5th/97.5th null percentiles). Edge-case semantics (corrected per spec kickback): under the (+1)/1001 correction, `p = 0` is unreachable; when the observation is more extreme than all 1,000 permutations the reported value is the lattice minimum `p = 1/1001`, annotated as `p < 0.001`; the `p > 0.999` bound applies when all permutations are at least as extreme. All-zero windows → `autocorrelation=nan`, `sensitivity_flag="not_applicable"`, permutation skipped. Write rows conforming to `contracts/mobius_stats.schema.yaml` (including `zero_count` and `theoretical_variance = σ²/L`, σ² = (6/π²)(1 − 6/π²)) to `data/processed/autocorrelation_stats.csv`, checkpointed incrementally.
  *Path*: `code/permutation.py`, `data/processed/autocorrelation_stats.csv`

- [ ] T024 [] [US1] **Exact int64 cross-validation of the FFT path (Constitution VI, strengthened)**: add to `code/autocorrelation.py` a validation routine that (a) **exhaustively** recomputes Σμ(k+i)μ(k+i+h) by direct `int64` summation for **ALL (window, lag) pairs at L = 10³** (100 windows × 500 lags — computationally trivial) and asserts agreement with the float64 FFT result within relative error < 1e−9; and (b) for L ∈ {10⁴, 10⁵}, recomputes a seeded random sample of ≥ 100 (window, lag) pairs per L plus one random lag per window, with the same assertion. Failures abort the stage. Record `n_pairs_checked` and `max_relative_error` in the `autocorrelation_crosscheck` entry of `data/processed/pipeline_status.json`. **Honest deviation statement**: exhaustive int64 verification of all ~5.5 M values at L = 10⁵ is infeasible within SC-003 (≤ 6 h); the project therefore does NOT claim unconditional Constitution VI compliance for the L = 10⁴/10⁵ FFT values — this tension is flagged for constitutional kickback (see header). Add a unit test on small windows comparing FFT and direct sums exactly.
  *Path*: `code/autocorrelation.py`, `tests/unit/test_autocorrelation.py`, `data/processed/pipeline_status.json`

- [~] T011 [] [US2] Apply the **Benjamini–Hochberg FDR correction** at α = 0.05 across all raw p-values (exactly 5,555,500 tests: 300 windows × (500 + 5,000 + 50,000) lags) via `statsmodels.multipletests` (implemented in `code/permutation.py`), adding the `adjusted_p_value` column to `autocorrelation_stats.csv`.
  *Path*: `code/permutation.py`, `data/processed/autocorrelation_stats.csv`

- [ ] T025 [] [US2] **Null calibration and empirical uniformity (SC-005)**: implement `code/calibration.py` with two clearly separated outputs. (a) **Null calibration on simulated random-sign windows** (test validation): generate synthetic windows with zero positions fixed at the observed density 6/π² and non-zero signs i.i.d. uniform ±1 (seeded), run the full 1,000-permutation test on 200 synthetic windows per L, and test p-value uniformity using (i) a chi-square goodness-of-fit test on binned p-value counts on the 1/1001 lattice and (ii) an approximate KS test on a small subsample of independent windows where lattice discreteness is negligible; write `chi2_statistic`, `chi2_pvalue`, `ks_statistic`, `ks_pvalue`, `n_simulated_windows` to `data/processed/calibration_test.json`. Success: both p > 0.05. (b) **Empirical uniformity check on real μ p-values** (labeled research result, not test validation): apply the same two tests to the real raw p-values and write `data/processed/empirical_uniformity.json`, explicitly labeled as a result about the random-sign heuristic. Unit tests must assert both files exist with valid fields and that the calibration file is computed on simulated windows only.
  *Path*: `code/calibration.py`, `tests/unit/test_calibration.py`, `data/processed/calibration_test.json`, `data/processed/empirical_uniformity.json`

- [ ] T012 [] [US2] **SUPERSEDED umbrella (ID preserved)** — zero-density sensitivity analysis (FR-007), previously rejected for TIMEOUT and flagged as too coarse. Atomized into **T027–T030** below; do not implement T012 as a single unit.

- [ ] T027 [] [US2] **Sensitivity — adjusted-window construction**: implement in `code/sensitivity.py` the per-window construction of adjusted zero counts z±5 % and z±10 % (rounded), realized by randomly converting |μ|=1 entries to 0 (insertion) or 0 entries to ±1 (deletion, signs drawn from the observed sign ratio), preserving length L, then re-shuffling non-zero signs. Seeded and deterministic.
  *Path*: `code/sensitivity.py`

- [ ] T028 [] [US2] **Sensitivity — computation and comparison**: for each of the 4 adjustments (`+5%`, `-5%`, `+10%`, `-10%` — concrete values; the data-model enum placeholders are flagged for kickback) generate 1,000 permutations and compute all lags in one batched FFT over a (1000, L) matrix, processing windows in chunks of 10 with per-chunk timing checkpoints. Compare per-lag significance between original and each adjusted run using the **raw p < 0.05 threshold** (FR-007's literal criterion — deliberately more sensitive than the FDR-governed main analysis); report both `p_raw` and `adjusted_p_value` status for every affected lag, and document the ≈ ±0.007 Monte Carlo noise limitation near the threshold in the output.
  *Path*: `code/sensitivity.py`

- [ ] T029 [] [US2] **Sensitivity — output and degradation guard**: set `sensitivity_flag` per window in `autocorrelation_stats.csv` and write `data/processed/sensitivity_summary.csv` (columns: `interval_start`, `interval_length`, `adjustment` ∈ {"+5%","-5%","+10%","-10%"}, `significant_change`, `affected_lags`, `affected_lags_fdr_significant`). Include a documented degradation guard: if cumulative elapsed time exceeds 4 h, restrict to L ∈ {10³, 10⁴} and record the degradation in `pipeline_status.json` (never reducing the 1,000-permutation count).
  *Path*: `code/sensitivity.py`, `data/processed/sensitivity_summary.csv`

- [ ] T030 [] [US2] **Sensitivity — regression test**: a unit test that runs the sensitivity stage on L = 10³ with a wall-clock assertion (< 60 s) to catch timeout regressions, and verifies the summary CSV schema and the deterministic reproducibility of adjusted windows under the fixed seed.
  *Path*: `tests/unit/test_sensitivity.py`

- [ ] T014 [] [US3] **Heatmap visualizations (FR-005, SC-006; fixes broken zero-line and missing PNGs)**: rewrite `code/viz.py` to load `autocorrelation_stats.csv`, group by `interval_length`, and for each L ∈ {10³, 10⁴, 10⁵} render `outputs/figures/heatmap_L{L}.png` with: (a) a heatmap via `plt.imshow` (X = lag, Y = window index ordered by start, color = autocorrelation, symmetric vmin/vmax); (b) a **black dashed contour at autocorrelation = 0** via `plt.contour(X, Y, Z, levels=[0.0], colors='black', linewidths=2, linestyles='--')` — a genuine horizontal line at autocorrelation = 0 in data space, not an `axhline` on an index axis; (c) a CI band panel directly below the heatmap sharing the lag (X) axis, plotting per-lag `ci_lower`/`ci_upper` (averaged over windows) with `plt.fill_between(lags, ci_lower, ci_upper, alpha=0.3)`; (d) red circle markers (`plt.scatter`) on heatmap cells where `adjusted_p_value < 0.05`. Save at ≥ 1200 × 1200 px (dpi=150, `bbox_inches='tight'`, `matplotlib.use('Agg')`). Unit tests must verify, **on the SAVED PNG file** (SC-006(b)): PNG format and resolution ≥ 1000 × 1000 px (via PIL), and **pixel-level detection of the black dashed horizontal contour at autocorrelation = 0** — load the rendered image with PIL, locate the heatmap axes region, and assert a row of dark pixels matching the dashed zero contour exists (this catches rendering failures that artist-presence checks miss, the exact original T014 rejection mode). Additionally assert, during figure construction, presence of the zero-contour artist at level 0.0 and of the CI band artists sharing the lag axis.
  *Path*: `code/viz.py`, `tests/unit/test_viz.py`, `outputs/figures/heatmap_L1000.png`, `outputs/figures/heatmap_L10000.png`, `outputs/figures/heatmap_L100000.png`

## Phase 3: Reproducible results and paper handoff

- [ ] T026 [] [US1] **SUPERSEDED umbrella (ID preserved)** — orchestration/consolidation, flagged as too coarse. Atomized into **T031–T034** below; do not implement T026 as a single unit.

- [ ] T031 [] [US1] **Fault-isolated orchestrator (fixes T017 exit=1 abort)**: rewrite `code/main.py` as a stage orchestrator where each stage (sieve/packing → window sampling → autocorrelation + cross-validation → permutation null → FDR → calibration → sensitivity → visualization) runs in a `try/except`, logs the failure, writes per-stage status (`status`, `elapsed_seconds`, `error`) to `data/processed/pipeline_status.json`, and continues with dependent stages skipped gracefully — exiting 0 with a non-empty failure list only if a core stage (sieve/autocorrelation/permutation) fails.
  *Path*: `code/main.py`, `data/processed/pipeline_status.json`

- [ ] T032 [] [US1] **Resource guards (SC-003, SC-004)**: the orchestrator enforces SC-003 (total runtime ≤ 6 h; abort with a clear error if exceeded) and SC-004 (peak RAM < 7 GB, monitored via `resource`/`psutil`; abort with a clear error if exceeded), recording measured elapsed time and peak memory per stage in `pipeline_status.json`.
  *Path*: `code/main.py`, `data/processed/pipeline_status.json`

- [ ] T033 [] [US1] **Checksums, state-file recording, and docs (Constitution III/V; US-3 AS-2)**: after the run completes, compute SHA-256 checksums for **all files under `data/`** AND the three heatmap PNGs under `outputs/figures/` (satisfying US-3 AS-2's automated checksum verification of the figures), writing them to `data/checksums/manifest.sha256` (append/merge) AND to the project state file's `artifact_hashes` map at `state/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i.yaml` (reconciling the constitution's state-file requirement with the manifest), bumping `updated_at`. Update `quickstart.md` to document `python -m code.main` and list all expected output artifacts.
  *Path*: `code/main.py`, `data/checksums/manifest.sha256`, `state/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i.yaml`, `quickstart.md`

- [ ] T034 [] [US1] **Full-pipeline integration test with fault injection**: `tests/integration/test_full_pipeline.py` invokes `python -m code.main`, verifies the presence of all final artifacts (`autocorrelation_stats.csv`, three heatmap PNGs, `calibration_test.json`, `empirical_uniformity.json`, `sensitivity_summary.csv`, `pipeline_status.json`, `manifest.sha256` with entries for the PNGs), validates the CSV against `contracts/mobius_stats.schema.yaml`, and injects a failing stage to assert graceful continuation (non-core failure → exit 0 with the failure recorded in `pipeline_status.json`).
  *Path*: `tests/integration/test_full_pipeline.py`

- [ ] T016 [] [US1] **Concrete claim-linked methods & results (fixes non-concrete links; SC-001 scoped to measurement-only)**: write `research.md` summarizing methodology and results where every scientific claim is linked to **concrete row identifiers read programmatically from the CSV** (exact `(interval_start, interval_length, lag)` triples, never hand-typed or given as conditions), the full list of windows flagged `sensitive` (with their `interval_start` values from `sensitivity_summary.csv`), the calibration vs. empirical uniformity results (clearly labeled as test validation vs. research result), the int64 cross-validation outcome (including the L = 10³ exhaustive scope and the sampled scope for larger L), any sensitivity-scope degradation, and the figure file names. **SC-001 reporting**: because the spec's pass threshold is `[deferred]` (spec-root, flagged for kickback), report the MEASURED proportion of lags per L whose 95 % CI contains zero (equivalently p > 0.05) as a descriptive statistic WITHOUT a pass/fail claim, explicitly noting the threshold gap. Describe negative findings and limitations honestly (including the raw-p-threshold sensitivity criterion, Monte Carlo noise near p = 0.05, and the Constitution VI sampled-verification deviation). Document the paper-stage handoff: the paper pipeline receives `research.md`, `autocorrelation_stats.csv`, `sensitivity_summary.csv`, the two uniformity JSON files, and the three heatmap PNGs.
  *Path*: `research.md`

---

## Dependencies and requirement coverage

| Spec requirement | Satisfying task(s) | Demonstration command |
|------------------|--------------------|----------------------|
| FR-001 (sieve + 2-bit ternary array) | T002, T003, T022 | `pytest tests/unit/test_sieve.py` |
| FR-002 (100 non-overlapping windows/L, FFT autocorrelation, all lags) | T004, T005, T007, T024 | `python -m code.main --demo` |
| FR-003 (exactly 1,000 zero-preserving sign permutations) | T008, T010 | `pytest tests/unit/test_permutation.py` |
| FR-004 (two-sided p-values, 95 % CI, BH FDR) | T010, T011 | `pytest tests/unit/` |
| FR-005 (heatmaps with zero line + CI bands) | T014 | `pytest tests/unit/test_viz.py` |
| FR-006 (structured CSV output) | T010, T011, T034 | schema check in `test_full_pipeline.py` |
| FR-007 (zero-density sensitivity ±5 %/±10 %) | T027, T028, T029, T030 | `pytest tests/unit/test_sensitivity.py` |
| SC-001 (CI coverage; threshold deferred — measurement-only) | T010, T016 | rows of `autocorrelation_stats.csv` |
| SC-002 (p vs α = 0.05) | T010, T011, T016 | rows of `autocorrelation_stats.csv` |
| SC-003 (≤ 6 h runtime) | T032 | `pipeline_status.json` elapsed times |
| SC-004 (< 7 GB RAM) | T032 | `pipeline_status.json` / abort guard |
| SC-005 (null calibration uniformity) | T025 | `calibration_test.json` |
| SC-006 (heatmap correctness incl. rendered-PNG zero-line detection) | T014 | `pytest tests/unit/test_viz.py` |
| US-3 AS-2 (figure checksum verification) | T033, T034 | `manifest.sha256` PNG entries |
| Constitution III/V (checksums incl. state `artifact_hashes`) | T000, T022, T033 | `manifest.sha256` + state YAML |
| Constitution VI (exact arithmetic; sampled at large L — deviation flagged) | T024 | `autocorrelation_crosscheck` |

**Execution order**: T002 → T003 → T004 → T005 → T006 → T000 → T022 (parallel with T007+) → T008 → T010 → T024, T011 → T025, T027 → T028 → T029 → T030 → T014 → T031 → T032 → T033 → T034 → T016. T027–T030 and T025 depend on T010; T014 depends on T011; T016 depends on all analysis stages. T023, T012, and T026 are superseded umbrella IDs (absorbed into T004, T027–T030, and T031–T034 respectively).

## Revision behavior

Completed tasks T001–T007 retain their verified status where their artifacts still match the corrected contracts; T005/T006 evidence must be re-verified against the corrected FR-002 sampling and the relocated `data/processed/demo_autocorr.csv`. T008/T010/T011 remain partially complete (`[~]`) and are reopened where the spec correction applies (1,000 sign permutations replacing block permutation; 100 windows per L feeding the null distribution). T015 is superseded by T025. T012 is atomized into T027–T030; T026 is atomized into T031–T034; T023 is absorbed into T004 — all umbrella IDs preserved for traceability, no acceptance criterion dropped (SC-003 runtime ≤ 6 h, SC-004 RAM < 7 GB, checksum manifest incl. figures and state `artifact_hashes`, pixel-level SC-006(b) verification all retained). No working artifact is deleted; `code/sensitivity.py`, `code/viz.py`, `code/main.py`, and `research.md` are rewritten in place to repair the verifier-rejected evidence.