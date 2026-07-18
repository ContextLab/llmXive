# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory or file structure named `projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/` was presented; the response contains only the specification text and no tangible project scaffold. The required artifact (the created project folder with appropriate sub‑folders/files) is missing.
- **T003** — No evidence of black or flake8 configuration files (e.g., `pyproject.toml`, `.flake8`, or `setup.cfg`) in the `code/` directory was provided, so the required linting/formatting setup cannot be confirmed. The implementer must add the appropriate config files and ensure they are non‑empty.
- **T007** — The required `data/raw/occ_rag_corpus.jsonl` file is missing, and `data/checksums.json` contains an empty `"artifacts"` map, so no checksum information is recorded. Both artifacts are incomplete relative to the task specification.
- **T014** — No code, script, or output file implementing the sorting‑by‑magnitude‑of‑performance‑drop logic (or using `CONFIG.RETENTION_PCT` to select the cutoff) was provided. The claim lacks any concrete artifact (e.g., Python module, CLI tool, or CSV result) that demonstrates the required “Critical Sub‑network” identification, so the task is not satisfied.
- **T015** — No code, configuration, test, or documentation artifact showing the new edge‑case flag (sensitivity Δ < 0.01) and its explicit linkage to Critical Sub‑network identification failure was provided; without such evidence the requirement cannot be confirmed as satisfied.
- **T019** — declared artifact(s) missing/empty/invalid: code/03_finetune_pruned.py, data/raw/occ_rag_corpus.jsonl
- **T020** — declared artifact(s) missing/empty/invalid: code/03_finetune_pruned.py
- **T021** — The required artifact `code/03_finetune_pruned.py` does not exist, so there is no script to verify CPU‑only execution, runtime limit, or optimizer usage. The implementer must add the missing file with a functional implementation that meets the specified constraints.
- **T022** — declared artifact(s) missing/empty/invalid: code/03_finetune_pruned.py
- **T025** — No code, script, or documentation implementing the p‑value check (p < 0.05 → flag significant, p ≥ 0.05 → not significant) was found in the provided artifacts; the required logic is absent. The task therefore remains unfulfilled.
- **T026** — No script, notebook, or output file that computes the Pearson correlation between the sub‑network sensitivity scores and a same‑size random subset (using CONFIG.SAMPLE_SEED) is present, nor any flagging of correlations > 0.2. The required artifact is missing.
