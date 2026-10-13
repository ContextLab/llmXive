# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000c** — The provided execution log (`code/.tasks/T000c.code_data_ingestion.py.log`) contains no line with the required text “Data feasibility confirmed”, and the expected `logs/pipeline.log` file is not present in the evidence. Consequently the task’s core requirement—logging the confirmation message when a suitable dataset is found—is not satisfied.
- **T002a** — Checked the `requirements.txt` file (14 bytes) which only contains `python-dotenv`. It does not list any of the required core packages (pandas, scikit‑learn, scipy, numpy, biom-format, scikit‑bio, matplotlib, seaborn, requests, pytest, statsmodels) nor pin their versions, so the task’s requirement is not satisfied.
- **T002c** — the task writes platform-owned path(s) inside the project: `state/seeds.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T009** — Requested task execution failed; rerun successfully: code/data_ingestion.py exit=1
