# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — The repository contains a `generate_target_list.py` file, but it is truncated and does not show the required exponential backoff with jitter, CSV writing logic, or column selection (`url`, `primary_language`, `stars`, `age`). Moreover, the expected output file `data/raw/target_list.csv` is absent. Consequently, the task’s functional requirements are not satisfied.
- **T007** — The repository contains `code/data/download_nvd.py`, but the file is truncated and implements an API‑based fetch rather than downloading the official yearly JSON feeds, and it never creates the required `data/raw/nvd_cve_merged.json.gz` and its `.sha256` checksum (both files are missing). Consequently the task’s output artifacts are absent and the implementation does not follow the specified logic.
