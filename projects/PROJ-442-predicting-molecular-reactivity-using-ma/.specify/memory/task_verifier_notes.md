# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013b** — The `src/utils/chemistry.py` file is only partially shown and ends abruptly inside `_match_reaction`; no complete reaction‑matching or classification function is present. Moreover, the required `config.yaml` containing the SMARTS patterns is missing, so the code cannot load the templates it is supposed to use. Both the essential artifact and its functionality are absent.
- **T012** — The provided `src/modeling/config.yaml` does not define a `USPTO_URL` key, violating the required configuration check. Additionally, the expected output file `data/raw/uspto_subset.parquet` is missing, indicating the ingestion script has not completed the download, checksum verification, and parsing steps.
