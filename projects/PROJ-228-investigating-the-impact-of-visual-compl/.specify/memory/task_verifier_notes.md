# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or file system evidence were provided showing that `code/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/interim/`, and `data/results/` actually exist; without such artifacts the requirement cannot be confirmed. The implementer must supply proof (e.g., a tree listing or screenshots) that these directories have been created.
- **T013** — The provided `tests/integration/test_ingestion.py` is truncated and does not contain the required post‑pipeline assertion `assert os.path.exists(csv_path) and len(csv_path) > 0`. Moreover, the expected output file `data/interim/complexity_metrics.csv` is absent, so the test cannot verify its existence or non‑emptiness. The integration test therefore does not satisfy the task specification.
