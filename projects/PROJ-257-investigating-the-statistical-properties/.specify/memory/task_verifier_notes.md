# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The downloaded files are not GWTC posterior samples: the execution log shows DOI 10.5281/zenodo.3966973 yielded a PNG image ("xem video nào của kênh youtube...png") and 10.5281/zenodo.3966974 yielded an "inscription_metadata_1804.json" about a copper-plate charter — both saved under the misleading names gwtc1.h5/gwtc2.h5, so the "real data" requirement is not met (the DOIs themselves are unresolved/wrong). Additionally, `pytest tests/unit/test_download.py` failed with exit 2 (ModuleNotFoundError: requests_mock), so the stated verification criterion does not pass.
- **T002** — Requested task execution failed; rerun successfully: src/data/preprocess.py exit=1
