# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The task's verification requires `data/processed` to exist, but the collector reports `data/` as MISSING at the confirmed project root (while `src/` and `tests/` do exist there). The historical log shows directories created only under a `code/` subdirectory, so the data (and likely artifacts) directories are not present at the expected project-root location; the implementer should create `data/{raw,processed}` and `artifacts/{results,plots}` at the project root (or reconcile the path layout).
