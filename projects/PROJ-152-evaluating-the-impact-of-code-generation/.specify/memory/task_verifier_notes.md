# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — The provided `code/generate.py` shows logging setup for `data/failures.log` but the file is truncated before any generation loop that iterates over the 30 prompts and creates 90 snippets, so we cannot confirm the required processing logic exists. Moreover, the `data/failures.log` file is absent, meaning failures are not currently being recorded. The implementer must add a concrete loop that reads the 30 prompts from `data/prompts/manifest.json`, generates snippets for the three models, and ensure `data/failures.log` is created and populated with any generation errors.
- **T016** — The `code/metrics.py` file contains the mapping functions, but the required `data/mappings/nist_severity_map.yaml` file is absent, so the implementation cannot actually perform the severity conversion as specified. The missing YAML mapping file must be added for the task to be complete.
- **T018** — declared artifact(s) missing/empty/invalid: data/generated/snippets.csv
