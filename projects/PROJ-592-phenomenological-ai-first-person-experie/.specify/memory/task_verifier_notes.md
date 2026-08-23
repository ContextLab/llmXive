# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — The `control_corpus.py` script exists but is incomplete (truncated) and does not show logic for appending `type='control'` or writing a merged CSV. Moreover, the required `data/processed/merged_dataset.csv` file is missing, so the verification step cannot succeed. The task’s core output is not present.
- **T013** — declared artifact(s) missing/empty/invalid: data/raw/generation_log.json
- **T012** — The repository contains `code/generation/runner_local.py`, but the required output file `data/raw/local_generation_test.json` is absent, meaning the verification step (`python code/generation/runner_local.py --test`) does not produce the expected artifact. The task is therefore not fully satisfied.
