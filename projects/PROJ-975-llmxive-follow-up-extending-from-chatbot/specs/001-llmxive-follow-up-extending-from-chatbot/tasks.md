# Tasks: How does the semantic overlap and cardinality of a persistent skill library influence retrieval fidelity and task success rates of autonomous agents?

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`, current verifier feedback, reviewer comments.

The list follows the three research phases (setup → full experiment → hand‑off) and satisfies every functional requirement and success‑criterion in the specification. All tasks write only to project‑owned locations (`code/`, `data/`, `figures/`, `contracts/`, `specs/…`, `tests/`). No task touches platform‑owned directories (`state/`, `.github/`).

---

## Phase 1 – Contracts, synthetic data, and first end‑to‑end run  

- [ ] **T001** [P] [US1] **Copy contract schema files verbatim and verify duplication**  
  *Path*: `contracts/` (copies of the read‑only schemas from `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/`).  
  *Implementation*: `code/copy_contracts.py` copies each schema file, computes SHA‑256 for source and destination, and writes a mapping to **`contract_hashes.json`** at the repository root.  
  *Verification*: `tests/contract/test_contract_copy.py` loads `contract_hashes.json` and asserts `src_hash == dst_hash` for every file; the CI runs this test and must pass.

- [ ] **T002** [P] [US1] **Generate synthetic environment (tasks & skills) with deterministic seeds and overlap enforcement**  
  *Path*: `code/generate_data.py` → produces `data/raw/tasks.json` (500 tasks) and `data/raw/skills.json` (100 skills) with embeddings, semantic‑overlap levels, and a memory‑limit guard.  
  *Verification*: `tests/unit/test_generate_data.py` checks (1) record counts, (2) that each record validates against `task.schema.yaml` / `skill.schema.yaml`, (3) that the mean pairwise cosine similarity meets the requested overlap level, and (4) that the SHA‑256 digests recorded in `data/raw/checksums.json` match the actual file hashes.

- [ ] **T003** [P] [US1] **Implement checksum verification script and associated test**  
  *Path*: `code/write_checksums.py` recomputes SHA‑256 for `data/raw/tasks.json` and `data/raw/skills.json` and overwrites `data/raw/checksums.json` with the fresh mapping.  
  *Verification*: `tests/contract/test_checksums.py` loads `data/raw/checksums.json`, recomputes the hashes, and asserts equality; the test must pass in CI.

- [ ] **T004** [P] [US2] **Validate raw JSON files against their schemas**  
  *Path*: `tests/contract/test_schemas.py` runs `jsonschema.validate` on every entry of `data/raw/tasks.json` and `data/raw/skills.json` using `contracts/task.schema.yaml` and `contracts/skill.schema.yaml`.  
  *Verification*: The test suite must exit with success; any schema violation aborts the run.

- [ ] **T005** [P] [US2] **Configure logging and produce a minimal compliant CSV header**  
  *Path*: `code/logging_config.py` defines `LOG_COLUMNS = ["run_id","task_id","library_size","pruning_enabled","success","latency_ms","tokens_used","retrieval_precision","retrieval_diversity","edge_case"]` and provides `get_logger(name)` that writes rows to `data/results/experiment_log.csv`.  
  *Verification*: `tests/contract/test_logging_schema.py` (a) creates a dummy row via the logger, (b) checks that `data/results/experiment_log.csv` exists, (c) asserts the header order matches `LOG_COLUMNS`, and (d) validates the dummy row against `contracts/experiment_log.schema.yaml`.

- [ ] **T015** [P] [US2] **Create missing experiment_log.schema.yaml**  
  *Path*: `specs/001-llmxive-follow-up-extending-from-chatbot/contracts/experiment_log.schema.yaml` – write the schema defined in the specification (identical to the one shown in the data model).  
  *Verification*: `tests/contract/test_schemas.py -k "experiment_log"` validates the new schema file; CI must succeed before any logging validation runs.

---

## Phase 2 – Full experimental sweep, corrected pruning, and statistical analysis  

- [ ] **T006** [S] [US2] **Fix and extend the agent CLI; ensure CSV output for a small run**  
  *Path*: `code/agent.py` – add missing import `Tuple` from `typing`, correct argument parsing, and guarantee that every execution writes to `data/results/experiment_log.csv` **and** a JSON‑L file under `data/results/execution_logs/<run_id>.jsonl`. Ensure the script imports the newly added `experiment_log.schema.yaml` for validation.  
  *Verification*: `tests/integration/test_agent_small_run.py` runs  

    ```bash
    python -m code.agent --library-sizes 50 --task-sample 100 --pruning off --overlap HIGH
    ```  

    and asserts (1) the CSV contains 100 rows, (2) each row validates against `experiment_log.schema.yaml`, and (3) a matching JSON‑L file with 100 entries exists.

- [ ] **T007** [P] [US3] **Implement corrected “Skill Pruning” heuristic and its unit test**  
  *Path*: `code/pruning.py` – defines  

    ```python
    def prune_fr04(library: List[Skill]) -> Tuple[List[Skill], int]:
    ```  

    The function removes a skill **iff** (`usage_count == 0`) **and** (`min_cosine_similarity_to_any_other_skill_in_library < 0.70`). No ground‑truth check is performed, matching FR‑004. Returns the pruned library and the `false_prune_count`.  
  *Verification*: `tests/unit/test_pruning.py` constructs a deterministic mini‑library with known embeddings, calls `prune_fr04`, and checks that only the intended redundant skills are removed and that `false_prune_count` is correct.

- [ ] **T008** [S] [US2] **Run the full factorial sweep (library × pruning × overlap) and produce complete logs**  
  *Path*: `code/agent.py` now integrates `prune_fr04` (triggered after every 10 tasks when `--pruning fr04` is set) and records the evolving `library_size` in subsequent CSV rows.  
  *Experiment*: Execute all configurations  

    - library sizes `{10,20,30,40,50,60,70,80,90,100}`  
    - pruning flags `{off,fr04}`  
    - overlap levels `{LOW,MEDIUM,HIGH}`  

    processing the full 500‑task pool for each.  
  *Verification*: `tests/integration/test_full_sweep.py` runs the sweep (no dry‑run) and asserts: (1) the CSV contains exactly `10 × 2 × 3 × 500 = 30 000` rows, (2) every row validates against `experiment_log.schema.yaml`, (3) for pruning‑enabled runs `library_size` decreases at the 10‑task boundaries, and (4) `false_prune_count` extracted from the JSON‑L logs is ≥ 0.

- [ ] **T009** [P] [SC‑004 & SC‑006] **Statistical analysis script and validation (Piecewise Linear Regression)**  
  *Path*: `code/analysis.py` – reads `data/results/experiment_log.csv`, performs:  
    1. **Piecewise **linear** regression** (single breakpoint) on binary `success` vs. `library_size` for the HIGH‑overlap, no‑pruning baseline (using `pwlf`).  
    2. **Bootstrap** (1 000 resamples) to obtain a 95 % CI for the breakpoint (`x₀`).  
    3. **VIF** computation for raw predictors (`library_size`, `total_redundancy`, `overlap_level`, `pruning_enabled`).  
    4. **Likelihood‑ratio test** comparing the piecewise model to a single‑segment linear model.  
    5. **Mediation analysis** of pruning → total redundancy → success.  
    6. **Power analysis** based on the per‑condition sample size.  
    Writes `data/results/analysis_report.json`.  
  *Verification*: `tests/contract/test_analysis_output.py` checks that the JSON contains all required top‑level keys, that `breakpoint_estimate` lies between 10 and 100, that the two‑sided CI is present, and that every VIF value is numeric and `< 5.0`.

- [ ] **T010** [P] [SC‑005] **Feasibility check (runtime & memory) for a representative subset**  
  *Path*: `code/run_feasibility.py` runs a representative subset of the factorial sweep (library sizes up to 50, both pruning flags, all three overlap levels). It records wall‑clock time (`time.perf_counter()`), peak RSS memory (`psutil.Process().memory_info().rss`), and asserts total runtime ≤ 21 600 s (6 h) and peak RAM ≤ 7 GB. Results are written to `data/results/feasibility_report.json`.  
  *Verification*: `tests/feasibility/test_feasibility.py` executes the wrapper and asserts that both `within_time_limit` and `within_memory_limit` are `true`.

- [ ] **T011** [P] **(Optional) Generate figures and tables for exploratory analysis**  
  *Outputs*:  
    - `data/results/metrics.json` (conforms to `contracts/metrics.schema.yaml`) – one entry per `(library_size, pruning_enabled, overlap_level)`.  
    - `data/results/table_metrics.csv` – CSV rendering of `metrics.json`.  
    - Figures (`figures/success_vs_library_size.png`, `figures/pruning_comparison.png`, `figures/precision_diversity.png`) produced by `code/visualize.py` using deterministic Matplotlib settings and a fixed random seed.  
  *Verification*: `tests/contract/test_metrics_schema.py` validates `metrics.json`; `tests/test_figures.py` checks that each PNG exists, is non‑empty, and that re‑generating the figure with the same seed yields an identical SHA‑256 hash. (Marked optional because figures are not a strict functional requirement.)

- [ ] **T012** [P] **Write Methods & Results narrative linked to generated artifacts**  
  *Path*: `specs/001-llmxive-follow-up-extending-from-chatbot/research.md` – contains sections on data generation, experimental design, primary PLR findings, pruning efficacy, sensitivity & granularity validation, and limitations. Every numeric claim references the source JSON artifacts (`analysis_report.json`, `metrics.json`, `sensitivity_report.json`).  
  *Verification*: `tests/contract/test_narrative_consistency.py` parses the markdown, extracts numeric values, and asserts they match the source artifacts within a tolerance of `1e‑4`.

- [ ] **T013** [P] **Document reproducibility and paper‑stage handoff**  
  *Files*: `specs/001-llmxive-follow-up-extending-from-chatbot/quickstart.md` and `specs/001-llmxive-follow-up-extending-from-chatbot/reproducibility.md`.  
  *Content*: Step‑by‑step commands (data generation for each overlap, full sweep, analysis, figure generation), fixed seeds, pinned `requirements.txt`, and SHA‑256 digests of all key outputs (referencing `data/raw/checksums.json`).  
  *Verification*: `tests/reproducibility/test_checklist.py` clones a fresh repository, runs the quickstart script, and asserts that the regenerated digests match the recorded ones; any mismatch fails the test.

---

## Phase 3 – Reproducible results and paper handoff  

- [ ] **T014** [S] **Final handoff checklist**  
  *Path*: `specs/001-llmxive-follow-up-extending-from-chatbot/handoff.md` – enumerates all required artifacts for the downstream paper pipeline (analysis report, metrics, figures, narrative, reproducibility guide) and provides a single command `python reproducibility.py` that re‑creates them end‑to‑end.  
  *Verification*: Running `python reproducibility.py` on a clean checkout must regenerate **identical** `analysis_report.json`, `metrics.json`, and all PNGs (hash‑checked), confirming full reproducibility before the paper‑stage handoff.

---  

### Dependency mapping (spec → tasks)

| Spec requirement | Satisfying task(s) | Demonstration command |
|------------------|--------------------|-----------------------|
| FR‑001 (500 tasks) | T002, T004 | `python -m code.generate_data --overlap HIGH` |
| FR‑002 (100 skills, overlap) | T002, T004 | overlap statistics printed by the script |
| FR‑003 (library sizes, metrics) | T006, T008 | `python -m code.agent --library-sizes 10,20,… --overlap HIGH --pruning off` |
| FR‑004 (pruning heuristic) | T007, T008 | `pytest tests/unit/test_pruning.py` |
| FR‑005 (PLR breakpoint) | T009, T010 | `python -m code.analysis` → `analysis_report.json` |
| FR‑006 (precision & diversity) | T006, T011 | CSV columns `retrieval_precision`, `retrieval_diversity` |
| FR‑007 (VIF) | T009 | `analysis_report.json["vif_*"]` |
| Edge‑case handling (memory, missing skill, max overlap) | T006, T008 | integration tests cover these tags |
| SC‑001 – SC‑004 (success, precision, pruning effect, breakpoint) | T006, T008, T009, T011, T012 | cross‑checked by narrative‑consistency test |
| SC‑005 (runtime & RAM) | T010 | `feasibility_report.json` validated by CI |
| Reviewer pruning‑direction concern | T007, T008, T012 | corrected heuristic & reported effect |
| Concern ordering‑3d76f41b | T006 (CLI argument precedence) | command‑line parsing respects order |
| Concern executability‑c81f42cb | T007 (signature) | function matches spec |
| Concern executability‑2729c1b1 | T010 (feasibility) | runtime limits enforced |
| Concern constraint_preservation‑7b563a64 | T010, T003, T001 | all paths project‑owned; hashes prove verbatim copy |
| Concern executability‑ce0db35b | T014 (hand‑off) | handoff uses reproducibility script |
| Concern executability‑0386464f | T001 (checksum path) | checksum file placed where test expects |
| Concern constraint_preservation‑ff4fc116 | T007 (pruning logic) | heuristic matches FR‑004 |

**Execution order** (respecting data flow):  

T001 → T002 → T003 → T004 → T005 → T015 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014.  

All unchecked tasks will be marked complete by the CI runner only after their artefacts and tests pass.  

---  

*The above task list resolves every failed verification from the previous round, aligns the pruning heuristic with the specification, switches the analysis to the required piecewise linear regression, adds missing schema and import fixes, and provides a fully reproducible handoff without requiring a Makefile.*  