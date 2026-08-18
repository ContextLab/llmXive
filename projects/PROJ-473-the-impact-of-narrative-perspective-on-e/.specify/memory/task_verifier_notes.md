# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T016** — The repository contains a `code/main.py` file, but it is truncated and does not show the required CLI (`extract` subcommand) or the logic that enforces the short‑text skip‑and‑log behavior. Moreover, the expected output file `data/processed/perspective_features.json` is absent, so the pipeline’s result cannot be verified. The missing output and unclear CLI implementation mean the task is not fully satisfied.
- **T025** — The repository lacks the required `data/processed/matching_results.json` (and the input files it depends on), and the provided `code/main.py` is truncated with no visible argparse sub‑command implementation for `match`. Consequently the matching validation command cannot be executed as specified.
