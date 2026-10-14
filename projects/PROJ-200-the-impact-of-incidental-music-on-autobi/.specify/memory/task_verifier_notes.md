# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The `state.yaml` exists and was created by a successful run of `code/init_state.py`, but its structure does not match the task requirement: it contains `config`, `files: {}`, and `updated_at`, but no `artifact_hashes` key (the task explicitly requires `artifact_hashes`, `updated_at`, `config`). The implementer should fix `init_state.py` to emit an `artifact_hashes` mapping (or rename `files` accordingly) and regenerate the file.
