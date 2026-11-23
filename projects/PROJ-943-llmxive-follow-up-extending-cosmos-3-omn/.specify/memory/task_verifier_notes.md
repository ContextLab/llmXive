# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The evidence contains no `code/.gitignore` file at all, let alone one with the required exact content. The implementer must add the missing `code/.gitignore` file with the specified lines.
- **T004** — declared artifact(s) missing/empty/invalid: code/data/schema/action_schema.json
- **T007** — The provided `code/tests/test_transform.py` exists, but its core test `test_composite_rule_violated` calls `apply_composite_rule(actions, text, schema)` and expects a string label, while the actual `apply_composite_rule` in `code/scripts/transform.py` takes numeric and boolean arguments and returns a bool. This mismatch means the test cannot verify that “L2 norm > 0.5 AND text keyword match → 'constraint_violated'” as required. The unit test must be corrected to use the proper function signature and check for the expected label.
- **T009** — Requested task execution failed; rerun successfully: code/scripts/download.py exit=1
