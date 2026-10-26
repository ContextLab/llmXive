# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — The repository contains `data/input/urls.csv`, `data/raw/` (≈300 files) and `data/checksums.txt`, but there is no concrete evidence that the CSV actually holds ≥ 300 rows, that every URL has a matching raw HTML file, or that each download succeeded with HTTP 200 and returned HTML (no logs or status checks are provided). Moreover, the URLs are generic Unbounce blog pages rather than verified “public A/B‑test summaries,” and no sample of the fetched HTML is shown to confirm they are indeed such summaries. To satisfy the task, the implementer must supply: (1) a definitive row count for `urls.csv`
- **T004** — Requested task execution failed; rerun successfully: code/src/audit/monte_carlo_validation.py exit=1
