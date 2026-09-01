# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — declared artifact(s) missing/empty/invalid: code/config.py
- **T015** — The `preprocess.py` file defines `load_schema` but does not import `jsonschema` nor call `jsonschema.validate` on the filtered DataFrame, and the `validate_schema` function is truncated and incomplete. Consequently, the required schema loading and validation step after filtering is not implemented.
