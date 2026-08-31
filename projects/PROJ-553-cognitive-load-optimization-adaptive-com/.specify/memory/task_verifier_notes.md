# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: data/processed/golden_set_template.csv
- **T015** — The required model artifact `data/processed/load_model.pkl` does not exist, and the provided `code/train_load_model.py` is truncated before any training, validation, size‑check, or saving logic is shown. Consequently the pipeline is not fully implemented nor does it produce the required output.
- **T022b** — The required output file `data/explanation_tiers/moderate_tiers.csv` is missing, so no moderate‑tier content was generated for the instructional units. The task therefore is not satisfied.
- **T023** — The required output file `data/explanation_tiers/simple_tiers.csv` does not exist, so the implementation and iterative refinement loop cannot be verified. The missing CSV means the task’s core deliverable is absent.
- **T024** — declared artifact(s) missing/empty/invalid: data/explanation_tiers/complex_tiers.csv
- **T025** — No CSV or JSON files were presented in `data/explanation_tiers/`, nor any code showing that generated tiers and their metadata are being written to that directory. The required output files are missing, so the task is not satisfied.
