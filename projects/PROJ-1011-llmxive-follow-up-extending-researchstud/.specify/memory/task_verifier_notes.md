# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The three data directories exist (each with a `.gitkeep`), but the required `data/CHECKSUMS` manifest is not confirmed present in the collected evidence, and the task's own verification test `test_data_dirs_and_checksum` FAILED (exit 1) with `FileExistsError: .../data/CHECKSUMS` — the toolkit's `paths.data()` helper tries to mkdir a parent that collides with the existing CHECKSUMS file. The implementer must fix the path handling (or ensure CHECKSUMS exists and the test passes) and provide evidence of a passing verification run.
- **T006** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T008** — Requested task execution failed; rerun successfully: code/error_handling_wrapper.py exit=1
