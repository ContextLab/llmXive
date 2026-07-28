# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T004** — The provided `code/data/loader.py` only parses arguments and calls external `data_fetcher` functions; it does not itself enforce the required URL, cache fallback, column checks, or abort‑and‑log behavior. Moreover, the expected cache file `data/raw/cache/GSS2018.dta` and the output CSV `data/raw/gss_2018_subset.csv` are absent, and the manifest still shows a pending status. The task’s core requirements are therefore not satisfied.
- **T004b** — The required `data/raw/gss_2018_subset.csv` file is absent, and the manifest still marks the artifact as “pending” with no checksum. Consequently the fetcher was not executed, no data was saved, and no SHA‑256 hash was recorded, so the task’s requirements are not met.
- **T005** — The repository contains a `code/data/synthetic.py` module, but it never writes the required CSV or JSON files (no code invoking `to_csv` or `json.dump` is present), and the expected schema file `contracts/dataset.schema.yaml` is absent. Consequently the required output artifacts `data/processed/synthetic_mar_v1.csv`, `data/processed/synthetic_mar_v1_meta.json`, and the schema are missing.
