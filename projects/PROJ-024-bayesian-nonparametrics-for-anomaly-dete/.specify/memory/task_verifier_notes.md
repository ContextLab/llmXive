# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T060** — The provided `code/config.yaml` does not contain the required keys (`dataset_stats`, `inference_results`, `simulation_metrics`), so there is nothing for the script to migrate. Moreover, the `migrate_config.py` script is truncated (ends with a stray “p”) and never checks that `code/config.yaml` is under 2048 bytes. Both the migration of the specified keys and the size verification are missing.
