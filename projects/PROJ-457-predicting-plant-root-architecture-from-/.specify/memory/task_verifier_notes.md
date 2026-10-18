# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The collector's artifact listing includes `code/config.py`, `code/models.py`, and `config.yaml`, but the required `config.yaml.template` is not present among the resolved artifacts — only a passing test log asserts it exists, which is not file evidence. The implementer must actually create `config.yaml.template` at the project root (and it should be a meaningful template of the config keys, not merely absent).
- **T006** — Requested task execution failed; rerun successfully: code/ingestion.py exit=1
