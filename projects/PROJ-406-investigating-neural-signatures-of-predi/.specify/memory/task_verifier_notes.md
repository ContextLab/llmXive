# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The seed utility (`src/utils/seed.py`) and package import (`src/__init__.py`) exist and correctly set the global seed, and `outputs/seed_verification.log` contains two identical deterministic values. However the CI test `test_seed_verification_script_creates_log` fails (AttributeError on monkeypatching `ProjectPaths.root`), meaning the automated verification that the script creates the log and that CI asserts the identical lines does not succeed. The task’s requirement that CI validates the log is therefore not met.
- **T001** — Requested task execution failed; rerun successfully: src/ingest/load_illusions.py exit=1
