# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The only artifact present is a `requirements.txt`, but it lists version ranges (e.g., `numpy>=1.26.0,<2.0.0`) rather than exact pinned versions, which does not satisfy the “pinning” requirement. Moreover, no other project‑initialization files (e.g., `pyproject.toml`, `setup.cfg`, or a marker of Python 3.11) are provided, so the Python 3.11 project is not fully initialized.
- **T006** — The `specs/001-decoding-internal-states/contracts/` directory exists but the four required schema files (`dataset.schema.yaml`, `output.schema.yaml`, `alignment_results.schema.yaml`, `correlation_results.schema.yaml`) are all reported as MISSING. Without these files the task of creating the base data schemas is not satisfied.
