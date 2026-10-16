# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The evidence only shows a `requirements.txt` at the project root with the correct pinned versions; the required file under `code/requirements.txt` is listed but its contents are not provided, and no CI install logs are shown. Without confirming the `code/` version contains the exact package list (including the `torch` line) and that it successfully installs, the task is not fully satisfied.
- **T004** — the task writes platform-owned path(s) inside the project: `state/artifact_hashes.json` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T007** — the task writes platform-owned path(s) inside the project: `state/validated_n.json` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
