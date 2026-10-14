# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The "downloaded" files are not GWTC posterior samples at all: the execution log shows Zenodo record 3966973 served a PNG ("xem video nào của kênh youtube...png") saved as `gwtc1.h5`, and record 3966974 served an `inscription_metadata_1804.json` (Sanskrit epigraphy metadata) saved as `gwtc2.h5` — the DOIs were unresolved claims pointing at unrelated records, and the code's fallback of "first file if no .h5" silently accepted wrong content. Additionally, `pytest tests/unit/test_download.py` FAILED (test_download_all, exit 1), and the "checksum verification" only hashes whatever was downloaded ra
- **T002** — Requested task execution failed; rerun successfully: src/data/preprocess.py exit=1
- **T003** — Requested task execution failed; rerun successfully: src/main.py exit=1
