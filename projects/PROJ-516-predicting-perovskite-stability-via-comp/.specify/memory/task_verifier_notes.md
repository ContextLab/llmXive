# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — The `data_fetcher.py` implementation is present and reads a `delay_multiplier` from a `retry` section in `config.yaml`, but the required `config.yaml` file does not exist in the repository, so the configurable retry logic cannot be verified. Add a `config.yaml` containing at least `retry: { delay_multiplier: <value>, max_attempts: 3, base_delay_seconds: 1.0, max_delay_seconds: 60.0 }`.
- **T012b** — declared artifact(s) missing/empty/invalid: data/raw/mp_perovskites.csv
