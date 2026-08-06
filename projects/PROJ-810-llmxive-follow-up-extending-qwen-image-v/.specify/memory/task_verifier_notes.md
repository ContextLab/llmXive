# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The `src/analysis/separability.py` script correctly implements the power‑analysis logic and would write the required fields, but the expected output file `data/results/power_analysis.json` is absent, so the deliverable is not present. The missing JSON file must be generated (e.g., by running the script) and contain `N_required`, `effect_size`, `power`, and `N_audit`.
- **T001** — The provided `vae_loader.py` checks a different model (`Qwen/Qwen2-VL-2B-Instruct`) instead of `Qwen-Image-VAE-2.0`, and the required `data/results/model_availability.json` file is absent. Consequently the task’s core validation and deliverable are not satisfied.
- **T003a** — No evidence of the required directories (`src/`, `tests/`, `specs/`, `data/`, `data/results/`, `data/manual/`) is provided; the submission contains only the task description and specifications, with no file‑system artifacts to verify that the project structure was actually created.
