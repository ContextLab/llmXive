# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The output JSON exists and its content is plausible (top eigenvalue 2.878 near BBP 2.9, outlier flag consistent with FR-004), but several explicitly required artifacts are missing: `data/raw/matrix_N1000_seed42.npy` (the task says the script loads the checksummed raw matrix — no such file or `checksums_raw.json` entry exists on disk), the schema files `simulation_run.schema.yaml` and `eigenvalue_result.schema.yaml` (so validation criterion (a) cannot be checked), and `data/logs/simulation_run.log` (required log output is absent, giving no execution evidence). Additionally, the contract in the
- **T003** — declared artifact(s) missing/empty/invalid: data/processed/validated_sweep_results.csv
- **T004** — Requested task execution failed; rerun successfully: code/analysis/threshold_identification_t004.py exit=1
