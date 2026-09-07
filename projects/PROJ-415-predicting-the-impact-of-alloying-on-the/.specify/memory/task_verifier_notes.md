# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T068** — The `code/models/training.py` contains a `verify_data_provenance` function, but it checks a separate `data_provenance.json` rather than directly confirming that `data/curated/filtered.csv` is non‑synthetic, and the required `data/curated/filtered.csv` file is absent from the repository. Both the missing input file and the mismatched verification logic mean the task’s requirement is not satisfied.
- **T071** — The `code/data/acquisition.py` file contains only a partially shown `validate_provenance_source_type()` stub that does not demonstrate the required check, and the required `data/curated/data_provenance.json` file is missing entirely, so the validation cannot be performed. The task’s core requirement is not met.
