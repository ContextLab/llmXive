# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The environment script correctly pins random seeds and writes them to `data/env_config.json`, and the Docker image tag (`gcc:13.2`) is recorded, but there is no evidence in `plan.md` showing the expected Docker digest to compare against the one stored in `env_config.json`. Without a documented digest in the plan, the required verification cannot be confirmed.
- **T001** — Requested task execution failed; rerun successfully: code/download_human.py exit=1
