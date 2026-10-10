# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The project lacks the required `specs/001-visual-distraction-cognitive-control/` directory, the `code/requirements.txt` does not pin versions and omits `requests` and `openml` (and adds an unrelated `pyyaml`). The utility module’s API does not match the specification (functions are named `compute_file_checksum`, `set_random_seed`, `sanitize_image_pii`, `log_structured_error` instead of `compute_checksum`, `set_global_seed`, `sanitize_images`, `log_error`). Consequently the claimed verification steps cannot be confirmed.
