# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019b** — The required output file `data/derived/energy_samples.csv` is absent, and the provided `code/ingestion.py` snippet is incomplete (truncated) with no visible energy‑calculation implementation or CSV‑writing logic. Consequently the task’s core deliverable—correct generation of the energy samples file with proper `E_vib` units—is not satisfied. The next implementer must add the energy computation (mass × variance for `E_vib`) and ensure the script writes the resulting dataframe to `data/derived/energy_samples.csv`.
