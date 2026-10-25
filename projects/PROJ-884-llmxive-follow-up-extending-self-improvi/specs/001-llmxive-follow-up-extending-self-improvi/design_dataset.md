# Dataset Strategy — Symbolic Backward-Step Substitution in Bidirectional Evolutionary Search

**Task**: T012 (Finalize Dataset Strategy)
**Spec**: `specs/001-llmxive-follow-up-extending-self-improvi/spec.md` (FR-001, SC-005)
**Status**: Finalized
**Date**: 2026-07-12

This document defines the generation methodology, complexity scaling, and provenance
metadata for the puzzle dataset used by the symbolic‑guided BES experiments. It is the
authoritative reference for `code/dataset/generator.py` and
`code/dataset/validate_distribution.py`.

---

## 1. Puzzle Types

The dataset is **programmatically generated** (synthetic curation with seeded,
deterministic generation) so that every instance ships with an exact ground‑truth
solution and a deterministic Python verifier. Four puzzle types are supported
(see `PuzzleType` in `code/dataset/generator.py`); the primary experimental set uses
the first two, per FR‑001:

| Type | Enum value | Description | Deterministic verifier |
|------|------------|-------------|------------------------|
| Sudoku variant | `sudoku` | Latin‑square grid with box constraints; grid size scales with N (minimum 9×9 for the primary set; 4×4 variants used in pilot/unit tests) | Row/column/box uniqueness check on the candidate grid |
| Constrained pathfinding | `pathfinding` | n × n grid with random obstacles; agent must find an obstacle‑free shortest path from start to end | BFS reference solve + adjacency/obstacle/path‑validity check |
| Logic grid | `logic_grid` | Einstein’s‑riddle‑style category assignment with clue constraints (exploratory; excluded from the primary symbolic run unless parseable) | Assignment‑uniqueness and clue‑satisfaction check |
| Arithmetic | `arithmetic` | Target‑value puzzles over N operands with +, –, *, / and parentheses | Exact evaluation of the expression against the target |

**Selection rationale**: Sudoku and pathfinding are the two families whose constraints map
cleanly onto the formal grammar consumed by the symbolic planner (`code/dataset/grammar.py`,
`code/symbolic/parser.py`). Logic‑grid and arithmetic instances are generated for
exploratory analysis; any instance whose constraints the parser cannot decompose is
excluded from the symbolic‑guided run and logged with reason `PARSE_FAILURE` or
`CONTRADICTION_DETECTED` to `data/processed/exclusions.json` (FR‑006) — never silently
dropped.

**Deterministic verification guarantee (Constitution Principle VI)**: solution validity is
decided ONLY by the external Python verifier in `code/dataset/verifier.py`, which returns
`(is_valid: bool, error_code: str)` and must execute in < 100 ms per solution. The verifier
is completely decoupled from the LLM and from the symbolic planner.

---

## 2. Generation Methodology

1. **Seeded construction**: a `random.Random(seed)` instance drives all generation; no
 global RNG state is touched. Each puzzle family has a dedicated construction routine
 (e.g., backtracking fill for Sudoku, random obstacle placement + BFS feasibility check
 for pathfinding).
2. **Ground truth by construction**: each generator produces the puzzle *from* a known
 solution (e.g., a completed Sudoku grid with cells removed; a BFS‑solved path), so every
 instance has an exact reference solution stored in `solution`.
3. **Feasibility enforcement**: generation retries up to `--max-attempts` (default 1000) to
 obtain a feasible instance (e.g., pathfinding grids must admit a path from start to
 end); exhaustion raises `DataGenerationError` — no silent fallback, no placeholder
 instances.
4. **Schema validation**: every generated instance must conform to
 `contracts/dataset.schema.yaml`; distribution‑level validation is performed by
 `code/dataset/validate_distribution.py`, which writes
 `data/processed/distribution_report.json` and
 `data/processed/distribution_validation.json`.
5. **Difficulty knobs**: per‑type difficulty (`easy` / `medium` / `hard`) controls the
 number of removed Sudoku cells, obstacle density, clue count, and operand count.

---

## 3. Scaling Plan

Complexity is parameterized by a single integer **N** per instance, recorded in
`metadata.complexity_n`, plus a composite `metadata.complexity_metric`
(`constraint_count`, `variable_domain_size`):

| Puzzle type | Meaning of N | Variable domain size |
|-------------|--------------|----------------------|
| `sudoku` | Grid side length (≥ 9 in the primary set) | N |
| `pathfinding` | Grid side length | N² |
| `logic_grid` | Items per category | N^(#categories) |
| `arithmetic` | Number of operands | ~100 (operand range) |

**Dataset scales (T004 deliverables)**:

- `data/raw/puzzles_N10.json` — pilot scale (N=10), used for the end‑to‑end pilot run and
 runtime/memory profiling.
- `data/raw/puzzles_N100.json` — mid scale (N=100).
- `data/raw/puzzles_N500.json` — full scale (N=500), the primary experimental set.

The scaling subset (multiple N values per type, e.g. `--n 10 100 500`) feeds the empirical
complexity analysis (SC‑005): log‑log regression of solver runtime against N via
`code/analysis/scalability_analyzer.py` / `code/analysis/scaling.py`, producing
`data/processed/scaling_raw_logs.json` and derived complexity reports. The expected
theoretical reference classes are O(N²) for the Sudoku verifier (cell‑scan with
row/column/box checks) and O(N²) for BFS pathfinding on an N × N grid; empirical slopes
are compared against these (contracts: `contracts/complexity_report.schema.yaml`,
`contracts/sc005_validation.schema.yaml`).

Sample‑size rationale: the full set (500 instances per condition) exceeds the requirement
derived from the pre‑registered power analysis in
`specs/001-llmxive-follow-up-extending-self-improvi/stat_analysis_plan.md` (two‑proportion z‑test at α = 0.05,
power ≥ 0.80 for the equivalence margin Δ = 0.05).

---

## 4. Seed Management

- **Master seed**: 42 (default `--seed` in `code/dataset/generator.py`; also the default in
 `code/main.py` and `PYTHONHASHSEED` in the run‑book).
- **Per‑run derivation**: the BES loop derives per‑generation seeds as
 `master_seed + generation` (see `set_seed` in `code/utils/seed.py` and
 `Population.initialize_random`), so evolutionary runs are reproducible from the master
 seed alone.
- **Per‑instance provenance**: every puzzle records `metadata.generation_seed` (the master
 seed of its generating run), so any single instance can be regenerated in isolation.
- **RNG isolation**: all generation uses a local `random.Random(seed)` instance; no
 `random.*` module‑level calls participate in dataset construction, guaranteeing that
 regenerating one scale does not perturb another.
- **Reproducibility check**: re‑running the generator with identical `--seed`, `--n`,
 `--count`, `--types`, and `--source-id` must produce byte‑identical puzzle content
 (timestamps in the header/metadata are the only non‑deterministic fields and are
 recorded for provenance, not for content).

---

## 5. Provenance Metadata

Every puzzle instance carries a `metadata` block (implemented in
`PuzzleGenerator._generate_metadata`):

- `source_id` — identifier of the generation source (default `curated_logic_v1`).
- `generation_seed` — master seed of the generating run.
- `timestamp` — ISO‑8601 UTC generation time.
- `generator_version` — generator version string (currently `1.0.0`).
- `complexity_metric` — `{constraint_count, variable_domain_size}`.
- `puzzle_type` — enum value of the type.
- `complexity_n` — the N parameter of the instance.

The output file additionally carries a `header` block with `source_id`, `generation_seed`,
`timestamp`, `generator_version`, `total_instances`, `n_values`, `puzzle_types`, and
`count_per_type`. Raw files under `data/raw/` are immutable after generation (Data
Hygiene, Principle III); all derived artifacts are written under `data/processed/`.

---

## 6. Exclusions and Failure Handling

Per FR‑006 and the spec's edge cases:

- Unparseable constraints → instance excluded from the symbolic‑guided run, logged with
 `PARSE_FAILURE`.
- Contradictory sub‑goals from the planner → `CONTRADICTION_DETECTED`, instance flagged
 for review/exclusion.
- All exclusions are recorded in `data/processed/exclusions.json` by
 `code/symbolic/exclusion_logger.py` (single writer per run); the exclusion rate is
 reported as `logical_contradiction_rate` in the statistical results.

**Generation failures** (infeasible instances after `--max-attempts`, schema violations) raise
`DataGenerationError` and abort the run — there is no synthetic or placeholder fallback
anywhere in the pipeline.