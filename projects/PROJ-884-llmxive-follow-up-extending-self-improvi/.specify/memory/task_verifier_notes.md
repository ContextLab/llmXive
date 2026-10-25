# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T016** — Requested task execution failed; rerun successfully: code/main.py exit=2
- **T001** — The pytest collection for `test_generator.py` fails with a `JSONDecodeError` because `contracts/dataset.schema.yaml` is a YAML file but the test loads it with `json.load`. Consequently the generator’s output is never validated against the schema. Moreover, `PuzzleGenerator.generate_puzzles` writes a single JSON object (with a “header” and a “puzzles” list) instead of the required JSON‑Lines (JSONL) format. Both issues prevent the required tests from passing and mean the generator does not emit records that conform to the contract. The verifier itself logs timings and returns the correct tuple,
