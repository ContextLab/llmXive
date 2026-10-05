# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or other evidence were provided showing that the required folders (`src/bias_pipeline`, `src/cli`, `data/raw`, `data/processed`, `data/validation`, `tests/unit`, `tests/integration`, `state`) actually exist; the claim is unsubstantiated. The implementer must supply a file‑system snapshot, `tree` output, or similar proof that the structure was created.
- **T003** — The repository contains a `pyproject.toml` with the required Black and pytest sections, but the required `.ruff.toml` file is missing; the ruff configuration is only present inside `pyproject.toml`, which does not satisfy the task’s explicit requirement for a separate `.ruff.toml`.
- **T006** — No evidence was presented showing that a `data/` directory with the subfolders `raw`, `processed`, and `validation` actually exists; the claim is unsubstantiated. The implementer must provide proof (e.g., a directory listing or screenshot) that the required directories were created.
- **T006a** — No evidence of a script or notebook that loads the `codeparrot/github-code` dataset, filters for Python files, and clones 500 repositories into a `data/raw` directory is present. The required `data/raw` folder with the cloned repositories is missing, and there is no indication that the implementation fails loudly on fetch errors or avoids synthetic fallbacks.
- **T043a** — declared artifact(s) missing/empty/invalid: src/bias_pipeline/extractor.py
- **T043c** — declared artifact(s) missing/empty/invalid: src/bias_pipeline/analyzer.py
- **T0410** — declared artifact(s) missing/empty/invalid: data/validation/labels.csv
- **T0411** — declared artifact(s) missing/empty/invalid: data/validation/labels.csv
- **T0412** — No artifact (e.g., script, log output, test result) was provided that actually checks the contents of `data/raw` for the required repository count, nor any evidence that such a pre‑condition verification was performed. The implementer’s claim lacks concrete proof.
- **T012a** — declared artifact(s) missing/empty/invalid: src/bias_pipeline/extractor.py
