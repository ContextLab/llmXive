# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The provided `requirements.txt` exists, but it uses “>=” version specifiers instead of exact pinned versions (e.g., `networkx==3.1`). Moreover, it lists many additional packages beyond the seven required, which does not meet the task’s specification of a pinned requirements file for those specific dependencies.
- **T005** — The `code/utils/hash_artifacts.py` script exists and implements hashing, but the required state file `state/projects/PROJ-911-llmxive-follow-up-extending-mcompassrag.yaml` is missing, so the task’s requirement to update that YAML file has not been fulfilled. The missing YAML file must be created/updated by the script (or provided) for the task to be complete.
- **T008b** — declared artifact(s) missing/empty/invalid: code/utils/timer.py
- **T012** — declared artifact(s) missing/empty/invalid: data/processed/fixed_vocab.json
- **T016b** — declared artifact(s) missing/empty/invalid: data/processed/features.csv
- **T017** — declared artifact(s) missing/empty/invalid: data/results/latency.log
- **T023** — declared artifact(s) missing/empty/invalid: data/results/retrieved_features.csv
- **T028b** — declared artifact(s) missing/empty/invalid: data/results/correlation.csv
- **T030b** — declared artifact(s) missing/empty/invalid: data/results/resource_usage.log
- **T034** — Requested task execution failed; rerun successfully: code/cleanup_refactor.py exit=1
