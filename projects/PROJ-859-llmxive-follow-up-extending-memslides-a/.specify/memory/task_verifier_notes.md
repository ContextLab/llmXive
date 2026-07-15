# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — The provided `code/contracts/__init__.py` ends abruptly inside `validate_json_file` (the `except json.JSONDecodeError` block just does `return` without a tuple) and the file is truncated, indicating missing implementation. Moreover, no `contracts/trace.schema.yaml` file is shown, so we cannot confirm the schema exists or is being specifically validated. The task’s requirement is therefore not fully satisfied.
