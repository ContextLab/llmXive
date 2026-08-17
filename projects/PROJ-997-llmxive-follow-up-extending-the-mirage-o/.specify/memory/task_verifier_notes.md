# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T021** — The provided `src/cli/train_predictor.py` is incomplete (the `save_model` function is truncated and never called) and the required output file `data/models/gap_predictor.pkl` does not exist. Consequently the script does not actually save a trained KRR model artifact as the task demands.
- **T027** — The provided `run_baseline_sync.py` is truncated (e.g., an unfinished `else` clause) and does not contain the full logic to run inference, compute acceptance_rate, timing metadata, or write `data/processed/baseline_metrics.json`. Moreover, the required `baseline_metrics.json` file is missing entirely. The task therefore remains unfinished.
- **T029** — The `src/utils/stats.py` file is truncated and does not contain a complete implementation of the paired t‑tests, Bonferroni correction, or JSON generation. Moreover, the required `data/processed/t_test_results.json` file is absent. Both the functional code and the expected output artifact are missing.
