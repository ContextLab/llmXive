# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T003** — The `code/utils/hygiene.py` file exists, but the required state file `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml` is missing, and the unit test that checks hash calculation and state update fails because the state file is not created. Consequently, there is no evidence that running the helper records the correct SHA‑256 hash in the state YAML. The task’s core requirement is therefore unmet.
