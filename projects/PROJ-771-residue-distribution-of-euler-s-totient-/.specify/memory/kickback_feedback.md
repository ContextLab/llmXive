# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 17 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The API described for `code/stats.py` includes `run_chi_squared_test` returning fields for a chi‑squared test, but the `StatisticalResult` schema only permits `test_type` = "block_bootstrap_deviation" and does not define chi‑squared fields. This schema‑API mismatch makes the verification in `tests/unit/test_stats.py` impossible to satisfy.
- Tasks T001–T006 claim to deliver configuration loader, MemoryGuard, seed‑pinning module, exception hierarchy, and benchmark instrumentation, but none of these files (code/config.py, code/memory_guard.py, code/seed.py, code/exceptions.py, code/benchmark.py) exist in the repository, so the FR‑007 verification steps cannot be performed.
- Task T010 requires `code/sieve.py` to provide `compute_phi_linear_sieve` and `compute_residues` with MemoryGuard integration, yet `code/sieve.py` does not define these functions nor raise `MemoryLimitExceeded`, breaking FR‑001 and FR‑007.
- Task T011 demands comprehensive docstrings and a successful mypy run, but no docstrings are present and no `results/reports/mypy_sieve.txt` file is generated, violating the verification clause.
- Task T012 specifies a χ² test API (including exact test fallback) and block‑bootstrap deviation logic, yet `code/stats.py` lacks the required functions, returns incorrect structures, and does not implement the exact multinomial test, breaching FR‑003.
- Task T013 expects a flags generator that reads a `StatisticalResult` JSON and writes boolean pass/fail flags, but no `code/flags.py` exists, so verification cannot be performed.
- Task T014 requires visualizations with theoretical error‑bound overlays, but `code/visualize.py` is missing, and no PNG files are produced, violating FR‑005.
- Task T015 calls for a CLI orchestrator `code/run_analysis.py` that runs the full pipeline, yet this script is absent, making the end‑to‑end verification impossible.
- Task T016 mandates a `quickstart.md` documenting exact commands; the file is not present, so the verification step cannot confirm command presence.
- Task T102 references execution of the full pipeline on N=5,000,000, but without the orchestrator and supporting modules from Phase 1, this task cannot be executed, breaking US‑2 validation.
- Task T103 requires validation of benchmark and flag JSONs, yet the prerequisite artifacts are missing, so the verification cannot be performed.
- Task T104 expects final visualizations and a markdown summary, but the necessary scripts and output files are absent.
- Task T107 (checksum generation) and T108 (synthetic dataset validation) rely on scripts that are not provided, preventing verification of data‑hygiene and statistical‑rigor requirements.
- Task T109 (benchmark report) and T110 (CLI edge‑case test) reference files and tests that do not exist, violating FR‑007 and the error‑handling acceptance criteria.
- Task T105 (research report) and T106 (reproducibility log) require markdown documents that are not present, so the final research deliverables cannot be validated.
- The plan summary states the investigation covers primes {5, 7, 11} only, whereas the specification (FR‑001/FR‑002) requires support for the full set {3, 5, 7, 11}, narrowing the scope without explicit staging.
- Assumption that the χ² approximation holds conflicts with the plan’s omission of a χ² test, creating a contradiction between the specification’s statistical assumptions and the implemented methodology.
