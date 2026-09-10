# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T046** — The required artifact `tests/integration/test_pipeline.py` is missing from the repository, so no integration test exists to verify full pipeline execution on sample data. The task cannot be considered completed until this file is added with a functional end‑to‑end test.
- **T060** — No GitHub Actions workflow file or CI configuration was provided, and there is no evidence of a step that runs a script asserting `torch.cuda.is_available()` is `False`. Without the workflow artifact showing this check, the requirement is not satisfied.
