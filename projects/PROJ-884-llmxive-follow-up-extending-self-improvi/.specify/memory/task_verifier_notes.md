# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` files exist and appear to be valid YAML, but there is no evidence (e.g., command output, log, or test script) showing that `python -c "import yaml, sys; yaml.safe_load(open('contracts/dataset.schema.yaml'))"` (and the analogous command for `output.schema.yaml`) was actually executed and exited without exception. Provide execution logs or a test confirming the load succeeds.
- **T016** — Requested task execution failed; rerun successfully: code/main.py exit=2
- **T001** — The `code/tests/test_generator.py` test suite fails: the `test_invalid_type_raises` case raises an `AttributeError` because `generate_puzzles` tries to access `.value` on a plain string instead of detecting the invalid type and raising `DataGenerationError` as required. Consequently the required pytest pass condition is not met, so the task is not fully satisfied. The verifier and timing log appear correct, but the generator’s error‑handling must be fixed.
- **T003** — Requested task execution failed; rerun successfully: code/bes/main.py exit=1
