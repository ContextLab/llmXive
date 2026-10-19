# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The quickstart markdown is present, but the entry‑point scripts are broken: `code/main.py` imports several analysis modules that are not in the repository (e.g., `analysis.stats`, `analysis.run_nbs`), causing an import error; `code/data/run_synthetic_generator.py` imports a non‑existent `synthetic_generator` module; `code/run_quickstart_test.py` invokes a pytest file that is not provided. Consequently the required commands cannot run end‑to‑end and the task is not satisfied.
- **T002** — Requested task execution failed; rerun successfully: code/data/run_synthetic_generator.py exit=1
