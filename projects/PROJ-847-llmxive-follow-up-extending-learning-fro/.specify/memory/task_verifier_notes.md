# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required `configs/full_suite.yaml` is explicitly MISSING from the project, and `data/results/` (which the verification says the quickstart run must create) also does not exist, with no execution evidence that `python -m code.run_experiments --config configs/quickstart.yaml` ever ran successfully. Additionally, `docs/quickstart.md` cannot document which artifacts `full_suite.yaml` regenerates or its wall-clock cost since that config doesn't exist, and the quickstart config's "thin run" actually delegates to a trainer that fabricates accuracy values via a deterministic dummy formula rather t
- **T002** — Requested task execution failed; rerun successfully: code/data.py exit=1
