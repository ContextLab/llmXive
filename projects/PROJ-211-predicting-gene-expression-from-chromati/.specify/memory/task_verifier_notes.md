# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The repository contains the `code/download_encode.py` script and the expected output files, but the script only writes synthetic placeholder data from fake URIs instead of streaming real ENCODE resources, and it does not abort on real HTTP errors. Moreover, the required integration test `tests/integration/test_download.py` is missing, so the verification step cannot be performed.
- **T003** — Requested task execution failed; rerun successfully: code/preprocess.py exit=1
