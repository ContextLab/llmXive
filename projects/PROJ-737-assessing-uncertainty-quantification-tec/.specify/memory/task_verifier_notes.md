# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `code/download.py` script and its tests run successfully and produce the required files, metadata, and checksum manifest, but the downloaded CSVs are placeholder datasets (iris, tips, planets) rather than the three real materials datasets specified in the task (Band Gap, Formation Energy, Thermal Conductivity). The `source_url` fields in the metadata point to these placeholder URLs, violating the core requirement to fetch the actual materials property CSVs. The task must be fixed by using the correct URLs (or equivalent real materials datasets) and updating the metadata accordingly.
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=1
