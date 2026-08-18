# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015b** — The provided `code/data/generator.py` exists but the visible portion does not contain a CLI entry point or code that actually writes the generated data to `data/raw/golden_fixture.json`; the file `data/raw/golden_fixture.json` is also missing. Consequently the script does not demonstrably fulfill the requirement to generate and save the fixture.
- **T015c** — The required artifact `data/raw/golden_fixture.json` is missing from the repository, so the file does not exist, cannot be non‑empty, and cannot be verified for correct contents or checksum. The implementer must run `python code/data/generator.py` (or otherwise generate) to create the JSON file at the specified path.
- **T015d** — declared artifact(s) missing/empty/invalid: data/raw/golden_fixture.json
- **T010** — The required input file `data/raw/golden_fixture.json` is missing, so the parser cannot be exercised, and the provided `parser.py` is truncated and does not return or write the parsed trace objects. Both the necessary data and a complete implementation are absent.
