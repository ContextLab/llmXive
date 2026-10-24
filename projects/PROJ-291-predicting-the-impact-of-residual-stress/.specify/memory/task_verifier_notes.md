# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided `env_check.py` does not import the full required stack (missing `psutil`, `openml`, `ucimlrepo` and treats `torch` as optional), and `config.py` lacks the explicit constants `K_STEEL`, `K_ALUMINUM`, `PSI_TO_MPA` and any path definitions. Consequently the test suite cannot correctly import `src.env_check` nor verify the required configuration. The task needs the missing imports added and the configuration file updated with the specified constants.
