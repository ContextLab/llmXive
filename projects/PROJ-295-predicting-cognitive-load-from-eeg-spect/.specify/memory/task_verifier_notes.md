# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T030** — The provided `code/main.py` does not define the required `--data-dir` and `--output-dir` CLI arguments, never imports or calls the `check_and_halt()` function from T042, and lacks any logic to load the T028, T038, T041, and T042 result files, merge them, compare the R² to the `r2_threshold` in `pipeline_config.yaml`, or exit with an error when the threshold is not met. Consequently, running the script does not produce the required `results/model_metrics.json` file (which is missing).
