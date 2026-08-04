# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T080** — The `distill_rules.py` script contains a validation function, but the required schema file (`distilled_rule.schema.yaml`) is missing, so the validation cannot actually run. Moreover, the truncated portion of the script does not show the validation being applied before writing `rules_library.json`. The task’s core requirement—strict schema validation of every generated rule—is therefore not fulfilled.
