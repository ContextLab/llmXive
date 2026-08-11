# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005a** — The repository lacks the required `data/derived/synthetic_queries_warmup.json` file (it is missing), and the shown `code/data/generator.py` does not contain any implementation that creates a 100‑query warm‑up set. Consequently the deliverable specified in the task is not present.
- **T010** — No `state/manifest.json` file or `state/hashes/` directory was provided, and there is no evidence that SHA‑256 hashes for files in `data/` and `code/` were computed. The required artifact is missing, so the task is not satisfied.
- **T011** — No evidence of the required `data/raw/` and `data/derived/` directories was provided, nor any implementation of checksumming hooks (e.g., scripts or configuration that compute and verify file checksums). The claim lacks the actual artifacts needed to satisfy the task.
- **T016** — The repository lacks the required `data/derived/synthetic_queries_warmup.json` file, and the provided `code/cache/semantic_cache.py` snippet shows only cache class definitions (get/set) with no implementation of a warm‑up phase that reads that JSON and populates the cache. Both the data file and the corresponding population logic are missing.
