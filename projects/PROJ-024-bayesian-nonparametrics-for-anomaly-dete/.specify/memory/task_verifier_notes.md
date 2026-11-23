# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The `validation_deferred.md` report is correctly generated and the script runs without error, but `search_datasets.py` only attempts downloads from NAB and PhysioNet and never queries the UCI repository as required by the task (“across UCI, NAB, and PhysioNet”). Consequently the search does not fully satisfy the specification.
- **T003** — Requested task execution failed; rerun successfully: code/src/data/download_datasets.py exit=1
