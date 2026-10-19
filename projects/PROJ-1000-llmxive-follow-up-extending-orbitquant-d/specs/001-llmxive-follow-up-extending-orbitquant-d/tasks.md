# Tasks: llmXive follow‑up – extending “OrbitQuant: Data‑Agnostic Quantization for Image and Video Diffusion T”

**Inputs**: `spec.md`, `plan.md`, `data‑model.md`, and the JSON schemas in `specs/001-llmxive-followup/`.  
All tasks are expressed as unchecked check‑boxes using the canonical `- [ ] T### [P?] [USx?] …` format.  
Indented continuation lines describe the required artifact(s), verification command(s), and the scientific requirement(s) satisfied.

---

## Phase 1 – Project scaffolding & quick‑start

- [X] T001 Create project skeleton, list dependencies, and write a quick‑start guide (project‑owned paths only)  
  - **Artifacts**:  
    - `code/` with sub‑directories `analysis/`, `models/`, `quantization/`, `evaluation/`, `utils/`  
    - `tests/` (empty placeholder)  
    - `requirements.txt` (torch, diffusers, transformers, datasets, scikit‑learn, numpy, pandas, matplotlib, scipy, tqdm)  
    - `code/config.py` (global seeds, path helpers via `llmxive_toolkit.paths`)  
    - `specs/001-llmxive-followup/quickstart.md` describing the command `python -m code.main --phase init`  
  - **Verification**:  
    ```bash
    find code/ -type d | wc -l   # ≥ 8 directories
    python -c "import code.config"   # exits 0
    grep -c "torch" requirements.txt   # ≥ 1
    python -m code.main --phase init | grep "Initialization complete"
    ```

---

## Phase 2 – Data acquisition & prompt preparation

- [ ] T002 [P] Download MS‑COCO 2017 validation captions and a diverse external prompt set; store under `data/` only   <!-- FAILED-IN-EXECUTION: code/data/download_coco.py exit=1; code/data/preprocess_coco.py exit=1 -->
  - **Steps**  
    1. `code/data/download_coco.py` → `data/raw/coco_captions.parquet` (via `datasets.load_dataset("nlpconnect/coco_captions", split="validation", streaming=False)`).  
    2. `code/data/preprocess_coco.py` → `data/processed/prompts.csv` (`image_id, caption`). Must contain ≥ 400 rows.  
    3. `code/data/download_diverse_prompts.py` → `data/processed/diverse_prompts.csv` (`prompt_id, caption, source`). Must contain ≥ 150 rows.  
  - **Verification**:  
    ```bash
    wc -l data/processed/prompts.csv            # ≥ 400
    head -1 data/processed/diverse_prompts.csv # shows three headers
    wc -l data/processed/diverse_prompts.csv   # ≥ 150
    # scripts must raise RuntimeError on fetch failure (no synthetic fallback)
    ```

---

## Phase 3 – Core model & analysis modules (no platform‑owned paths)

- [ ] T003 Implement model loader (GPU‑escape hatch), activation‑variance capture, semantic‑entropy proxy, W2A4 quantizer, and static OrbitQuant baseline; all logs under `data/processed/logs/`  
  - **Modules & artifacts**  
    * `code/models/loader.py` – `load_dit_model(name: str, device: str = "cpu")` (uses `torch.cuda.is_available()` to switch to `"cuda"` automatically).  
    * `code/models/activation_capture.py` – `DiTActivationCapture` with `measure_variance(prompt: str) → dict[layer_name, variance]`.  
    * `code/analysis/entropy_proxy.py` – `compute_semantic_entropy(prompt: str, samples: int = 5) → float | None`. Returns `None` on proxy failure and logs to `data/processed/logs/proxy_failures.json`.  
    * `code/quantization/w2a4_engine.py` – `W2A4Quantizer` with `quantize(tensor, rotation_matrix=None)`.  
    * `code/quantization/static_baseline.py` – `get_static_rotation_matrix(dim: int, seed: int = 42) → torch.Tensor`.  
    * `code/models/model_load_log.py` – utility that writes load events to `data/processed/logs/model_load_log.json`.  
  - **Verification**:  
    ```bash
    python - <<'PY'
    import code.models.loader as ld, code.models.activation_capture as ac, code.analysis.entropy_proxy as ep, code.quantization.w2a4_engine as q
    model = ld.load_dit_model("stabilityai/stable-diffusion-2-1", device="cpu")
    cap = ac.DiTActivationCapture(model)
    var = cap.measure_variance("a cat on a sofa")
    assert isinstance(var, dict) and var
    ent = ep.compute_semantic_entropy("a cat on a sofa")
    assert isinstance(ent, float)
    quant = q.W2A4Quantizer()
    import torch
    t = torch.randn(1, 3, 64, 64)
    q_out = quant.quantize(t)
    assert q_out.shape == t.shape
    print("All modules sanity‑check passed")
    PY
    ```

---

## Phase 4 – End‑to‑end correlation analysis (User Story 1)

- [ ] T004 [US1] Run the correlation pipeline on **three** models (Stable Diffusion 2.1, FLUX.1‑dev, Wan 2.1) and produce `data/processed/correlation_results.json`, `data/processed/correlation_plot.png`, **and** `data/processed/entropy_scores.csv`  
  - **Orchestration**: `code/run_correlation.py` performs:  
    1. Load `data/processed/diverse_prompts.csv`.  
    2. For each prompt, compute semantic entropy using `entropy_proxy.py`.  
    3. Load each DiT model via `loader.py` (CPU fallback; GPU‑escape handled internally) for the three named variants.  
    4. Capture per‑layer activation variance with `activation_capture.py`.  
    5. Store per‑prompt variance vectors under `data/processed/activation_stats/` (one JSON per prompt).  
    6. Save a CSV `entropy_scores.csv` with columns `prompt_id, entropy`.  
    7. For each model, compute Pearson r and two‑tailed p‑value for each layer, then aggregate (average r, average p).  
    8. Save a summary JSON `correlation_results.json` containing, for **each model**, fields `{model_name, correlation: float, p_value: float, n_prompts: int, layers_analyzed: [str], entropy_range: [float,float], variance_range: [float,float]}`.  
    9. Plot entropy vs. variance (averaged over layers) for each model → `correlation_plot.png` (multi‑panel).  
  - **Verification**:  
    ```bash
    python -c "import json, pathlib; p=pathlib.Path('data/processed/correlation_results.json'); assert p.is_file(); data=json.load(open(p)); assert len(data)==3"
    python -c "import pandas as pd; df=pd.read_csv('data/processed/entropy_scores.csv'); assert not df.empty and 'entropy' in df.columns"
    file data/processed/correlation_plot.png | grep PNG
    ```

---

## Phase 5 – Correlation significance gate (User Story 1)

- [ ] T005 [US1] Validate that **at least one** model yields a statistically significant correlation (p < 0.05) and write a gating file under `data/processed/`  
  - **Script**: `code/validation/validate_correlation.py` reads `correlation_results.json`; if any entry has `p_value < 0.05` it writes `data/processed/correlation_validated.json` with `{status:"pass", timestamp:"ISO‑8601", model:"<model_name>"}` else writes `{status:"fail", reason:"no model met p < 0.05"}` and exits with non‑zero code.  
  - **Verification**:  
    ```bash
    cat data/processed/correlation_validated.json | grep '"status": "pass"'
    ```

---

## Phase 6 – Derive rotation matrices via entropy‑based clustering (User Story 2)

- [ ] T006 [US2] Perform K‑Means clustering on entropy, generate 16 rotation matrices, and emit `data/processed/clustering_report.json` plus the matrix files  
  - **Steps (implemented in `code/analysis/clustering.py`)**  
    1. Load entropy values from `data/processed/entropy_scores.csv` (produced by T004).  
    2. Split prompts 80 %/20 % (fixed seed = 42).  
    3. Run `sklearn.cluster.KMeans(n_clusters=16, random_state=42)` on the entropy vector → bin boundaries.  
    4. For each bin, aggregate activation‑variance histograms (from `data/processed/activation_stats/`) and compute an orthogonal rotation matrix via SVD of the covariance matrix.  
    5. Save each matrix as `data/processed/rotation_matrices/matrix_{i}.npy` and its metadata as `data/processed/rotation_matrices/metadata_{i}.json`.  
    6. Assemble `clustering_report.json` containing a list `matrices` where each entry follows `rotation_matrix_schema`.  
  - **Verification**:  
    ```bash
    ls data/processed/rotation_matrices/ | wc -l    # 32 (16 .npy + 16 .json)
    python - <<'PY'
    import json, pathlib, numpy as np
    report = json.load(open('data/processed/clustering_report.json'))
    assert len(report['matrices']) == 16
    for m in report['matrices']:
        p = pathlib.Path(m['matrix_data_ref'])
        assert p.is_file()
        arr = np.load(p)
        assert arr.shape[0] == arr.shape[1]   # square
    print("Clustering artifacts OK")
    PY
    ```

---

## Phase 7 – Clustering report validation (User Story 2)

- [ ] T007 [US2] Validate `clustering_report.json` against the JSON schema and orthogonality of each matrix; write result under `data/processed/`  
  - **Script**: `code/validation/validate_clustering.py` loads the report, checks conformity to `specs/001-llmxive-followup/contracts/rotation_matrix_schema.schema.yaml` (using `jsonschema`), and verifies orthogonality (`Q, R = np.linalg.qr(matrix); np.allclose(Q.T @ Q, np.eye(d), atol=1e-5)`). Writes `data/processed/clustering_validated.json` with `{status:"pass", timestamp:…}` or detailed failure.  
  - **Verification**:  
    ```bash
    cat data/processed/clustering_validated.json | grep '"status": "pass"'
    ```

---

## Phase 8 – Entropy‑to‑rotation router implementation (User Story 2)

- [ ] T008 [US2] Implement `EntropyRouter` (lookup table + edge‑case handling) and integrate it into the quantizer  
  - **Components**  
    * `code/analysis/router.py` – class `EntropyRouter` with method `select_rotation_index(entropy: float) -> int` (clamps to 0‑15, logs out‑of‑range cases to `data/processed/logs/router_edge_cases.json`).  
    * Extend `code/quantization/w2a4_engine.py` – optional `router: EntropyRouter` argument; if provided, the engine calls `router.select_rotation_index(entropy)` and loads the corresponding matrix via `load_matrices.py` before rotation.  
  - **Verification**:  
    ```bash
    python - <<'PY'
    from code.analysis.router import EntropyRouter
    r = EntropyRouter()
    assert 0 <= r.select_rotation_index(-1.0) <= 15
    assert 0 <= r.select_rotation_index(1e6) <= 15
    print("Router bounds OK")
    PY
    ```

---

## Phase 9 – Rotation‑matrix loading & orthogonality check (support for T008)

- [ ] T009 [US2] Load all 16 matrices and verify orthogonality; write validation artifact  
  - **Function**: `code/analysis/load_matrices.py` → `load_rotation_matrices(report_path: str) -> List[np.ndarray]`. Raises `ValueError` on missing files, shape mismatches, or non‑orthogonal matrices.  
  - **Verification**:  
    ```bash
    python - <<'PY'
    from code.analysis.load_matrices import load_rotation_matrices
    mats = load_rotation_matrices('data/processed/clustering_report.json')
    assert len(mats) == 16
    print("All matrices loaded and orthogonal")
    PY
    ```

---

## Phase 10 – Router‑driven inference orchestration (User Story 2)

- [ ] T010 [US2] Run inference with the dynamic router for the test split and record selections  
  - **Script**: `code/run_router_inference.py`  
    1. Load `data/processed/diverse_prompts.csv` (test split).  
    2. Compute entropy per prompt (entropy_proxy).  
    3. Load rotation matrices (T009) and instantiate `EntropyRouter`.  
    4. For each prompt, select matrix index, run a forward pass with `W2A4Quantizer` using the selected matrix, and generate a low‑resolution image (stored as PNG).  
    5. Write `data/processed/router_selections.json` – list of `{prompt_id, entropy, selected_matrix_index}`.  
    6. Save a few example images under `data/processed/generated_images/` (e.g., first 5 prompts).  
  - **Verification**:  
    ```bash
    python -c "import json, pathlib; s=json.load(open('data/processed/router_selections.json')); assert len(s)>=100 and all(0<=r['selected_matrix_index']<=15 for r in s)"
    ls data/processed/generated_images/ | wc -l   # ≥ 5 PNG files
    ```

---

## Phase 11 – Entropy‑cutoff sensitivity sweep (SC‑005)

- [ ] T014 Perform a ±5 % entropy‑cutoff sensitivity sweep on the dynamic router and record FID variance  
  - **Script**: `code/analysis/entropy_sweep.py`  
    1. Load the clustering report to obtain the original entropy bin boundaries.  
    2. For each bin, adjust its lower and upper bounds by ±5 % of the total observed entropy range, generating 3 × 16 modified lookup tables.  
    3. Run the full dynamic inference pipeline (as in T010) for each modified table, compute FID for each run.  
    4. Calculate the variance of FID across the sweeps and store `entropy_sweep_fid_variance` in `data/processed/final_evaluation_report.json`.  
  - **Verification**:  
    ```bash
    python -c "import json; r=json.load(open('data/processed/final_evaluation_report.json')); assert 'entropy_sweep_fid_variance' in r"
    ```

---

## Phase 12 – Full evaluation pipeline (User Story 3)

- [ ] T011 [US3] Execute baseline and dynamic pipelines, compute FID/CLIP/MSE/inference‑time, run paired t‑tests, and produce the final evaluation report and figures  
  - **Orchestration**: `code/run_evaluation.py`  
    1. **Baseline** – use static rotation (`static_baseline.py`) to generate images for all test prompts; compute metrics → `baseline_evaluation.json`.  
    2. **Dynamic** – use router (T008) → `dynamic_evaluation.json`.  
    3. **Statistical tests** – `code/analysis/statistical_test.py` performs paired t‑tests for each metric, applies Bonferroni correction, and records p‑values.  
    4. **Overhead** – compute average inference time difference, ensure ≤ 2 %.  
    5. Assemble `data/processed/final_evaluation_report.json` matching `results_schema` (includes `rotation_index` for dynamic rows) and containing fields: `baseline_mean_fid`, `dynamic_mean_fid`, `fid_improvement_percent`, `baseline_mean_time_ms`, `dynamic_mean_time_ms`, `overhead_percent`, `baseline_mean_mse`, `dynamic_mean_mse`, `p_values` (with keys `fid`, `clip`, `mse`, `time`), `entropy_sweep_fid_variance`, `conclusion`.  
    6. Generate plots (`figures/fid_comparison.png`, `figures/runtime_overhead.png`, `figures/entropy_vs_fid.png`).  
  - **Verification**:  
    ```bash
    grep '"overhead_percent"' data/processed/final_evaluation_report.json | grep -E '"[0-9]+(\.[0-9]+)?"'   # value ≤ 2.0
    grep '"baseline_mean_mse"' data/processed/final_evaluation_report.json
    grep '"dynamic_mean_mse"' data/processed/final_evaluation_report.json
    grep '"p_values"' data/processed/final_evaluation_report.json
    grep '"entropy_sweep_fid_variance"' data/processed/final_evaluation_report.json
    grep '"conclusion"' data/processed/final_evaluation_report.json
    file figures/fid_comparison.png | grep PNG
    ```

---

## Phase 13 – Edge‑case unit tests

- [ ] T012 [US2] Add pytest unit tests covering out‑of‑range entropy, proxy‑failure logging, and activation outliers  
  - **Files**: `tests/unit/test_edge_cases.py` with three test functions (`test_entropy_clamping`, `test_proxy_failure_logging`, `test_activation_outlier_handling`).  
  - **Verification**:  
    ```bash
    pytest tests/unit/test_edge_cases.py -q
    # should report 3 passed
    ```

---

## Phase 14 – Security, path sanitization, and checksum validation

- [ ] T013 [US?] Harden all file‑path handling against traversal and verify integrity of downloaded assets; store checksums under `data/`  
  - **Changes**  
    * All path constructions use `pathlib.Path(...).resolve()` and raise `ValueError` if the resolved path is outside the project root.  
    * After each dataset or model download, compute SHA‑256 and append an entry to `data/checksums.json` (`{relative_path: checksum}`).  
    * Loader utilities (`code/models/loader.py`, `code/data/download_coco.py`) verify the checksum before loading; mismatches raise `RuntimeError`.  
    * Add `code/security/checksums.py` with `verify_checksum(path: str, expected: str) -> bool`.  
  - **Verification**:  
    ```bash
    # Simulate corruption
    echo "corrupt" >> data/raw/coco_captions.parquet
    python -c "from code.security.checksums import verify_checksum; import json; chk=json.load(open('data/checksums.json'))['data/raw/coco_captions.parquet']; assert not verify_checksum('data/raw/coco_captions.parquet', chk)"
    # Run the security unit test
    pytest tests/unit/test_security.py -q
    ```

---

### Dependency & execution order (critical path)

1. **T001** → **T002** → **T003** → **T004** → **T005** (gate) → **T006** → **T007** → **T008** → **T009** → **T010** → **T014** → **T011** → **T012** → **T013**  

All later phases are blocked until the preceding validation tasks (`T005`, `T007`) produce a `"status":"pass"` file in `data/processed/`.

*All tasks remain unchecked; the CI will automatically mark a task as completed only after the described artifact exists and the verification command succeeds.*  