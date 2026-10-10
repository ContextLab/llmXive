# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The provided `requirements.txt` lists the required packages but uses “>=” version specifiers instead of exact pins and adds many extra dependencies; there is no evidence that `pip install -r requirements.txt` was run successfully without conflicts. To satisfy the task, the file must pin exact versions for the listed packages (e.g., `numpy==1.24.0`) and include verification that installation completes cleanly.
- **T004** — The `ruff.toml` and `pyproject.toml` files exist and contain the required settings, but there is no provided evidence (e.g., command‑line output or logs) that `ruff check .` and `black --check .` were actually run and reported zero violations. Without that execution proof, the task’s verification requirement is unmet.
