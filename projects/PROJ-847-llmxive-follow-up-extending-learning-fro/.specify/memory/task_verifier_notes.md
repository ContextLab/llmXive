# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/run_experiments.py exit=1
- **T002** — The repository contains the rewritten `code/data.py` with the correct streaming loaders, but the required `data/raw/manifest.txt` file is missing, so the task’s requirement to record sample sizes and source identifiers is not satisfied.
- **T003** — The repository contains `code/diffusion.py`, which implements a masking schedule, but the required real diffusion checkpoint is never loaded (no `code/model.py` or `load_diffusion_model` function) and the metadata file `outputs/model_checkpoint.json` is missing. Additionally, the test suite fails because the `torch` dependency is not installed, so the verification command cannot be run. These missing pieces prevent the task from being considered complete.
- **T004** — Requested task execution failed; rerun successfully: code/run_thin_training.py exit=1
