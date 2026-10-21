# Tasks: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

**Inputs**: Active `spec.md`, `plan.md`, `data-model.md`, and `contracts/` under `specs/001-investigating-the-predictive-power-of-mo/`.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US1] Commit the curated experimental reference file `data/raw/nist_refs.json` containing self‑diffusion coefficients for water, ethanol, and acetone at matched temperature (298 K), each entry with `solvent`, `temperature`, `value` (m²/s), and `source` (NIST Chemistry WebBook citation string). Implement `code/data/loader.py` that loads and schema‑validates this file and **FAILS LOUDLY** (raise `FileNotFoundError`/`ValueError`) on missing or malformed input, with **NO synthetic fallback** (FR‑001, spec §4, §7). Compute and record the file's SHA256 checksum in `data/raw/nist_refs.json.sha256`. Include pytest unit tests in `code/tests/test_loader.py` covering valid load, missing file, and malformed schema. **Verify**: `pytest code/tests/test_loader.py` passes and `python -c "from code.data.loader import load_refs; print(load_refs())"` prints the three validated entries.

- [ ] T002 [US1] Implement `code/simulations/build_system.py` and `code/simulations/run_simulation.py`: build OPLS‑AA simulation boxes (~150 molecules) for water (TIP3P‑style OPLS), ethanol, and acetone via OpenMM `ForceField`/`Modeller`, and run seeded NPT Langevin simulations (OpenMM 8.1.1, CPU platform, pinned seeds) writing trajectories as `.xtc` plus run logs with wall‑clock times to `data/raw/simulations/`. Each run performs minimization, equilibration, and production. Log wall‑clock; any run exceeding **5.5 h** is logged as a performance issue per FR‑004 (never silently altered). Include a smoke test in `code/tests/test_simulation.py` that runs a 1000‑step water box and checks outputs exist. **Verify**: `pytest code/tests/test_simulation.py` passes and a seeded 1 ns water run produces `data/raw/simulations/water_1ns_seed0.xtc` plus a log file. <!-- FAILED-IN-EXECUTION: code/tests/test_simulation.py exit=2 -->

- [ ] T003 [US1] Implement `code/analysis/msd.py` and `code/analysis/diffusion.py`: compute MSD trajectories with mdtraj, discard the first **0.1** of trajectory time (ballistic regime), fit MSD vs. *t* by linear regression, and require **R² ≥ 0.95** (FR‑003, Constitution VI). Compute *D* = slope/6 and set `d_scaled_m2_s = d_calc_m2_s` (no CG scaling). Rows failing the gate get `status = "convergence_failed"` and are excluded from MAE aggregation but recorded. Include pytest unit tests in `code/tests/test_diffusion.py` with synthetic analytic MSD curves (test fixtures only, never results) covering the linear case and the R²‑failure case. **Verify**: `pytest code/tests/test_diffusion.py` passes.

- [ ] T004 [US1] Implement `code/pipeline.py` orchestrating loader → simulation → MSD/diffusion → MAE for a small first case (water, 1 ns, 1 seed), writing real result rows to `data/processed/diffusion_results.csv` conforming to `contracts/diffusion_results.schema.yaml` (fields: `solvent`, `duration_ns`, `seed`, `msd_slope`, `r_squared`, `d_calc_m2_s`, `d_scaled_m2_s`, `mae`, `status`). Add schema validation of the written CSV against the contract. Document the runnable command in `specs/001-investigating-the-predictive-power-of-mo/quickstart.md`. **Verify**: `python code/pipeline.py --solvent water --duration 1 --seed 0` runs end‑to‑end without errors (FR‑009) and the CSV contains one real, schema‑valid row. <!-- FAILED-IN-EXECUTION: code/pipeline.py exit=2 --> <!-- FAILED-IN-EXECUTION: code/pipeline.py exit=1 -->

**Checkpoint**: The documented command executes on real simulation output and its numerical outputs can be checked against the curated references.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US1] Run the full seed matrix: 3 solvents × (1 ns × 3 seeds, 5 ns × 3 seeds, 10 ns × 1 seed) = 21 trajectories, appending all rows to `data/processed/diffusion_results.csv` (FR‑002, plan §2). Wall‑clock is logged per run; conditions with zero accepted seeds are excluded from subsequent schema‑validated statistics to satisfy contract constraints (n_seeds ≥ 1), with failures recorded in simulation logs. **Verify**: `data/processed/diffusion_results.csv` contains 21 rows, all schema‑valid, with per‑run wall‑clock times present in the simulation logs.

- [ ] T007 [US3] Implement `code/analysis/bootstrap.py`: for each solvent × duration, resample per‑seed absolute errors with replacement for **exactly 1000 iterations** (fixed; **NO automatic reduction** under any circumstance — FR‑004), compute mean MAE and 2.5/97.5 percentile 95 % CIs, and write `data/processed/bootstrap_stats.json` conforming to `contracts/bootstrap_stats.schema.yaml`. Include a **paired‑bootstrap hypothesis test** that resamples the paired differences of MAE between the 1 ns and 10 ns simulations for each solvent, yielding a numeric `p_value` and a `granularity_note` explaining the minimal achievable p‑value given the seed count. Bootstrap RNG seed is pinned for reproducibility. Include unit tests in `code/tests/test_bootstrap.py` verifying iteration count is exactly 1000 and CI ordering. **Verify**: `pytest code/tests/test_bootstrap.py` passes and `bootstrap_stats.json` validates against its contract with `iterations == 1000` for every entry (SC‑003, SC‑005).

- [ ] T008 [US1] Implement `code/analysis/report.py`: generate timescale‑accuracy curves (MAE vs. simulation duration at **1 ns**, **5 ns**, **10 ns**) with **95 % confidence bands** per solvent from `data/processed/bootstrap_stats.json` (SC‑001), and summary tables (mean MAE, 95 % CI, descriptive trend analysis per solvent) into `results/` as figures and CSV tables (SC‑004). All figures/tables derive solely from the processed artifacts — no hand‑typed numbers (Constitution IV). **Verify**: `results/` contains one curve figure per solvent with CI bands and a summary table covering all 9 solvent × duration conditions.

- [ ] T009 [US3] Run the complete pipeline end‑to‑end from the documented quickstart command over the full parameter domain (all solvents, durations, seeds, bootstrap, reporting) and record actual outcomes. Confirm all pytest suites pass and all three processed artifacts validate against their contracts. Any wall‑clock > 5.5 h is logged and reported as a performance issue per FR‑004. **Verify**: `python code/pipeline.py --full` completes without errors (FR‑009, SC‑006) and `pytest code/tests/` passes in full.

## Phase 3: Reproducible results and paper handoff

- [ ] T010 Write a concise methods/results account in `specs/001-investigating-the-predictive-power-of-mo/research.md` (results section) linked to the actual rows of `diffusion_results.csv`, `bootstrap_stats.json`, and `sensitivity_report.json` and the figure files in `results/`. Report honestly: seed‑count power limitations (N = 1 at 10 ns), any convergence‑failed trajectories (those failing the R² gate), sensitivity variance percentages, and the paired‑comparison granularity limits. **Verify**: every number in the account traces to a named artifact cell/file.

- [ ] T011 Re‑run the documented workflow from its declared inputs (curated `nist_refs.json`, pinned seeds) and confirm bit‑reproducible statistics (bootstrap CIs identical under the pinned RNG seed). Document the paper‑stage handoff in `specs/001-investigating-the-predictive-power-of-mo/quickstart.md`: figures, tables, summary statistics, and limitations to be consumed by the paper pipeline (layout/PDF/publication are out of scope here). **Verify**: a second full run reproduces identical `bootstrap_stats.json` values and the handoff section lists all deliverable artifacts.

## Dependencies and requirement coverage

- **FR‑001** (load curated refs): T001. Command: `pytest code/tests/test_loader.py`.
- **FR‑002** (MSD extraction, D from regression slope): T002–T004. Command: `python code/pipeline.py --solvent water --duration 1 --seed 0`.
- **FR‑003** (0.1 discard, R² ≥ 0.95 gate): T003. Command: `pytest code/tests/test_diffusion.py`.
- **FR‑004** (1000‑iteration bootstrap, no reduction, 5.5 h performance flag): T002, T007, T009. Command: `pytest code/tests/test_bootstrap.py`.
- **FR‑008** (timescale‑accuracy curves, CI bands, paired hypothesis test): T007, T008.
- **FR‑009 / SC‑006** (end‑to‑end execution): T004, T009.
- **SC‑001, SC‑003, SC‑004, SC‑005**: T007, T008, T009.
- **US2 sensitivity**: no dedicated task (sensitivity analysis removed as it lacks a functional requirement).

**Execution order**: T001 → T002 → T003 → T004 (first end‑to‑end result) → T005 → (T007 after T005) → T008 → T009 → T010 → T011. T006 was removed; remaining tasks respect data dependencies.

# End of tasks.md