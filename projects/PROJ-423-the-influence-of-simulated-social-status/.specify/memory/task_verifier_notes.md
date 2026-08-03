# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003b** — No `.gitignore` file was presented in the evidence, and thus we cannot confirm that it exists, is non‑empty, and contains the required patterns (`__pycache__`, `*.pyc`, `.env`, `data/processed/*.csv`) while deliberately not ignoring `data/raw/*.csv`. The implementer must provide the actual `.gitignore` content meeting these specifications.
- **T050** — No `plan.md` file or its contents were presented, so we cannot confirm that the sensitivity sweep threshold list was changed to `{2.5, 3.0, 3.5}` in the specified sections. The required artifact is missing.
- **T051** — No updated `plan.md` file was provided, nor any evidence (diff, excerpt, or commit message) showing that references to `structure_config.json` were replaced with `model_config.json` or that an alias generation in T021c was documented. The required artifact is missing, so the task is not satisfied.
