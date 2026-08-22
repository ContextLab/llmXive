# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directory tree (code/, data/raw/, data/processed/, tests/, docs/, docs/reports/) is presented; the implementer did not provide any file‑system listing, screenshots, or other proof that these folders exist and are non‑empty. The task therefore remains unverified.
- **T016** — The repository contains `code/data/generate.py` with a correct matrix‑generation function, but the script never writes the resulting array to `data/processed/synthetic_phylo_matrix.npy`, and that file is absent from the project. The required output file is missing, so the task is not fully satisfied.
- **T012** — The repository contains a partially‑implemented `code/data/generate.py` (the shown portion stops after creating the DataFrame and does not show label computation or CSV writing). Moreover, the required output file `data/processed/synthetic_genomics.csv` is absent. The task’s core deliverables—generating labels per the specified rule and persisting them to the exact CSV path—are therefore not fulfilled.
- **T019** — declared artifact(s) missing/empty/invalid: tests/unit/test_stats.py
- **T029** — The `code/models/compare.py` file does not implement the required validation logic (checking the count of the 15 validation genes among the top‑10 features) nor does it create/write `docs/reports/final_analysis.md`. Moreover, the `final_analysis.md` file is absent from the repository. Both the script and the final report are missing, so the task is not satisfied.
- **T030** — declared artifact(s) missing/empty/invalid: data/logs/metrics.json
