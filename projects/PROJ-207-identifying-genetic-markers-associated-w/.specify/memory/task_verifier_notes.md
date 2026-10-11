# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `requirements.txt` file exists and lists all required packages, but only `biopython` and `samtools` are version‑pinned; the other required packages (plink2, freebayes, bwa, scikit‑learn, pandas, numpy, statsmodels, pyyaml, requests) lack explicit version specifications, violating the “pinned” requirement. Additionally, an unrelated package (`dwgsim`) is included, which is not part of the requested stack. The implementer must pin every listed package to a specific version (e.g., `plink2==X.Y.Z`) and may remove unnecessary extras.
- **T003** — Requested task execution failed; rerun successfully: code/01_download_metadata.py exit=1
