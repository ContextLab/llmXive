# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The downloaded files are not GWTC posterior samples: `data/raw/gwtc1.h5` begins with a PNG header (an image, ~1 MB) and `data/raw/gwtc2.h5` is a JSON record about a copper-plate inscription from a completely different Zenodo record — neither is HDF5 GWTC data, so the "real run" produced fabricated/wrong artifacts. Additionally, the verification requirement fails: the recorded pytest run of `tests/unit/test_download.py` exited with code 2 (`ModuleNotFoundError: No module named 'requests_mock'`), so the tests do not pass, and the download code never verifies checksums against Zenodo-provided exp
- **T002** — Requested task execution failed; rerun successfully: src/data/preprocess.py exit=1
- **T003** — Requested task execution failed; rerun successfully: src/main.py exit=1
