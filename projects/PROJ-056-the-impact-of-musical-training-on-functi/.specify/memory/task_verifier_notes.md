# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The quickstart markdown is present, and `real_ingest.py` correctly prints a message, writes a JSON status file, and exits 0. However, `code/main.py` cannot run end‑to‑end because it imports many analysis modules (e.g., `analysis.stats`, `analysis.output_connectivity_results`, `analysis.run_nbs`, etc.) that are not present in the repository, causing ImportError. Likewise, `run_synthetic_generator.py` depends on a missing `data.synthetic_generator` module, and `run_quickstart_test.py` invokes a non‑existent pytest test file. Consequently the required entry points do not execute successfully, and
- **T002** — Requested task execution failed; rerun successfully: code/data/run_synthetic_generator.py exit=1
