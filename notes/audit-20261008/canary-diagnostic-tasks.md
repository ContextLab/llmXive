---
description: "Task list for Finite-range residue imbalance of Euler's totient"
---

# Tasks: Finite-range residue imbalance of Euler's totient

**Input**: Design documents from `/specs/001-totient-canary/`
**Prerequisites**: `plan.md`, `spec.md`
**Tests**: Test module `code/test_totient.py` required per FR‑010.

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 [P] Create full project directory hierarchy
  `projects/PROJ-9999-totient-canary/{code,data,paper,paper/figures,contracts,state}`
  and write an empty `README.md` at the repo root.
- [ ] T002 [P] Write `code/requirements.txt` with pinned dependencies:
  `numpy==2.1.*`, `matplotlib==3.9.*`, `pytest`, `pandas`, `PyYAML`.
- [ ] T003 [P] Write contract schemas `contracts/tv-summary.schema.yaml` and `contracts/residue-counts.schema.yaml` defining required fields and enforcing per‑modulus array‑length constraints for `p ∈ {5,7,11}`.
- [ ] T004 [P] Write `code/setup_runner.sh`: a fail‑loudly script that installs `pandoc` (pinned) and a minimal LaTeX backend, verifies their availability, and aborts with a clear error if checks fail (Constitution I).

## Phase 2: Foundational (Blocking Prerequisites)

*No foundational code is required for this pure‑computational study, but the setup tasks above must be completed before any user‑story work.*

## Phase 3: User Story 1 – Exact totient census and residue counts (Priority: P1) 🎯 MVP

**Goal**: Compute exact φ(n) for 1 ≤ n ≤ 10⁶, validate against a gcd‑based method, and produce unconditional & conditional residue counts for each (N, p).

- [ ] T005 [US1] Implement exact totient sieve in `code/totient_analysis.py` (φ(1)=1, integer arithmetic, CPU‑only, range up to 10⁶).
- [ ] T006 [US1] Implement residue census in `code/totient_analysis.py` for `p ∈ {5,7,11}` and `N ∈ {10³,10⁴,10⁵,10⁶}`: per‑class counts, zero‑residue mass, unconditional denominator N, conditional denominator (N − zero‑mass).
- [ ] T007 [US1] Add sieve‑validation tests to `code/test_totient.py`: for all n ≤ 1000 recompute φ(n) via `math.gcd` and assert exact agreement; also assert φ(1)=1.
- [ ] T008 [US1] Add count‑conservation tests to `code/test_totient.py`: verify unconditional counts sum to N and conditional counts sum to the conditional denominator for all 12 (N, p) combos, plus a hand‑recomputed check for (N=10³, p=5).

## Phase 4: User Story 2 – TV distances, exports, and schema validation (Priority: P2)

**Goal**: Compute total‑variation distances for both populations, export all results, and validate file formats.

- [ ] T009 [US2] Implement TV computation in `code/totient_analysis.py` per FR‑004 (unconditional TV uses k = p, conditional TV uses k = p‑1, denominators reported explicitly).
- [ ] T010 [US2] Add TV‑verification tests to `code/test_totient.py`: hand‑recompute TV for (N=10³, p=5) for both populations and assert equality with pipeline output.
- [ ] T011 [US2] Export the following artifacts in the `data/` directory:
  `residue_counts.csv`, `residue_counts.json`, `tv_summary.csv`.
  Each file must contain per‑class counts, zero‑residue mass, unconditional denominator, conditional denominator, and both TV values for every (N, p).
- [ ] T012 [US2] Write `code/validate_schemas.py` that loads the two contract YAML files and validates `data/tv_summary.csv` and `data/residue_counts.json`; exit non‑zero on any violation.
- [ ] T013 [US2] Compute SHA‑256 hashes for all generated data artifacts (`residue_counts.csv`, `residue_counts.json`, `tv_summary.csv`) and record them under an `artifact_hashes` map in `state/projects/PROJ-9999-totient-canary.yaml`.

## Phase 5: User Story 3 – Trend analysis, figure, and paper (Priority: P3)

**Goal**: Summarise TV trends, flag reversals, produce a figure, and generate a ≤ 6‑page methods/results paper.

- [ ] T014 [US3] Export compact `data/results_table.csv` (one row per (N, p) with unconditional TV, conditional TV, and both denominators) by reading `data/tv_summary.csv`. Record its hash in the state YAML (via T013).
- [ ] T015 [US3] Detect every (N, p) where conditional TV increases relative to the next‑smaller N; export `data/reversals.json` listing the (N, p) location and the two TV values; record its hash.
- [ ] T016 [US3] Plot conditional and unconditional TV vs. N (log‑scale x‑axis) for each p ∈ {5,7,11} and save to `paper/figures/tv_vs_N.png`; record its hash.
- [ ] T017 [US3] Generate `paper/paper.md` (≤ 4000 words / ≤ 6 pages) with numbers programmatically injected from `data/tv_summary.csv` and `data/results_table.csv`. The paper must:
  1. Cite verbatim the reference: Lebowitz‑Lockard, Pollack and Singha Roy (2021), “Distribution mod p of Euler's totient and the sum of proper divisors”, arXiv:2105.12850, https://arxiv.org/abs/2105.12850.
  2. Reproduce the theorem’s coprimality assumption **character‑for‑character** from the idea document.
  3. Distinguish the conditional asymptotic result from the finite‑range unconditional measurements.
  4. Explicitly disclaimer that finite computation cannot prove asymptotic convergence.
  5. List every reversal from `data/reversals.json`.
  After generation, invoke the word‑/page‑count checker (T018) and record the hash.
- [ ] T018 [US3] Write `code/check_paper_limits.py` that parses `paper/paper.md` to count words and uses `pdfinfo` on `paper/paper.pdf` to count pages; exit non‑zero if limits are exceeded.
- [ ] T019 [US3] Build `paper/paper.pdf` from `paper/paper.md` using `pandoc` with the minimal LaTeX backend provisioned by T004.
- [ ] T020 [US3] Write `code/verify_pdf.py` that confirms the PDF exists, its hash matches the entry recorded by T013/T017, and that the limits were respected (calls T018 internally).

## Phase 6: Polish & Gates

- [ ] T021 [P] Create GitHub Actions workflow `.github/workflows/totient-pipeline.yml` that runs on `ubuntu-latest` (2‑core CPU‑only runner, ≤ 7 GB RAM). Steps:
  1. Run `code/setup_runner.sh`.
  2. Execute `python code/totient_analysis.py --all`.
  3. Measure runtime (`time`) and peak memory (`resource.getrusage(RUSAGE_SELF).ru_maxrss`).
  4. Fail if runtime > 5 min or memory > 2 GB.
  5. Record measured runtime and peak memory in `state/projects/PROJ-9999-totient-canary.yaml`.
- [ ] T022 [P] Scope‑compliance review script `code/scope_review.py` that:
  * Scans the `code/` directory for any imports or functions related to chi‑square, KS, p‑value, bootstrap, or other statistical‑significance utilities (fails if found).
  * Confirms the deliverable consists of a single analysis script plus one test module (FR‑010).
  * Generates a coverage checklist mapping each FR‑001…FR‑011 and SC‑001…SC‑005 to the implementing task ID; stores this checklist under `fr_sc_coverage` in `state/projects/PROJ-9999-totient-canary.yaml`.
- [ ] T023 [P] Integrate `code/scope_review.py` into the CI workflow (T021) so the pipeline aborts on prohibited code.

## Dependencies & Execution Order

- **Setup**: T001 → T002 → T003 → T004
- **User Story 1**: T005 → T006 → T007 → T008
- **User Story 2**: T009 → T010 → T011 → T012 → T013
- **User Story 3**: T014 → T015 → T016 → T017 → T018 → T019 → T020
- **Polish & Gates**: T021 → T022 → T023

Parallelism is allowed among tasks marked `[P]` when file‑level independence permits, but all data‑flow dependencies are respected.

---
