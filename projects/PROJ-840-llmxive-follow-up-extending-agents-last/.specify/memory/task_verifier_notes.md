# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015d** — declared artifact(s) missing/empty/invalid: data/raw/golden_fixture.json
- **T015b** — The repository contains `code/data/generator.py`, but the required output file `data/raw/golden_fixture.json` is absent, and the provided snippet does not show a CLI entry point that writes the JSON to that path. The task’s core deliverable – a script that generates and saves the 10 scenario traces to `data/raw/golden_fixture.json` – is therefore not satisfied.
- **T015c** — The required artifact `data/raw/golden_fixture.json` is absent; without the file the existence, non‑emptiness, label distribution, and checksum checks cannot be performed. The implementer must run `code/data/generator.py` to create the JSON file in the specified location.
