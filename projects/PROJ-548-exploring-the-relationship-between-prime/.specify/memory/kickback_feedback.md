# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, pre‑commit hooks, or CI integration scripts) were provided. Without these artifacts the project does not have Ruff and Black set up as required.
- `T012` (rejected 1x): The `src/data/generate_primes.py` file is truncated (the `run_pipeline` function ends abruptly and never writes any CSV), and the required output file `data/processed/raw_gaps.csv` does not exist. Consequently, the prime‑gap generation and streaming to the specified CSV file have not been realized.
- `T015` (rejected 1x): The `src/data/ingest_zeros.py` script is present but truncated and never writes to `data/raw/zeta_zeros.csv` (its `OUTPUT_FILE` points to `data/processed`). Moreover, the required output file `data/raw/zeta_zeros.csv` does not exist at all. The ingestion logic therefore does not satisfy the task’s requirement to fetch, parse, and populate the raw CSV file.
- `T018b` (rejected 1x): The provided `distribution_test.py` contains only stub functions and comments; it does not implement the sliding‑window computation, normalization, or CSV writing. Moreover, the required output file `data/processed/maximal_gaps.csv` is absent. The task’s core functionality and output artifact are therefore missing.
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: results/ks_test_results.json
- `T024` (rejected 1x): No code, data, or result files were presented that compute or report the p‑value for the observed distributional alignment against the Cramér null distribution. The required artifact (e.g., a script or output file containing the calculated p‑value) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

