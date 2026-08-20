# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020a** — The required input files `data/raw/barrier_dataset.csv` and `data/confounds.csv` are absent, and the provided `code/dft_calculator.py` does not contain the described subset‑selection logic (reading the CSV, computing N, stratified sampling with `pd.qcut`). Hence the task’s specifications are not met.
- **T020b** — The repository contains a partially shown `code/dft_calculator.py`, but the file is truncated and does not demonstrate the required Psi4 invocation, output parsing for HOMO/LUMO, StratifiedKFold with a fixed `random_state`, or creation of `data/descriptors_dft.csv`. Moreover, the expected `data/descriptors_dft.csv` file is absent. The task’s core outputs are therefore missing.
