# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — The provided `code/data_loader.py` only contains helper functions and a partially shown `validate_qrels_schema`; it never loads data, applies the schema validation to all records, nor logs warnings for zero‑relevance queries. Moreover, the required schema file `contracts/dataset.schema.yaml` is missing, so the validation cannot reference it. The task’s core requirements are therefore not satisfied.
