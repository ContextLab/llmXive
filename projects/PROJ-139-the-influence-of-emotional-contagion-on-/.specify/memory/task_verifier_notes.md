# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T002** — The provided `requirements.txt` is present but does not pin versions for any package, omits the required `langdetect` entry, and adds unrelated packages (`pytest`, `ruff`, `black`). To meet the task, the file must list exactly the requested packages with explicit version specifiers (e.g., `pandas==1.5.3`).
- **T003** — `docs/quickstart.md` contains the required one‑line command, but the expected output file `data/results/sample_run.csv` is missing, so the documented command’s result is not demonstrated.
- **T003v** — declared artifact(s) missing/empty/invalid: data/results/sample_run.csv
- **T004** — Requested task execution failed; rerun successfully: code/contracts/copy_schemas.py exit=1
