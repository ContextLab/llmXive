# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The layout, pinned `requirements.txt`, and a `config.py` with CPU-only enforcement and a 6.3 GB memory check exist, and the unit tests passed. However, `config.py` imports `psutil`, which is not listed in `code/requirements.txt`, so a fresh `pip install -r code/requirements.txt` would not guarantee the module is importable (the passing test run only worked because psutil happened to be present in the venv). Additionally, the config's docstring openly states the "original implementation (not shown)" is elided, i.e., the file is a partial stand-in rather than the full configuration module. Fix:
- **T002a** — Requested task execution failed; rerun successfully: code/train.py exit=1
