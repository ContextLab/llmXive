# Dataset Strategy — Symbolic Backward‑Step Substitution in Bidirectional Evolutionary Search

**Task**: T012 (Finalize Dataset Strategy)
**Spec**: `specs/001-llmxive-follow-up-extending-self-improvi/spec.md` (FR‑001, SC‑005)
**Status**: Finalized
**Date**: 2026‑07‑12

This document defines the generation methodology, complexity scaling, and provenance
metadata for the puzzle dataset used by the symbolic‑guided BES experiments. It is the
authoritative reference for `code/dataset/generator.py` and related validation scripts.

---

## Puzzle Types

The dataset is **programmatically generated** (synthetic curation with seeded,
deterministic generation) so that every instance ships with an exact ground‑truth
solution and a deterministic Python verifier. Four puzzle types are supported; the
primary experimental set uses the first two, per FR‑001:

| Type | Enum value | Description | Deterministic verifier |
|---------------------|------------|-----------------------------------------------------------------------------|-----------------------------------------------------------|
| Sudoku variant | `sudoku` | Latin‑square grid with box constraints; grid size scales with **N** (minimum 9×9 for the primary set; 4×4 variants used in pilot/unit tests) | Row/column/box uniqueness check on the candidate grid |
| Constrained pathfinding | `pathfinding` | *n* × *n* grid with random obstacles; agent must find an obstacle‑free shortest path from start to end | BFS reference solve + adjacency/obstacle/path‑validity check |
| Logic grid | `logic_grid` | Einstein‑riddle‑style category assignment with clue constraints (exploratory; excluded from the primary symbolic run unless parseable) | Assignment‑uniqueness and clue‑satisfaction check |
| Arithmetic | `arithmetic` | Target‑value puzzles over *N* operands with `+`, `‑`, `*`, `/` and parentheses | Exact evaluation of the expression against the target |

**Selection rationale**: Sudoku and pathfinding constraints map cleanly onto the formal grammar consumed by the symbolic planner
(`code/dataset/grammar.py`, `code/symbolic/parser.py`). Instances whose constraints cannot be parsed are excluded from the symbolic‑guided run and logged with reason `PARSE_FAILURE` or `CONTRADICTION_DETECTED` in `data/processed/exclusions.json` (FR‑006). [UNRESOLVED-CLAIM: c_4cd6f003 — status=not_enough_info]

---

## Scaling Plan

Complexity is parameterized by a single integer **N** per instance, recorded in
`metadata.complexity_n`, plus a composite `metadata.complexity_metric`
(`constraint_count`, `variable_domain_size`):

| Puzzle type | Meaning of **N** | Variable domain size |
|-------------|--------------------------------------|----------------------|
| `sudoku` | Grid side length (≥ 9 in the primary set) | **N** |
| `pathfinding` | Grid side length | **N²** |
| `logic_grid` | Items per category | **N**^(#categories) |
| `arithmetic` | Number of operands | ≈ 100 (operand range) |

**Dataset scales** (delivered by Task T004):

- `data/raw/puzzles_N10.json` — pilot scale (N = 10), used for profiling and pilot runs. [UNRESOLVED-CLAIM: c_ede11336 — status=not_enough_info]
- `data/raw/puzzles_N100.json` — mid scale (N = 100). [UNRESOLVED-CLAIM: c_e1ae0b09 — status=not_enough_info]
- `data/raw/puzzles_N500.json` — full scale (N = 500), the primary experimental set. [UNRESOLVED-CLAIM: c_1fc6ea36 — status=not_enough_info]

The scaling subset feeds the empirical complexity analysis (SC‑005) via
`code/analysis/scalability_analyzer.py`, producing `data/processed/scaling_raw_logs.json`
and derived reports. Expected theoretical classes are **O(N²)** for both Sudoku
verification (cell‑scan) and BFS pathfinding; empirical slopes are compared against these
(schemas: `contracts/complexity_report.schema.yaml`, `contracts/sc005_validation.schema.yaml`).

---

## Seed Management

- **Master seed**: `42` (default `--seed` in `code/dataset/generator.py`; also the default in `code/main.py` and `PYTHONHASHSEED` in the run‑book).
- **Per‑run derivation**: the BES loop derives per‑generation seeds as `master_seed + generation` (see `code/utils/seed.py`). This guarantees reproducibility of evolutionary runs from a single master seed.
- **Per‑instance provenance**: every puzzle records `metadata.generation_seed` (the master seed of its generating run) so any single instance can be regenerated in isolation.
- **RNG isolation**: all generation uses a local `random.Random(seed)` instance; no module‑level `random.*` calls participate, ensuring that regenerating one scale does not perturb another.
- **Reproducibility check**: re‑running the generator with identical `--seed`, `--n`, `--count`, `--types`, and `--source-id` must produce byte‑identical puzzle content (timestamps are the only non‑deterministic fields and are recorded for provenance only).

---

## Provenance Metadata

Every puzzle instance carries a `metadata` block:

- `source_id` — identifier of the generation source (default `curated_logic_v1`).
- `generation_seed` — master seed of the generating run.
- `timestamp` — ISO‑8601 UTC generation time.
- `generator_version` — generator version string (currently `1.0.0`).
- `complexity_metric` — `{constraint_count, variable_domain_size}`.
- `puzzle_type` — enum value of the type.
- `complexity_n` — the **N** parameter of the instance.

The top‑level file also includes a `header` block with overall statistics
(`source_id`, `generation_seed`, `timestamp`, `generator_version`,
`total_instances`, `n_values`, `puzzle_types`, `count_per_type`). Raw files under `data/raw/` are immutable after generation; all derived artifacts are written under `data/processed/`.