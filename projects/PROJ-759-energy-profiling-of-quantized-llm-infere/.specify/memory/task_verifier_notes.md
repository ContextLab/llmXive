# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required file `code/quickstart.md` is missing (only a root‑level `quickstart.md` exists) and the contract test `test_pyrapl_load` fails on the GitHub Actions runner, indicating that pyRAPL does not load successfully. Both the documentation artifact and the verification step are therefore not satisfied.
- **T002** — The required artifacts `data/raw/wikitext2.parquet` and `data/raw/README.md` are both MISSING — only the loader script `code/utils/data_loader.py` exists, and it was never executed to produce the dataset or checksum. There is also no test file or pytest run evidence for `test_wikitext2_download`, so the verification requirement is unmet.
- **T003** — Requested task execution failed; rerun successfully: code/utils/quantize.py exit=1
