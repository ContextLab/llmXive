# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The `src/analysis/separability.py` script exists and contains a power‑analysis implementation, but it writes its results to `data/results/power_analysis.json`, which is absent on disk. Moreover, the default `effect_size` is set to 0.8 (not strictly greater than 0.8) contrary to the task’s “d > 0.8” requirement. The required JSON output is therefore missing and the parameter condition is not met.
- **T001** — The `src/models/vae_loader.py` contains placeholder model IDs and does not implement the logic to write the required `model_availability.json`. Moreover, the `data/results/model_availability.json` file is missing entirely. The task’s deliverable is not present.
- **T002** — declared artifact(s) missing/empty/invalid: src/utils/memory.py, data/results/memory_budget.json
- **T002b** — declared artifact(s) missing/empty/invalid: src/utils/memory.py, data/results/runtime_fallback.json
