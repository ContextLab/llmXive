# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004c** — The `code/config.py` file only defines dataclasses and does not contain any logic to read, generate, or validate `data/processed/config.yaml`. Moreover, the required `data/processed/config.yaml` file is absent, so the generator/loader behavior described in the task is not implemented. The next implementer must add code that (a) checks for the file, (b) creates it with the required schema and defaults when missing, (c) loads its values into the `Config` class, and (d) raises `ValueError` on malformed content.
