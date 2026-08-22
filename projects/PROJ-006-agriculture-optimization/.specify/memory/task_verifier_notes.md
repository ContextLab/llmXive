# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010a** — The required file `src/cli/run_pipeline.py` is missing, so the integration wiring cannot exist. Moreover, the existing `synthetic_generator.py` does not implement the specified checks (it looks at `data/processed/`, does not consider `CI=true` or a `--no-synthetic` flag, and never raises a `FatalError`). The task’s core functionality is therefore not present.
- **T010b** — declared artifact(s) missing/empty/invalid: github/workflows/ci.yml
