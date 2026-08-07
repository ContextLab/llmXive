# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree named `projects/PROJ-191-investigating-the-validity-of-the-invers/` with the required sub‑folders is present in the provided evidence; the implementer did not supply any file‑system listing or screenshots confirming the creation of those directories. The task therefore remains unfulfilled.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or a pre‑commit hook setup) are present in the provided evidence, nor any documentation showing that Ruff and Black have been integrated into the project workflow. Without these artifacts, the requirement to configure linting (ruff) and formatting (black) is not satisfied.
- **T007** — The submission provides only a textual description of the overall project and user stories; it contains no script, command, or file‑system listing showing that the `data/raw/`, `data/processed/`, and `data/results/` directories have been created (or that `mkdir -p` logic is used). Consequently, the required artifact demonstrating the directory structure is missing.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/state.json
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/covariance_matrix.npy
- **T023** — No code, script, or output file implementing the `emcee` runner was provided; the evidence on disk contains no artifact that starts with 5 000 steps, checks Gelman‑Rubin, and continues in 1 000‑step batches. Consequently the required functionality is missing.
