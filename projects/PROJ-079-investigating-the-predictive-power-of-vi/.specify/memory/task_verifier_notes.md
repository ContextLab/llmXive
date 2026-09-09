# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — declared artifact(s) missing/empty/invalid: tests/integration/test_data_pipeline.py, data/processed/merged_dataset.csv
- **T012** — The `fetch_viral_genomes` function in `src/download.py` is a stub that raises `NotImplementedError`, so no real NCBI Virus API query, FASTA parsing, or dict output is produced. Moreover, the required `data/manifest_v1.json` file does not exist, and the manifest generation logic does not compute SHA‑256 checksums or follow the exact key schema. The task’s core functionality and manifest output are missing.
- **T013** — The `fetch_geo_data` function is still a stub that raises `NotImplementedError`, so no GEO download or parsing occurs, and no dictionary of sample‑to‑strain accessions is produced. Moreover, the required `data/manifest_v2.json` file does not exist (and the manifest generation code leaves the `checksums` field empty). Both the core function and the manifest output are missing, so the task is not satisfied.
- **T014** — declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/normalized_counts.csv
- **T015** — declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/ortholog_map.csv
- **T016** — declared artifact(s) missing/empty/invalid: src/preprocess.py, data/processed/isg_scores.csv
- **T017** — The required file `src/preprocess.py` does not exist, so the `filter_samples` function cannot be present or verified. Consequently the task’s implementation is missing.
- **T018** — declared artifact(s) missing/empty/invalid: src/features.py
- **T018b** — declared artifact(s) missing/empty/invalid: src/features.py
- **T043a** — No pytest execution logs, coverage reports, or any test output files are present in the repository. The claim that `pytest --cov` was run on `src/` and `tests/` cannot be verified because the required artifacts (e.g., console output, `.coverage` file, HTML report) are missing. The task therefore remains incomplete.
- **T043b** — No coverage report file for the `src/` modules is present in the provided evidence, and there is no content showing line‑coverage percentages. Consequently, the requirement to verify that a coverage report exists and indicates >80 % line coverage cannot be confirmed.
- **T046** — No source files, validation code, or unit‑test files were presented; the claim that all public functions in `src/` now perform null/type/range checks and raise `ValueError`, together with accompanying tests, cannot be verified from the provided evidence. The required artifacts are missing.
- **T047** — No execution logs, output files, or documentation of the run of `quickstart.md` in a fresh virtual environment are present. The required evidence that the pipeline completed end‑to‑end and produced the expected artifacts (e.g., downloaded genomes, preprocessed matrices, model files, performance reports) is missing, so the task is not satisfied.
