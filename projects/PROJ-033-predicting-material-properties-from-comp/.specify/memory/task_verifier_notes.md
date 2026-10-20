# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required contracts, requirements.txt, seeds.py, and quickstart.md are present and correctly populated, but the contract test suite does not fully pass – `tests/contract/test_dataset_schema.py` fails because the schema rejects a valid row (expects an array but receives an object). Consequently the verification step “pytest tests/contract/ passes” is not satisfied.
- **T002** — Requested task execution failed; rerun successfully: code/verify_dataset.py exit=1
- **T003** — Requested task execution failed; rerun successfully: src/data/loader.py exit=1
