# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No script or directory structure was provided; there is no evidence of a file that creates the required folders (`code/`, `tests/`, `data/`, etc.) with `.gitkeep` files, nor any verification code using `os.path.exists`. The implementer must supply the initialization script and demonstrate that it creates and checks all specified directories.
- **T031a** — The required log file `data/processed/lint_log.txt` does not exist, so there is no evidence that `ruff check code/` was run or that it succeeded. Without this artifact the task cannot be considered completed.
- **T031b** — declared artifact(s) missing/empty/invalid: data/processed/type_log.txt
