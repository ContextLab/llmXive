# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The synthetic fallback CSV (`data/raw/cochrane_base_synthetic.csv`, N=20, mu=0, sigma=1, valid effect sizes/SEs) exists and the script ran successfully, but the loader never attempts the required primary source — it fetches from a GitHub URL (`mpiktas/meta-analysis-data/jackson2010.csv`, which 404s) instead of Zenodo DOI `10.5281/zenodo.10286623`, so the real-data path specified by the task can never succeed. Additionally, `code/requirements.txt` contains `pytest`, violating the "only CPU-tractable dependencies (numpy, scipy, pandas, scikit-learn, matplotlib, pyyaml)" requirement. Fix: point `
- **T005** — Requested task execution failed; rerun successfully: code/main.py exit=1; code/main.py exit=1
