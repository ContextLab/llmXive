# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — I looked for the four required top‑level directories (`code/`, `data/`, `tests/`, `paper/`) in the provided artifact list, but no directory entries or file listings were supplied. Since there is no evidence that these directories were actually created, the task’s requirement is not satisfied. The implementer must add the missing directory structure (or provide a manifest showing they exist).
- **T003** — declared artifact(s) missing/empty/invalid: pyproject.toml, ruff.toml
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — declared artifact(s) missing/empty/invalid: tests/unit/test_static_analysis.py
- **T014** — The repository lacks the required `data/processed/raw_metrics.json` file (the processor never created it) and the schema file `contracts/output.schema.yaml` is absent, so the output cannot be validated against the specified schema. Additionally, the provided `processor.py` is truncated, leaving uncertainty that it fully implements the waiting, filtering, timing, and efficiency‑reporting steps. These missing artifacts prevent the task from being considered complete.
- **T022** — The repository contains `code/llm/pipeline.py`, but the file is truncated and does not show the full implementation (e.g., the loop body is cut off). More critically, the required output artifact `data/processed/refactoring_results.json` is absent, so the pipeline does not actually save the deltas as specified. The missing result file must be generated for the task to be considered complete.
