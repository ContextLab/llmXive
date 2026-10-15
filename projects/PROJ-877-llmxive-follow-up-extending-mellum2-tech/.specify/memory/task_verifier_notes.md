# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — Requested task execution failed; rerun successfully: code/verify_environment.py exit=2
- **T001b** — `quickstart.md` exists (2186 bytes) and contains the required command, environment-activation instructions, usage notes, and runtime limits, so the document content itself matches the task. However, the task's explicit verification criterion — that `python -m code.main --phase all --sample small` runs without raising parsing errors — has no supporting execution evidence: the only underlying artifact is an environment check showing several pinned packages (tree_sitter_python, tree_sitter_java) failing to import, and the doc's own claim that "the `--sample` flag is now accepted by `code/main.py`
- **T002** — declared artifact(s) missing/empty/invalid: data/processed/raw_chunks.parquet, data/checksums.txt
