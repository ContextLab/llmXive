# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — declared artifact(s) missing/empty/invalid: state.yaml
- **T002** — Checked `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`. Both files exist and contain schema definitions, but the `dataset.schema.yaml` uses a non‑standard `nullable: true` keyword (not valid in JSON‑Schema draft‑07) and thus would fail strict `jsonschema` validation, meaning the contracts do not fully meet the spec’s validation requirement.
