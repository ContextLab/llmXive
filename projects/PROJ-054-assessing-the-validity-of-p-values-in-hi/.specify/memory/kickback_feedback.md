# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T024` (rejected 1x): No code, data files, or analysis outputs (e.g., synthetic data generator, test‑execution scripts, p‑value collections, KS statistics, or QQ‑plot figures) were supplied; the claim cannot be verified against any concrete artifact. The required deliverables for the three user stories are missing.
- `T028` (rejected 1x): The required `data/sweep/seed_map.json` file is missing, violating the pre‑condition, and the provided `code/analyze_pvalues.py` does not contain any implementation of the permutation test generator (no call to `RNGWrapper.reset` or row‑resampling logic). Both the necessary data file and the core functionality are absent.
- `T011b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/sweep/plan_update_request.md, data/sweep/power_analysis_result.json
- `T017` (rejected 1x): The repository lacks the required output file `data/sweep/params.csv`, and the shown portion of `code/generate_data.py` does not demonstrate the full Cartesian‑product sweep, handling of `distribution_type`, or CSV writing logic. Consequently the task’s core output and complete sweep implementation are missing.
- `T019` (rejected 1x): The repository lacks the required `data/sweep/params.csv` file, so the generator cannot iterate over the sweep parameters. Moreover, the provided `code/generate_data.py` (truncated) shows no streaming generator that reads this CSV, sets `np.random.seed` per iteration, or yields data to a callback, so the core functionality is absent. Both the pre‑condition and the implementation requirements are unmet.
- `T019b` (rejected 1x): The required `data/sweep/seed_map.json` file does not exist, so the core output of the task is missing despite the presence of `master_seed.txt`. The implementer must create the JSON seed map as specified.
- `T022` (rejected 1x): The required input files `data/sweep/seed_map.json` and `data/sweep/params.csv` are absent, and the provided `code/run_tests.py` does not fully implement the pipeline (e.g., it never uses `load_seed_map`, lacks schema validation, is truncated, and does not reference T019c). The task’s core requirements are therefore unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

