# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `tests/unit/test_trainer.py` suite fails with an `AttributeError` because the `config` object passed to `Trainer` lacks the required `memory_limit_bytes` attribute, causing the trainer initialization to abort. Consequently the warm‑up, dream‑phase triggering, perplexity‑skip, and entropy‑retry checks are never exercised, so the core Wake/Dream training loop does not meet the task’s verification requirements. Fix the configuration (ensure `memory_limit_bytes` is present) and re‑run the unit tests.
- **T003** — Requested task execution failed; rerun successfully: code/train.py exit=1
- **T005** — The quickstart.md file exists and contains a runnable command, and the expected JSON result file is present, but there is no evidence that the command was actually executed in a fresh environment without error (no logs, CI run output, or verification script results). Concrete proof of successful execution is missing.
- **T006** — The integration test `tests/integration/test_token_parity.py` fails – the subprocess call to `code/baseline.py` exits with status 2 (argparse error), so no log is produced and the token‑parity assertion is never evaluated. Consequently the required baseline that mirrors real‑token exposure is not verified as functional.
- **T007** — Requested task execution failed; rerun successfully: code/main.py exit=1
