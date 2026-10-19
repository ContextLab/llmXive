# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — the task writes platform-owned path(s) inside the project: `.github/workflows/research.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T006** — The evidence contains `data/manifest.json`, `code/data_gap_resolver.py`, `code/config.py`, and `code/download.py`, but no `Snakefile` at all — the core deliverable of T006 is absent. Consequently there is no `verify_data_availability` rule, no `download: verify_data_availability` dependency, no `data_gap_resolver` Snakemake rule, and no evidence that `snakemake -n verify_data_availability` prints "All datasets unavailable – aborting." (the manifest shows all three datasets Unavailable, so this abort path is exactly what should be demonstrable). The implementer must create the Snakefile with th
- **T007** — Requested task execution failed; rerun successfully: code/data_gap_resolver.py exit=1
- **T008** — Requested task execution failed; rerun successfully: code/preprocess_and_geometry.py exit=1
