# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — No `results_full.csv` file was presented at the required location, nor any content showing the columns `game_id`, `specialization_index`, `retrieval_efficiency`, `context_condition`, `agent_count`. Without the actual CSV artifact, the task’s requirement cannot be confirmed as satisfied.
- **T018** — The provided `run_experiment.py` file is present, but the displayed excerpt never shows any logic that actually truncates the context based on a token limit (e.g., calling `truncate_context_to_token_limit` or using `GameConfig.token_limit`). The implementation of limited‑context simulation is therefore not evidenced. The next implementer must add code that, when `--context limited` is specified, trims the accumulated context to the configured token limit before it is fed to the model.
