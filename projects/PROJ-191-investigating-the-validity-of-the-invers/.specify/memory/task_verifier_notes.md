# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree named `projects/PROJ-191-investigating-the-validity-of-the-invers/` with the required sub‑folders is present in the provided evidence; the implementer did not supply any file‑system listing or screenshots confirming the creation of those directories. The task therefore remains unfulfilled.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or a pre‑commit hook setup) are present in the provided evidence, nor any documentation showing that Ruff and Black have been integrated into the project workflow. Without these artifacts, the requirement to configure linting (ruff) and formatting (black) is not satisfied.
- **T007** — The submission provides only a textual description of the overall project and user stories; it contains no script, command, or file‑system listing showing that the `data/raw/`, `data/processed/`, and `data/results/` directories have been created (or that `mkdir -p` logic is used). Consequently, the required artifact demonstrating the directory structure is missing.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/state.json
- **T022** — No code, script, or module implementing the requested log‑likelihood function is present; there is no evidence that a function using the T015‑COV covariance matrix (full or block‑diagonal) and Cholesky decomposition was added. The required artifact is missing, so the task is not satisfied.
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/data_config.json
