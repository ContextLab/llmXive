# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003b** — declared artifact(s) missing/empty/invalid: scripts/hash_artifacts.sh, src/utils/checksum.py
- **T014** — The repository lacks the required `data/results/generalization_report.md` file, and the provided `src/experiments/baseline_runner.py` excerpt does not show a `validate_generalization` implementation (the file is truncated before any such function). Both the output artifact and the specific function implementation are missing, so the task is not satisfied.
- **T010b** — The provided `src/training/homeostasis.py` does not contain a `log_gradient_norms` function (the file is truncated and ends mid‑implementation of `scale_weights`). Additionally, the required output file `data/logs/gradient_norms.json` is missing. Both the function definition and the log file are required to satisfy the task.
