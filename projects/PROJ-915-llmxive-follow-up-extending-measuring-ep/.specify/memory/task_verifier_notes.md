# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T003b** — The `pyproject.toml` exists and correctly configures Black (line-length 100, target py311), but the task's stated verification — `black --check code/` returning exit code 0 — fails: the recorded test run shows exit code 1 with 23 files in `code/` needing reformatting. The implementer must run `black code/` (or otherwise bring the code into Black-compliant form) so the check passes.
