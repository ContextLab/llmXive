# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T102** — Both required files exist and `link_dataframe` implements the pre-existing-ID, fuzzy, and embedding branches, but there is no execution evidence that `pytest tests/unit/test_entity_linker.py` was run and passed (the task's explicit verification criterion). Moreover, the embedding-path test is broken as written: it monkeypatches `utils.entity_linker.SentenceTransformer`, but the module imports `SentenceTransformer` inside `link_dataframe` via a function-local `from sentence_transformers import SentenceTransformer`, so the patch never takes effect and the test runs against the real model with a
- **T103** — Requested task execution failed; rerun successfully: code/ingest/download_data.py exit=1
