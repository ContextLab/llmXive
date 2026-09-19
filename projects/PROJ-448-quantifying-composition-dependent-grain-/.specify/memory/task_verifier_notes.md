# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The required artifact `data/raw/dft_energies.json` is missing entirely, so the implementer cannot verify that it lacks `MISSING_SOURCE: true` nor demonstrate the abort behavior. The task’s core requirement is therefore unmet.
- **T013b** — The `load_dft_energies.py` script is present, but the required source file `data/raw/dft_energies.json` does not exist, so the function cannot actually load any DFT energies (it would raise `DataLoadError`). No placeholder file is provided either, meaning the implementation cannot satisfy the task’s core requirement.
