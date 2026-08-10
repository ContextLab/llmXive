# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T051** — The provided `code/data/external.py` is truncated before the GitHub/NPM request logic, so we cannot verify that the functions actually use the cache or respect the 24‑hour TTL. Additionally, the required cache file `data/cache/github_api_cache.json` does not exist on disk. The implementation must be shown in full and demonstrate writing/reading the cache file to satisfy the task.
- **T053** — The provided `clustering.py` defines a logging helper but never calls it, and the required log file `data/processed/clustering_warnings.log` does not exist. Consequently the fallback‑skip‑and‑log behavior for Levenshtein distances > 2 is not demonstrated. The task remains unfinished.
