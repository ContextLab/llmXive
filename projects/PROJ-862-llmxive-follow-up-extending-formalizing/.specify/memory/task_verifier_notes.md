# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No evidence was provided that a `tests/` directory or a non‑empty `tests/__init__.py` file actually exists in the repository; the claim cannot be verified. The required directory and file need to be added and shown.
- **T004** — The provided `code/requirements.txt` exists but uses “>=” version specifiers instead of exact pinned versions (e.g., `transformers==4.35.0`) and includes many extra dependencies not requested. To satisfy the task it must list only the eight specified packages with exact version numbers.
- **T006** — The required file `code/data_loader.py` does not exist, so no implementation, dataset fetching, column check, or error handling is present. The task cannot be considered fulfilled.
