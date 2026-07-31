# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015b** — The repository contains a non‑empty `code/data/generator.py` that imports `generator_logic.py` and defines a `generate_golden_fixture` function using seeds 42+i, but the provided excerpt does not show a CLI entry point that writes to `data/raw/golden_fixture.json`, nor is the required `golden_fixture.json` file present. Without evidence that the script actually creates the JSON at the specified location, the task’s output requirement is not satisfied.
- **T015c** — The required artifact `data/raw/golden_fixture.json` does not exist on disk, so the generation step and verification (existence, non‑empty content, correct `ground_truth_label` enums) have not been fulfilled. The implementer must run `code/data/generator.py` to create the file and ensure it is present and valid.
- **T015d** — declared artifact(s) missing/empty/invalid: data/raw/golden_fixture.json
- **T010** — The required input file `data/raw/golden_fixture.json` is missing, so the parser cannot be exercised, and the provided `parser.py` is truncated and does not return or write the parsed trace objects. Both the necessary data and a complete implementation are absent.
