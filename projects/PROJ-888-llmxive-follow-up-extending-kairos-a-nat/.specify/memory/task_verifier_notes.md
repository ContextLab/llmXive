# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/`, `code/`, `tests/`, `data/`, `state/`, `docs/` directories or the `state/directory_listing.txt` file is present. The implementer must create the specified directory hierarchy and generate a non‑empty `state/directory_listing.txt` via `tree -L 2`.
- **T001f** — No README.md file or its contents were provided; consequently there is no file existence check nor the first five lines of the document to verify. The required artifact is missing.
- **T004** — The required `code/config.py` file does not exist, so there is no configuration object defining seeds, paths, quantization levels, or noise std devs. Consequently `code/utils/validate_config.py` cannot import `QUANTIZATION_LEVELS` or `validate_config`, and the verification step cannot succeed. The missing config file must be added with the specified fields and include the required quantization levels [4, 6, 8, 16].
