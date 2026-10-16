# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/`, `data/raw/`, `data/processed/`, `data/results/`, and `tests/` directories all exist and `code/__init__.py` is present, but there is no evidence of a `.gitignore` file in the project root. Adding a standard `.gitignore` is required to satisfy the task.
- **T050** — The provided `code/main.py` only writes a placeholder CSV with column headers and records a trivial RAM estimate; it does not download data, run preprocessing, generate models, or produce any intermediate artifacts. Consequently the final `results_summary.csv` is empty of real results and the full end‑to‑end pipeline is not executed as required. The missing components are the data ingestion steps, intermediate files, and a populated results summary reflecting actual computations.
