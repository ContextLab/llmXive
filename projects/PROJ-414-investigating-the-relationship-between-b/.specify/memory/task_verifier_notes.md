# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The extracted CSVs and QC JSONs exist, but the unit tests fail: the DVARS‑based bad‑volume rule does not flag the injected spikes (test_dvars_exclusion_fires_on_known_bad_volumes), and the CSVs write numeric subject IDs causing schema validation and exclusion‑log mismatches (test_real_outputs_conform_to_schema, test_exclusion_log_covers_all_subjects). Additionally, the required `results/performance_metrics.txt` file documenting memory usage is missing. Fix the DVARS logic, ensure subject IDs are written as strings, generate the performance‑metrics file, and re‑run the tests.
- **T004** — Requested task execution failed; rerun successfully: code/connectivity.py exit=1
