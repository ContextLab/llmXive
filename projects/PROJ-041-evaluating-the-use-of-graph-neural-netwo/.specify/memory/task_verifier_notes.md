# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The core artifacts exist (directories, `__init__.py` files, `requirements.txt`, `pyproject.toml`, `seed.py`, `memory_monitor.py`), but key requirements fail: (1) `run_with_limit` is a simulated stand-in — it never executes a function or performs a dummy allocation, it merely compares `limit_gb * 1024` against the configured limit, so it cannot actually wrap work or enforce a real 7 GB RAM constraint as specified; (2) `requirements.txt` pins `tracemalloc==0.1.0`, a nonexistent PyPI package (tracemalloc is stdlib), and `torch==2.3.0+cpu` needs an extra index URL, so `pip install -r requirements.
- **T002** — Requested task execution failed; rerun successfully: code/data/download_ctu13.py exit=1
