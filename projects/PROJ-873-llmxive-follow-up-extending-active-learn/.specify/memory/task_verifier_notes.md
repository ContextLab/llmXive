# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T057** — The provided `run_pipeline.py` defines `check_data_integrity` and the `PipelineDependencyError`, but the snippet does not show this check being invoked before the active ranker loop, so the required strict ordering is not demonstrably enforced. Additionally, the script’s usage of the check (or integration with the ranker calls) is absent from the visible code. The implementer must add a call to `check_data_integrity()` (or equivalent) right before the ranker execution begins and show that the script aborts with `PipelineDependencyError` when the prerequisite files are missing or empty.
