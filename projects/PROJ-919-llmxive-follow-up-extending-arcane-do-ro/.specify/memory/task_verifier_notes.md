# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The task requires creating `data/raw/`, `data/derived/`, and `artifacts/` directories, but the evidence shows `data/raw/` and `data/derived/` are MISSING and `artifacts/` is not listed at all. Additionally, no `.gitkeep` files are confirmed in any of the existing directories (src/, tests/, data/gold_standard/, specs/), which the task explicitly requires.
- **T003** — Requested task execution failed; rerun successfully: code/scripts/run_lint.py exit=1
- **T009a** — The file `data/gold_standard/human_annotations.json` exists and is non-empty, but its content is clearly fabricated placeholder data: generic archetypes ("Protagonist", "Foil", "Mentor", "Ally", "Antagonist"), four boilerplate scenario templates, and uniformly random-looking scores (0.19–4.89) with no connection to the ArcANE study's actual characters, psychological axes, or the T009c generation protocol. There is also no evidence of the required HuggingFace fetch attempt or of the T009a-gen fallback being invoked (no script, log, or provenance record). The next implementer should implement th
- **T009a-gen** — The required executable script `src/services/gold_standard_generator.py` does not exist, and the output file `data/gold_standard/human_annotations.json` contains fabricated random-looking data (generic "Protagonist/Foil/Mentor" characters, random ground_truth_scores, "Act 1/2/3" phases) rather than paragraphs from Pride and Prejudice (Gutenberg 1342) annotated with "Coarse"/"Fine" phase labels per the specified rule set. The implementer must write the actual generator using `datasets.load_dataset` for Gutenberg ID 1342, extract paragraphs at regular intervals, annotate with Coarse/Fine labels,
- **T009b** — The gold standard file `data/gold_standard/human_annotations.json` exists (3689 bytes, sha256 a58e22a0...), but there is no evidence that the checksum was recorded in `state/projects/PROJ-919-.../artifact_hashes` — no state file, hash entry, or update log was provided. The task's actual deliverable (the recorded hash in the state artifact_hashes) is missing; the next implementer should write the SHA256 of the file into the project's state artifact_hashes store.
- **T005** — declared artifact(s) missing/empty/invalid: src/lib/utils.py
- **T006** — declared artifact(s) missing/empty/invalid: src/lib/config.py
- **T007** — declared artifact(s) missing/empty/invalid: src/lib/validators.py
- **T008** — declared artifact(s) missing/empty/invalid: src/lib/state.py
- **T049** — declared artifact(s) missing/empty/invalid: src/lib/stream_loader.py, data/raw/arcane_corpus.jsonl
- **T015** — declared artifact(s) missing/empty/invalid: data/derived/axes.jsonl
- **T011b** — declared artifact(s) missing/empty/invalid: config/characters.json
- **T013** — declared artifact(s) missing/empty/invalid: config/characters.json, data/raw/arcane_corpus.jsonl
- **T027a** — declared artifact(s) missing/empty/invalid: config/sentiment_targets.json
- **T021** — declared artifact(s) missing/empty/invalid: data/derived/probes.jsonl
- **T028** — declared artifact(s) missing/empty/invalid: data/derived/results_raw.jsonl
- **T029a** — declared artifact(s) missing/empty/invalid: data/derived/calibration_metrics.json
- **T029c** — declared artifact(s) missing/empty/invalid: data/derived/judge_metrics.json
- **T030** — declared artifact(s) missing/empty/invalid: src/services/experiment_runner.py
- **T045** — declared artifact(s) missing/empty/invalid: scripts/check_cpu_feasibility.py
