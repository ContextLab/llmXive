# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/bootstrap.py` script fails its own test (`test_bootstrap_creates_structure`) because it cannot monkey‑patch `paths.root`, causing an error and preventing verification that the directory layout and pinned `requirements.txt` are created. Moreover, the repository contains a top‑level `requirements.txt` that does not match the pinned list written by the script (the script writes a different file under `code/requirements.txt`). Consequently, the required project layout, the correct requirements file, and a proven runnable entry point are not demonstrably provided.
- **T002** — Requested task execution failed; rerun successfully: code/ingestion/download_data.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/salience/generate_maps.py exit=1
