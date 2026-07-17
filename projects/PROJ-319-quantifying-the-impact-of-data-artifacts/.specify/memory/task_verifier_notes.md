# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — The repository contains `code/synthetic/generator.py`, but the shown code is truncated and provides no function that writes ground‑truth ellipticity/asymmetry to a JSON file. Moreover, the required `data/synthetic/gt_metadata.json` does not exist at all. Hence the task’s core requirement—saving exact ground‑truth values to a JSON metadata file—is not fulfilled.
- **T015** — The required `data/synthetic/gt_metadata.json` file is absent, so the pipeline cannot load ground truth as specified. Moreover, the provided excerpt of `code/main.py` does not demonstrate loading that JSON or invoking `run_noise_significance_test`. Both the missing artifact and the lack of the required functionality mean the task is not genuinely completed.
- **T022** — The repository lacks the required `data/synthetic/gt_metadata.json` file, and the provided `code/main.py` excerpt does not contain any logic that loads this ground‑truth JSON or invokes `run_saturation_significance_test` as specified. Consequently the pipeline step described in the task is not implemented.
- **T024** — declared artifact(s) missing/empty/invalid: data/processed/saturation_sweep.csv
