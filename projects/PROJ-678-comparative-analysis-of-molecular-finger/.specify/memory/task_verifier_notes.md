# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The collector reports that `projects/PROJ-678-comparative-analysis-of-molecular-fingerprints/` does not exist, and the only evidence of directory creation is a log that mentions a similarly‑named path ending in “…-finger” (missing the “prints” suffix). No actual directory tree with `data/raw`, `data/processed`, `code`, and `tests` is present under the required project path. The task’s core artifact – the project directory structure – is therefore missing.
- **T010** — The provided `tests/integration/test_download.py` defines `test_download_and_checksum_tox21` and does download the Tox21 dataset and compute an MD5 checksum, but it never asserts that the computed checksum matches a known reference value. Without a comparison to an expected hash, the test does not truly validate the checksum, so the integration‑test requirement is not fully met.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/filter_log.txt
- **T018c3** — Requested task execution failed; rerun successfully: code/split.py exit=1
- **T029a2** — declared artifact(s) missing/empty/invalid: data/processed/test_set_descriptive.json
- **T029a3** — declared artifact(s) missing/empty/invalid: data/processed/research_results.md
- **T034** — Requested task execution failed; rerun successfully: code/quickstart_validation.py exit=1
