# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007a** — the task writes platform-owned path(s) inside the project: `state/artifact_hashes.json` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T008a** — The `checkpoint.py` file exists but its `save_checkpoint` and `load_checkpoint` signatures do not match the required `save_checkpoint(state: dict, path: str)` / `load_checkpoint(path: str) -> dict`, and the current implementation saves files to the wrong location, causing the provided unit tests to fail (2 of 4 tests error). The task therefore is not satisfied.
- **T033a** — The `code/scripts/utils/pagination.py` helper is present, but the required unit test `tests/test_pagination.py` is missing and there is no provided evidence that `fetch_data.py` actually calls `paginate_api`. Both are needed to satisfy the task.
- **T001** — Requested task execution failed; rerun successfully: code/scripts/fetch_data.py exit=1
