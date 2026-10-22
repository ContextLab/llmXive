# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The `code/requirements.txt` file exists but contains an invalid entry `python==3.11`, causing `pip install -r code/requirements.txt` to fail (see `code/.tasks/T012.code_tests_test_requirements.py.log`). The required verification that installation succeeds therefore does not hold.
- **T002** — Requested task execution failed; rerun successfully: src/utils/checksum_all.py exit=1
- **T003** — The repository contains the required `src/data/featurize.py`, but the expected output files are absent: `data/processed/features.csv` and `data/processed/featurize.log` are missing, and the existing `descriptor_gaps.log` shows a descriptor gap (missing `A_atomic_radius`), causing the script to abort. The task therefore does not deliver a complete feature matrix with the required 12 descriptor columns plus `formation_energy`.
- **T004** — The `src/data/validate.py` script is present and implements the required checks and power calculation, but the required output file `data/processed/validation.log` is missing, so the task’s output artifact is not provided.
- **T005** — Requested task execution failed; rerun successfully: src/utils/checksum_all.py exit=1
