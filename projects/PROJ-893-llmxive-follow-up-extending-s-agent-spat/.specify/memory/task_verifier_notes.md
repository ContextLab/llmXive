# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure (`code/`, `data/raw/`, `data/derived/`, `data/results/`, `specs/`, `tests/`) is present in the provided artifacts; the claim lacks any tangible evidence that the required folders were created.
- **T004** — The `code/hygiene.py` file is truncated (e.g., `load_state_yaml` ends with a typo and the script never writes the computed hashes back to the YAML), and the required state file `state/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat.yaml` does not exist at all. Both the implementation and the target artifact are missing/incomplete.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The `run_solver.py` script is incomplete (truncated) and never writes to the required `data/derived/predictions.jsonl` or `data/derived/latency_log.jsonl` files, which are absent from the repository. Consequently the task’s output artifacts are missing.
