# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — The provided `metadata.py` does not use `datetime.now(timezone.utc)`, never reads `data/assets/generation_log.json` (the file is missing), and contains no logic to write the required `data/stimuli/{id}_metadata.yaml` files or include the asset parameters. Additionally, the script is truncated (e.g., `return` statement is incomplete) and no generated metadata files are present. These omissions mean the task requirements are not met.
- **T035#1** — The repository contains `code/analysis/anova.py`, but the file is truncated and never writes the required `data/analysis/anova_results.json`. Moreover, the JSON results file is missing entirely, so the task’s output artifact and schema verification are not satisfied.
