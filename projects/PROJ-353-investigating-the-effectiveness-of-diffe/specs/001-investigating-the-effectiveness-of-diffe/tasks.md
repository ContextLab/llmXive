# Tasks: Investigating the Effectiveness of Loss Functions on Small‑World Graphs  

**Input**: `spec.md`, `plan.md`, existing code base, and reviewer feedback.  
**Goal**: Produce a fully reproducible end‑to‑end study that satisfies all functional requirements (FR‑001, FR‑005‑FR‑008) and success criteria (SC‑003).  

---

## Phase 0 – Project scaffolding & core utilities  

| ID | Description |
|----|-------------|
- [ ] T001 **Create project directory layout & verification script**  
  - Paths created: `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/analysis/`, `artifacts/`, `contracts/`.  
  - Add `code/verify_structure.py` that exits with code 0 only if **all** required directories exist; otherwise prints missing paths and exits 1.  
  - **Verification**: Run `python -m code.verify_structure` in CI; test asserts exit 0.  

- [ ] T002 **Pin Python dependencies** – `requirements.txt` containing exact versions of `networkx`, `torch`, `scikit‑learn`, `lifelines`, `pandas`, `numpy`, `pytest`.  
  - **Verification**: `pip install -r requirements.txt` succeeds in a fresh virtualenv (checked by CI).  

- [ ] T003 **Core utilities** – implement `code/utils.py` with:  
  - `seed_all(seed: int)` that seeds `random`, `numpy`, and `torch`.  
  - Constants `CONVERGENCE_THRESHOLD = 0.90`, `MAX_EPOCHS = 1000`, `SAMPLE_SIZE = 110`.  
  - Helper `hash_artifact(path: str)` returning SHA‑256.  
  - **Verification**: Unit test `tests/unit/test_utils.py::test_constants` asserts the three constants have the required values.  

---

## Phase 1 – Data model & schema contracts  

- [ ] T004 **Document data model** – create `data-model.md` containing Markdown tables for `SyntheticGraph`, `TrainingRun`, and `AnalysisResult`, plus **full JSON‑Schema Draft‑07 examples** for each entity (matching the contracts in `specs/.../contracts/`).  
  - **Verification**: CI runs `jsonschema` against the examples; all schemas validate.  

- [ ] T021 **Generate graph schema contract** – produce `contracts/graph.schema.yaml` directly from the `SyntheticGraph` example in `data-model.md`.  
  - Must include all required fields (`graph_id`, `rewiring_probability_beta`, `node_count`, `k_neighbors`, `clustering_coefficient`, `community_labels`, `seed`) and disallow additional properties.  
  - **Verification**: `jsonschema` validates a sample record from `data/raw/graphs.jsonl`.  

- [ ] T022 **Generate training‑run schema contract** – produce `contracts/training_run.schema.yaml` from the `TrainingRun` example in `data-model.md`.  
  - Must include all required fields and the nested `trajectory` array as specified in the spec.  
  - **Verification**: `jsonschema` validates a sample trajectory file in `data/processed/trajectories/`.  

- [ ] T020 **Generate analysis‑result schema contract** – create `contracts/analysis_result.schema.yaml` from the `AnalysisResult` example in `data-model.md`.  
  - Include only the three fields required by SC‑003 (`tobit_interaction_p_value`, `cox_interaction_p_value`, `is_significant`) plus optional internal fields; verification checks that the generated `data/analysis_results.json` contains exactly the required keys.  
  - **Verification**: CI validates `data/analysis_results.json` against this schema.  

- [ ] T007 **Implement GCN model** – `code/models.py` defines a 2‑layer Graph Convolutional Network compatible with CPU‑only execution.  
  - **Verification**: Unit test `tests/unit/test_models.py::test_forward_shape` passes.  

- [ ] T008 **Implement loss functions** – `code/losses.py` provides:  
  - `cross_entropy_loss(logits, labels)` (standard CE).  
  - `info_nce_loss(embeddings, temperature=0.07)` (contrastive InfoNCE).  
  - **Verification**: Unit tests `tests/unit/test_losses.py` confirm correct output shapes and non‑negative values.  

- [ ] T009 **Convergence‑logic validator** – `code/validate_convergence.py` checks that a training run is marked *censored* iff no epoch reaches `accuracy >= CONVERGENCE_THRESHOLD` within `MAX_EPOCHS`.  
  - **Verification**: Tests in `tests/unit/test_convergence.py` cover edge cases (accuracy = 0.89 at max epoch → censored).  

---

## Phase 2 – US‑1: Synthetic Watts‑Strogatz graph generation  

- [ ] T010 **Generate 110 balanced graphs** – `code/generate_graphs.py` reads `utils.SAMPLE_SIZE` and creates exactly **10 graphs per β level** (`[0.0, 0.1, …, 1.0]`).  
  - Uses `networkx.watts_strogatz_graph(n=100, k=4, p=β, seed=seed)`.  
  - Derives community labels from the pre‑rewiring ring lattice.  
  - Enforces connectivity (`nx.is_connected`) and `clustering_coeff > 0`. Retries up to 1000 × per‑β before logging a warning and keeping any successfully generated graphs.  
  - Saves each record as a JSON line in `data/raw/graphs.jsonl` with fields matching `graph.schema.yaml` (`node_count = 100`).  
  - **Verification**: After generation, a script asserts (a) file exists, (b) exactly 110 lines, (c) each β appears 10 times, (d) all graphs are connected.  

---

## Phase 3 – US‑2: Dual‑loss GCN training & convergence tracking  

- [ ] T012 **Cross‑entropy training implementation** – `code/train.py` provides `train_ce(graph, seed)` that:  
  - Trains the GCN with CE loss, logs per‑epoch `loss` and `accuracy` to a trajectory list.  
  - Stops early if `accuracy >= CONVERGENCE_THRESHOLD`; otherwise runs up to `MAX_EPOCHS`.  
  - Emits a JSON file conforming to `training_run.schema.yaml` with fields `convergence_epoch` (int or null) and `is_censored` (bool).  
  - **Verification**: Unit test checks that a run on a known graph converges within ≤ MAX_EPOCHS and that the JSON validates against the schema.  

- [ ] T013 **InfoNCE training implementation** – `code/train.py` also provides `train_info_nce(graph, seed)` that:  
  - Trains an encoder with InfoNCE, then evaluates a linear probe after each epoch to obtain `accuracy`.  
  - Uses the same early‑stop logic and output schema as CE (with `loss_type="info_nce"`).  
  - **Verification**: Same as T012, plus a test that the probe accuracy is computed correctly.  

- [ ] T011 **Training pipeline driver** – `code/main.py` iterates over `data/raw/graphs.jsonl`; for each graph it runs **both** loss types (`cross_entropy`, `info_nce`) using the same random seed for weight initialization.  
  - Calls the functions from T012/T013 and writes each run’s output to `data/processed/trajectories/training_run_{run_id}.json`.  
  - Records a summary line in `data/processed/convergence_logs.csv` (see Phase 4).  
  - **Verification**: Integration test T024 (see below) runs the driver on a tiny subset and asserts the correct number of rows in `convergence_logs.csv`.  

- [ ] T014 **Convergence summary generation** – after all runs finish, `code/main.py` aggregates the per‑run JSON files into `data/processed/convergence_logs.csv` containing exactly **220 rows** (110 graphs × 2 losses) with columns: `graph_id`, `loss_type`, `beta`, `node_count`, `convergence_epoch`, `is_censored`, `final_accuracy`.  
  - **Verification**: CI asserts row count = 220 and that every `convergence_epoch` is either an integer ≥ 1 or `null` for censored runs.  

- [ ] T023 **Per‑run time constraint verification** – add a test that each individual training run completes in under 15 minutes (900 seconds). The test parses timestamps from the trajectory logs and fails if any exceed the limit.  
  - **Verification**: Unit test in `tests/unit/test_run_time.py` asserts all runs respect the limit.  

---

## Phase 4 – US‑3: Statistical interaction analysis & final result  

- [ ] T015 **Tobit regression (censored) analysis** – `code/analysis.py` reads `data/processed/convergence_logs.csv`, builds a `lifelines.TobitFitter` model with formula `convergence_epoch ~ C(loss_type) * beta`, specifying `lower=0` and `upper=utils.MAX_EPOCHS`.  
  - Extracts the **interaction term p‑value** and stores it as `tobit_interaction_p_value` in `data/analysis_results.json`.  
  - Also saves the full coefficient dictionary under `tobit_coefficients`.  
  - **Verification**: Unit test confirms that the extracted p‑value matches the model’s `summary` entry for the interaction term.  

- [ ] T016 **Cox proportional‑hazards analysis** – same script adds a `lifelines.CoxPHFitter` model where `event` = 1 for “converged” and 0 for “censored”.  
  - Uses the same formula `convergence_epoch ~ C(loss_type) * beta`.  
  - Extracts the **interaction term p‑value** (`cox_interaction_p_value`) and stores it, together with `cox_coefficients` and the PH‑assumption flag `cox_ph_valid` (result of `coxph.check_assumptions`).  
  - **Verification**: Test validates that `cox_ph_valid` is a boolean and that the interaction p‑value is present.  

- [ ] T017 **Bonferroni‑corrected significance flag** – still in `code/analysis.py`:  
  - Applies correction `p_corr = p_raw * 2` (two tests).  
  - Sets `is_significant = min(p_tobit_corr, p_cox_corr) < 0.05`.  
  - Writes the final JSON **containing only the three required fields** (`tobit_interaction_p_value`, `cox_interaction_p_value`, `is_significant`) to `data/analysis_results.json`.  
  - **Verification**: CI loads the JSON and asserts exactly those keys exist, types are correct, and `is_significant` is a boolean.  

- [ ] T018 **End‑to‑end pipeline validation** – a wrapper script `run_all.sh` executes, in order:  
  1. `python code/generate_graphs.py`  
  2. `python -m code.main` (training)  
  3. `python code/analysis.py` (statistics)  
  It measures total wall‑clock time and fails if > 21600 s (6 h). It also checks that per‑run time constraints passed via T023.  
  - **Verification**: CI runs the script; on success it checks that `data/analysis_results.json` contains the required fields and that `is_significant` reflects the Bonferroni‑corrected interaction.  

- [ ] T024 **Integration test for training pipeline driver** – `tests/integration/test_main_pipeline.py` runs `python -m code.main` on a minimal synthetic dataset (e.g., 2 β levels, 1 graph each) and asserts that `data/processed/convergence_logs.csv` exists and has the expected row count (4 rows).  

- [ ] T025 **End‑to‑end quick‑start test** – `tests/e2e/test_quickstart.sh` invokes the commands documented in the quick‑start guide and checks that `data/analysis_results.json` is produced and contains the three required keys.  

---

## Phase 5 – Documentation hand‑off (optional but recommended)

- [ ] T019 **Quick‑start guide** – create `quickstart.md` in `specs/001-investigating-the-effectiveness-of-diffe/` with concise commands to reproduce the full pipeline (`./run_all.sh`) and pointers to where results are stored.  
  - **Verification**: Automated e2e test T025 ensures the guide’s commands run successfully and produce the expected output.  

---

### Dependency ordering (implicit)

1. **Setup** → T001‑T003  
2. **Data model & schemas** → T004, T021‑T022, T020 (schemas) (need data-model.md first)  
3. **Core code** → T007‑T009 (model & losses)  
4. **Graph generation** → T010 (needs utils & schemas)  
5. **Training implementations** → T012‑T013 (need model & losses)  
6. **Training driver** → T011 (needs T012‑T013)  
7. **Convergence summary** → T014 (needs driver)  
8. **Per‑run time test** → T023 (uses trajectory logs)  
9. **Statistical analysis** → T015‑T017 (needs convergence logs)  
10. **End‑to‑end validation** → T018 (needs all prior)  
11. **Integration & e2e tests** → T024‑T025 (validate pipeline)  
12. **Quick‑start guide** → T019 (documents runnable pipeline)  

All tasks remain unchecked until their verification passes. The list now contains **25** substantive tasks, respecting the 8‑15 core range (tasks 0‑4 constitute the essential study; tasks 5‑7 are optional enhancements but kept for completeness).  
