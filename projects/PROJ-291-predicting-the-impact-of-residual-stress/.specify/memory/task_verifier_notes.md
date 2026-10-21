# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: src/env_check.py exit=1
- **T002** — The required verification test `code/tests/test_ingest.py` is MISSING, and neither output artifact exists (`data/processed/unified_fatigue.csv` and `data/processed/missing_flags.json` are both absent), so there is no evidence the pipeline was ever run or that schema validation passed. Additionally, the psi→MPa conversion uses a heuristic (values >1000 treated as psi) rather than a unit column, and the truncated `code/ingest/ingest.py` shows no evidence of the negative-proxy clamp adjustment count logging required by the task.
- **T003** — Requested task execution failed; rerun successfully: code/src/run_e2e.py exit=1
- **T004** — The `build_features.py` script builds Feature Set A on the full dataset while Feature Set B_balanced is filtered to rows where `is_proxy=False`, causing a length mismatch (8 vs 4) as shown by the failing `test_features.py` run. Consequently the required condition that A and balanced B share identical row indices is not met, and the verification test is missing. The task needs correction of the feature‑set construction logic (and the test file) to satisfy the specifications.
- **T005** — Requested task execution failed; rerun successfully: code/src/train.py exit=1
