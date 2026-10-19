# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T102** — Requested task execution failed; rerun successfully: code/analysis/explainability.py exit=1
- **T103** — The required output `data/derived/deviation_contexts.csv` is MISSING (as is `data/derived/test_set.csv`), so there is no evidence the `--map-bits` command was ever run or that the unit test passed. Additionally, the implementation's mapping logic is substantively wrong: it builds `rule_lookup = {idx: rules[idx] ...}` positionally, so only the first 5 bit indices get a SMARTS rule and all higher bits are labeled `uninterpretable` regardless of whether they are MACCS or hashed ECFP4/FP2 bits — it never actually matches each top-K bit's SMARTS against molecules via `GetSubstructMatches` or resolv
- **T104** — Requested task execution failed; rerun successfully: code/analysis/explainability.py exit=1
