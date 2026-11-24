# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — Requested task execution failed; rerun successfully: code/run_lint.py exit=1
- **T009** — The `download_datasets()` function is present, but it obtains URLs from `config.get_dataset_urls()` rather than from the `research.md#verified-datasets` section as required, and the `research.md` file does not contain any actual verified URLs (the table’s URL cells are empty). Consequently, the function will raise a `ValueError` for missing URLs and never performs a real `wget` download. The task’s core requirement—fetching the TMDB 5000 and IMDb Reviews datasets from verified public URLs using `wget`—is therefore not satisfied.
