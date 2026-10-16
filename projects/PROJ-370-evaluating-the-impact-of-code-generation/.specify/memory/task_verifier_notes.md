# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/src/*`, `code/tests/*`, `code/data/*`, and `code/logs` directories all exist and the setup script ran successfully (exit 0). However, the task's verification command explicitly requires `specs/001-eval-llm-review-quality/contracts`, while the execution log shows the script created a differently-named path, `specs/001-evaluating-the-impact-of-code-generation/contracts`, and no evidence confirms the requested `001-eval-llm-review-quality/contracts` directory exists — the implementer should create the exact requested path (or reconcile the naming with the feature branch slug).
