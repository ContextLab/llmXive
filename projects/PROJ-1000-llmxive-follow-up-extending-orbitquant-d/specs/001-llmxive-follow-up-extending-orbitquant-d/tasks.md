# Tasks: llmXive follow‑up – extending “OrbitQuant: Data‑Agnostic Quantization for Image and Video Diffusion T”

**Inputs**: `spec.md`, `plan.md`, existing `data‑model.md`, and contracts under `specs/001-llmxive-followup/`.  
All tasks are expressed as check‑boxes with the canonical `- [ ] T### [P?] [USx?] description …` format.  Indented continuation lines detail the required artifact, verification command, and any scientific requirement they satisfy.

---

## Phase 1 – Project initialization  

- [X] T001 [P] Create project skeleton, dependency list, configuration, and quick‑start guide  
  - **Artifacts**: directories `code/`, `code/data/`, `code/models/`, `code/analysis/`, `code/quantization/`, `code/evaluation/`, `tests/`, `data/raw/`, `data/processed/`, `state/`; files `requirements.txt`, `code/config.py`, `specs/001-llmxive-followup/quickstart.md`.  
  - **Verification**: `find code/ -type d | wc -l` ≥ 8, `python -c "import code.config"` succeeds, `grep -c "torch" requirements.txt` ≥ 1, and the quick‑start command `pip install -r requirements.txt && python code/main.py --phase init` runs without error and prints “Initialization complete”.

---

## Phase 2 – Data acquisition & prompt preparation  

- [ ] T002 [P] Download MS‑COCO validation set, extract captions, and fetch a diverse external prompt set   <!-- FAILED-IN-EXECUTION: code/data/download_coco.py exit=1; code/data/download_diverse_prompts.py exit=1; code/data/preprocess.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download_coco.py exit=1; code/data/download_diverse_prompts.py exit=1; code/data/preprocess.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download_coco.py exit=1; code/data/download_diverse_prompts.py exit=1; code/data/preprocess.py exit=1 -->
  - **Steps**  
    1. `code/data/download_coco.py` → `data/raw/coco_captions/` (HuggingFace `nlpconnect/coco_captions`, split = validation).  
    2. `code/data/preprocess.py` → `data/processed/prompts.csv` with columns `image_id, caption`. Must contain ≥ 400 rows.  
    3. `code/data/download_diverse_prompts.py` → `data/processed/diverse_prompts.csv` with columns `prompt_id, caption, source`; must contain ≥ 150 rows.  
  - **Verification**: `wc -l data/processed/prompts.csv` ≥ 400, `head -1 data/processed/diverse_prompts.csv` shows the three headers, and `wc -l data/processed/diverse_prompts.csv` ≥ 150. All scripts must raise a `RuntimeError` on fetch failure (no synthetic fallback).

---

## Phase 3 – Core model & analysis modules  

- [ ] T003 [P] Implement model loader (GPU escape hatch), activation‑variance capture, semantic‑entropy proxy, W2A4 quantizer, and static OrbitQuant baseline  
  - **Modules & artifacts**  
    * `code/models/flux_wan_loader.py` → function `load_dit_model(name, device="cpu")`; logs to `state/model_load_log.json`.  
    * `code/models/dit_wrapper.py` → class `DiTActivationCapture` with method `measure_activation_variance(prompt) → dict[layer_name → variance]`.  
    * `code/analysis/entropy_proxy.py` → `compute_semantic_entropy(prompt, num_samples=5) → float`. Returns `None` on proxy failure (logged to `state/proxy_failures.json`).  
    * `code/quantization/w2a4_engine.py` → class `W2A4Quantizer` with `quantize_activation(tensor, rotation_matrix=None)`.  
    * `code/quantization/static_baseline.py` → `get_static_rotation_matrix(dim, seed=42) → torch.Tensor`.  
  - **Verification**: Import each module (`python -c "import code.models.flux_wan_loader"` etc.) without error, instantiate classes, and run a single‑prompt sanity check (e.g., `prompt="a cat on a sofa"`). The sanity check must produce a non‑empty variance dict, a float entropy, and a quantized tensor shape matching the input.

---

## Phase 4 – End‑to‑end correlation analysis (User Story 1)  

- [ ] T004 [US1] Run the correlation pipeline and produce `data/processed/correlation_results.json`  
  - **Orchestration**: `code/run_correlation.py` performs: load `diverse_prompts.csv`, compute entropy (T003), load DiT (T003), generate a forward pass, capture activation variance (T003), and compute Pearson `r` and `p` via `scipy.stats.pearsonr`.  
  - **Output schema** (`correlation_results.json`): `{correlation: float, p_value: float, n_prompts: int, layers_analyzed: [str], entropy_range: [float, float], variance_range: [float, float]}`.  
  - **Verification**: `python -c "import json; r=json.load(open('data/processed/correlation_results.json')); assert 0<=r['p_value']<=1"` succeeds and `r['n_prompts']` ≥ 100.

---

## Phase 5 – Correlation hypothesis validation (gate)  

- [ ] T005 [US1] Validate that the correlation is statistically significant (p < 0.05)  
  - **Script**: `code/validation/validate_correlation.py` reads `correlation_results.json`; if `p_value < 0.05` writes `state/correlation_validated.json` with `{status:"pass", timestamp:…}` else writes `{status:"fail", reason:"p ≥ 0.05"}` and exits with non‑zero code.  
  - **Verification**: `cat state/correlation_validated.json | grep status` shows “pass”. The rest of the pipeline (Phases 6‑12) is gated on this file existing with status = pass.

---

## Phase 6 – Derive rotation matrices via entropy‑based clustering (User Story 2)  

- [ ] T006 [US2] Perform K‑Means clustering on entropy, generate 16 rotation matrices, and emit `data/processed/clustering_report.json`  
  - **Steps** (implemented in `code/analysis/clustering.py`)  
    1. Load entropy values from `correlation_results.json`.  
    2. Split prompts 80 %/20 % (fixed seed = 42).  
    3. K‑Means (K = 16) on entropy → bin boundaries.  
    4. For each bin, aggregate activation‑variance histograms (from the variance capture) and compute a rotation matrix via SVD of the covariance.  
    5. Save matrices as `data/processed/rotation_matrices/matrix_0.npy` … `matrix_15.npy`.  
    6. Write `clustering_report.json` matching the `rotation_matrix_schema` (cluster_id, entropy_range_min/max, matrix_shape, matrix_data_ref, derived_from_split).  
  - **Verification**: `ls data/processed/rotation_matrices/ | wc -l` = 16, and `python - <<'PY'\nimport json, pathlib, numpy as np\nr=json.load(open('data/processed/clustering_report.json'))\nassert len(r['matrices'])==16\nfor m in r['matrices']:\n    path=pathlib.Path(m['matrix_data_ref'])\n    assert path.is_file()\n    arr=np.load(path)\n    assert arr.shape[0]==arr.shape[1]\nprint('OK')\nPY` exits without AssertionError.

---

## Phase 7 – Clustering report validation  

- [ ] T007 [US2] Verify existence and schema of `clustering_report.json` (formerly T023a)  
  - **Script**: `code/validation/validate_clustering.py` checks that the file exists, conforms to the JSON schema in `specs/…/rotation_matrix_schema.schema.yaml`, and that each matrix is orthogonal (QR check). Writes `state/clustering_validated.json` with `{status:"pass", timestamp:…}` or a failure description.  
  - **Verification**: `cat state/clustering_validated.json | grep status` shows “pass”.

---

## Phase 8 – Quantization validation using derived matrices  

- [ ] T008 [US2] Apply each derived rotation matrix to activations, quantize with W2A4, and save `data/processed/quantized_activations.json`  
  - **Orchestration**: `code/run_quantization_validation.py` loads the test‑split prompts, loads rotation matrices via the loader (T010), captures activations (T003), applies the matrix, runs `W2A4Quantizer.quantize_activation`, and records for each prompt/layer `{prompt_id, layer_name, quantized_values, rotation_index}`.  
  - **Output schema**: list of objects matching the `activation_schema` with an extra `rotation_index`.  
  - **Verification**: `python -c "import json; q=json.load(open('data/processed/quantized_activations.json')); assert len(q)>=100"` succeeds.

---

## Phase 9 – Dynamic router implementation and integration  

- [ ] T009 [US2] Implement entropy‑to‑rotation lookup and integrate it into the quantizer  
  - **Components**  
    * `code/analysis/router.py` → class `EntropyRouter` with `select_rotation_index(entropy) → int` (clamps out‑of‑range values, logs to `state/router_edge_cases.json`).  
    * Extend `W2A4Quantizer` (T003) to accept an optional `router` and an `entropy_score` argument; it selects the matrix via the router before quantization.  
  - **Verification**: `python - <<'PY'\nfrom code.analysis.router import EntropyRouter\nr=EntropyRouter()\nassert 0<=r.select_rotation_index(-1.0)<=15\nassert 0<=r.select_rotation_index(1e6)<=15\nprint('OK')\nPY` runs, and a unit test (see Phase 13) passes.

---

## Phase 10 – Rotation‑matrix loading and orthogonality check  

- [ ] T010 [US2] Load all 16 matrices and validate orthogonality (formerly T028)  
  - **Function**: `code/analysis/load_matrices.py` → `load_rotation_matrices(report_path) → List[torch.Tensor]`. Raises `ValueError` on missing files, shape mismatch, or non‑orthogonal matrices.  
  - **Verification**: `python -c "from code.analysis.load_matrices import load_rotation_matrices; mats=load_rotation_matrices('data/processed/clustering_report.json'); assert len(mats)==16; print('OK')"` succeeds.

---

## Phase 11 – Router‑driven inference orchestration  

- [ ] T011 [US2] Run inference with the dynamic router and record selections (formerly T029)  
  - **Script**: `code/run_router_inference.py` loads test prompts, computes entropy, loads matrices (T010), selects rotation via `EntropyRouter`, runs generation with the rotated activations, and writes `data/processed/router_selections.json` (`[{prompt_id, entropy, selected_matrix_index}]`).  
  - **Verification**: `python -c "import json; s=json.load(open('data/processed/router_selections.json')); assert len(s)>=100 and all(0<=r['selected_matrix_index']<=15 for r in s)"` succeeds.

---

## Phase 12 – Full evaluation pipeline and final report (User Story 3)  

- [ ] T012 [US3] Execute baseline and dynamic pipelines, compute metrics, perform statistical tests, and produce `data/processed/final_evaluation_report.json` (formerly T036)  
  - **Orchestration**: `code/run_evaluation.py`  
    1. Baseline: use `static_baseline` rotation, generate images for all test prompts, compute FID, CLIP, MSE, and per‑prompt inference time → `baseline_evaluation.json`.  
    2. Dynamic: use router (T009) → `dynamic_evaluation.json`.  
    3. Run paired t‑tests (with Bonferroni correction) for each metric via `code/analysis/statistical_test.py`.  
    4. Compute runtime overhead percent.  
    5. Assemble `final_evaluation_report.json` matching the `results_schema` (including `rotation_index` for dynamic rows) and containing fields: `baseline_mean_fid`, `dynamic_mean_fid`, `fid_improvement_percent`, `baseline_mean_time_ms`, `dynamic_mean_time_ms`, `overhead_percent`, `p_values`, `conclusion`.  
  - **Verification**: `cat data/processed/final_evaluation_report.json | grep overhead_percent` returns a numeric value ≤ 2.0, and `grep "pass" data/processed/final_evaluation_report.json` shows a non‑empty `conclusion` string.

---

## Phase 13 – Edge‑case unit tests  

- [ ] T013 [US2] Add unit tests covering out‑of‑range entropy, proxy failure logging, and activation outliers (formerly T039)  
  - **Files**: `tests/unit/test_edge_cases.py` with three test functions using `pytest`.  
  - **Verification**: `pytest tests/unit/test_edge_cases.py -q` reports 3 passed tests.

---

## Phase 14 – Security, path sanitization, and checksum validation  

- [ ] T014 [US?] Harden data loading and model loading against path traversal and tampering (formerly T040)  
  - **Changes**  
    * All file‑path constructions use `pathlib.Path` with `resolve()` and reject any path containing `..` or that is outside the project root.  
    * After each dataset or model download, compute SHA‑256 and store in `state/artifact_hashes.json`.  
    * At load time, verify the current file’s checksum matches the recorded value; raise `RuntimeError` on mismatch.  
  - **Verification**: Corrupt a downloaded file (e.g., append a byte) and run a loader script; it must abort with an error mentioning “checksum mismatch”. The test `tests/unit/test_security.py` (added automatically) passes.

---

### Dependency & execution order (critical path)

1. **T001** → **T002** → **T003** → **T004** → **T005** (gate) → **T006** → **T007** → **T008** → **T009** → **T010** → **T011** → **T012** → **T013** → **T014**.  

All later phases are blocked until the preceding validation tasks (`T005`, `T007`) write a “pass” status file.

--- 

*All tasks above are unchecked; the CI will mark a task as completed only after the described artifact exists and the verification command succeeds.*
