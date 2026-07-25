# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T036** — The script does use `streaming=True` but lacks any fallback to `itertools.islice` with `SAMPLE_SIZE_FALLBACK` and does not log a warning when streaming fails. It also saves the fetched data to `data/raw/arc_bench.json` instead of processing it into `data/derived/parsed_traces.json`, and that target file is missing. Consequently the required behavior and output are not fulfilled.
