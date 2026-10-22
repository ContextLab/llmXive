# Tasks: llmXive follow‑up – extending “OrbitQuant: Data‑Agnostic Quantization for Image and Video Diffusion T”

**Inputs**: `spec.md`, `plan.md`, `data‑model.md`, and the JSON schemas in `specs/001‑llmxive‑followup/`.  
All tasks are expressed as unchecked check‑boxes using the canonical  
`- [ ] T### [P?] [USx?] …` format. Indented continuation lines describe the required
artifact(s), verification command(s), and the scientific requirement(s) satisfied.

---

## Phase 1 – Project scaffolding & quick‑start

- [ ] T001 Establish project skeleton, list dependencies, and write a quick‑start guide  
  - **Artifacts**: `code/` (sub‑dirs `analysis/`, `models/`, `quantization/`, `evaluation/`, `utils/`), `tests/` (placeholder), `requirements.txt`, `code/config.py` (global seeds, path helpers via `llmxive_toolkit.paths`), `specs/001‑llmxive‑followup/quickstart.md` (command `python -m code.main --phase init`).  
  - **Verification**:  
    ```bash
    find code/ -type d | wc -l   # ≥ 8 directories
    python -c "import code.config"   # exits 0
    grep -c "torch" requirements.txt   # ≥ 1
    python -m code.main --phase init | grep "Initialization complete"
    ```

---

## Phase 2 – Data acquisition & prompt preparation

- [ ] T002 [P] Download the MS‑COCO 2017 validation captions, stream the images, and create a curated prompt table – all under `data/`  
  - **Steps**  
    1. `code/data/download_coco.py` → `data/raw/coco_captions.parquet` using the HuggingFace streaming API:  
       ```python
       from datasets import load_dataset
       ds = load_dataset("coco2017", split="validation", streaming=False)
       ds.to_parquet("data/raw/coco_captions.parquet")
       ```  
    2. `code/data/preprocess_coco.py` → `data/processed/prompts.csv` (`image_id,caption`). Must contain **≥ 400** rows.  
    3. `code/data/download_diverse_prompts.py` → `data/processed/diverse_prompts.csv` (`prompt_id,caption,source`). Must contain **≥ 150** rows and be sampled from at least two external public caption collections (e.g., `huggingface/datasets` “openimages” and “conceptual_captions”).  
    4. All scripts **must raise** on any download or I/O error; no synthetic fallback is permitted.  
  - **Requirements satisfied**: FR‑001 (semantic‑entropy input), FR‑002 (activation‑variance input), data‑hygiene rules.  
  - **Verification**:  
    ```bash
    wc -l data/processed/prompts.csv                # ≥ 400
    head -1 data/processed/diverse_prompts.csv      # header present
    wc -l data/processed/diverse_prompts.csv        # ≥ 150
    # Ensure scripts exit non‑zero on failure
    python - <<'PY'
    import subprocess, sys
    rc = subprocess.call(['python','code/data/download_coco.py'])
    sys.exit(rc)
    PY
    ```

- [ ] T003 Implement core modules (model loader, activation‑variance capture, semantic‑entropy proxy, W2A4 quantizer, static OrbitQuant baseline) and centralised logging under `data/processed/logs/`  
  - **Modules & artifacts**  
    * `code/models/loader.py` – `load_dit_model(name: str, device: str = "cpu")` (auto‑detects CUDA, falls back to CPU).  
    * `code/models/activation_capture.py` – `DiTActivationCapture.measure_variance(prompt: str) → dict[layer_name, variance]`.  
    * `code/analysis/entropy_proxy.py` – `compute_semantic_entropy(prompt: str, samples: int = 30) → float | None`. Returns `None` on proxy failure and logs to `data/processed/logs/proxy_failures.json`.  
    * `code/quantization/w2a4_engine.py` – `W2A4Quantizer.quantize(tensor, rotation_matrix=None)` AND `W2A4Quantizer.compute_mse(original, quantized) → float` (FR-009).  
    * `code/quantization/static_baseline.py` – `get_static_rotation_matrix(dim: int, seed: int = 42) → torch.Tensor`.  
    * `code/models/model_load_log.py` – writes events to `data/processed/logs/model_load_log.json`.  
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
    mse = quant.compute_mse(t, q_out)
    assert q_out.shape == t.shape and isinstance(mse, float)
    print("Core modules sanity‑check passed")
    PY
    ```

---

## Phase 0 – Correlation & Sensitivity Study (User Story 1)

- [ ] T004 [US1] Run the correlation pipeline on three DiT variants (Stable Diffusion 2.1, FLUX‑dev, Wan 2.1) and produce the required artifacts  
  - **Orchestration script**: `code/run_correlation.py`  
    1. Load `data/processed/diverse_prompts.csv`.  
    2. Compute semantic entropy for each prompt (30 Monte‑Carlo samples, fixed seed).  
    3. For each model, load via `loader.py` (GPU‑escape handled internally).  
    4. Capture per‑layer activation variance AND quantization MSE (FR-009) for a subset of activations.  
    5. Store per‑prompt variance and MSE JSON under `data/processed/activation_stats/`.  
    6. Write `entropy_scores.csv` (`prompt_id,entropy`).  
    7. **Statistical Analysis**:  
       - Pair prompts by nearest-neighbor entropy matching.  
       - Perform **paired t-tests** on variance differences between high- and low-entropy pairs (FR-010, SC-001).  
       - Compute **Spearman ρ** between entropy and activation variance (controlling for covariates).  
       - Compute **Spearman ρ** between activation variance and quantization MSE (FR-011).  
    8. Save a summary JSON `data/processed/correlation_results.json` with entries `{model_name, paired_t_stat, p_value, spearman_var_mse, n_prompts, layers_analyzed, entropy_range, variance_range}`.  
    9. Plot entropy vs. average variance (multi‑panel) → `figures/correlation_plot.png`.  
  - **Verification**:  
    ```bash
    python -c "import json, pathlib; p=pathlib.Path('data/processed/correlation_results.json'); assert p.is_file(); data=json.load(open(p)); assert 'paired_t_stat' in data[0]"
    python -c "import pandas as pd; df=pd.read_csv('data/processed/entropy_scores.csv'); assert not df.empty and 'entropy' in df.columns"
    file figures/correlation_plot.png | grep PNG
    ```

- [ ] T005 [US1] Validate that at least one model yields a statistically significant correlation (p < 0.05) and effect size (d ≥ 0.2) and write a gating file  
  - **Script**: `code/validation/validate_correlation.py` reads `correlation_results.json`; if any entry has `p_value < 0.05` AND `effect_size >= 0.2` it writes `data/processed/correlation_validated.json` with `{status:"pass", timestamp:"ISO‑8601", model:"<model_name>"}` otherwise `{status:"fail", reason:"no model met p < 0.05 or d ≥ 0.2"}` and exits non‑zero on failure.  
  - **Verification**:  
    ```bash
    cat data/processed/correlation_validated.json | grep '"status": "pass"'
    ```

---

## Phase 4 – Rotation‑matrix generation via entropy‑based clustering (User Story 2)

- [ ] T006 [US2] Perform K‑Means clustering on entropy scores, generate 16 orthogonal rotation matrices, and emit clustering artifacts  
  - **Implementation**: `code/analysis/clustering.py`  
    1. Load `entropy_scores.csv`.  
    2. Split prompts 80 %/20 % (seed = 42).  
    3. Run `sklearn.cluster.KMeans(n_clusters=16, random_state=42)` on the entropy vector → bin boundaries.  
    4. For each bin, aggregate activation‑histogram data from `data/processed/activation_stats/` and compute an orthogonal rotation matrix via SVD of the covariance matrix.  
    5. Save each matrix as `data/processed/rotation_matrices/matrix_{i}.npy` and its metadata as `data/processed/rotation_matrices/metadata_{i}.json`.  
    6. Assemble `data/processed/clustering_report.json` containing a list `matrices` that conforms to `rotation_matrix_schema`.  
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

- [ ] T007 [US2] Validate `clustering_report.json` against the JSON schema and orthogonality of each matrix; write validation artifact  
  - **Script**: `code/validation/validate_clustering.py` uses `jsonschema` to check conformity to `rotation_matrix_schema.schema.yaml` and verifies orthogonality (`Q, _ = np.linalg.qr(matrix); np.allclose(Q.T @ Q, np.eye(d), atol=1e-5)`). Writes `data/processed/clustering_validated.json` with `{status:"pass", timestamp:"…"} ` or detailed failure.  
  - **Verification**:  
    ```bash
    cat data/processed/clustering_validated.json | grep '"status": "pass"'
    ```

---

## Phase 5 – Entropy‑to‑rotation router implementation (User Story 2)

- [ ] T008 [US2] Implement `EntropyRouter` (lookup table + edge‑case handling) and integrate it into the quantizer  
  - **Components**  
    * `code/analysis/router.py` – class `EntropyRouter` with method `select_rotation_index(entropy: float) -> int` (clamps to 0‑15, logs out‑of‑range cases to `data/processed/logs/router_edge_cases.json`).  
    * Extend `code/quantization/w2a4_engine.py` – optional `router: EntropyRouter` argument; if provided, engine calls `router.select_rotation_index(entropy)` and loads the corresponding matrix via `load_matrices.py` before rotation.  
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

- [ ] T009 [US2] Load all 16 rotation matrices and verify orthogonality; write validation artifact  
  - **Function**: `code/analysis/load_matrices.py` → `load_rotation_matrices(report_path: str) -> List[np.ndarray]`. Raises `ValueError` on missing files, shape mismatches, or non‑orthogonal matrices.  
  - **Artifact**: `data/processed/matrices_validated.json` (`{status: "pass", count: 16, timestamp: "..."}`).  
  - **Verification**:  
    ```bash
    python - <<'PY'
    from code.analysis.load_matrices import load_rotation_matrices
    mats = load_rotation_matrices('data/processed/clustering_report.json')
    assert len(mats) == 16
    print("All matrices loaded and orthogonal")
    PY
    cat data/processed/matrices_validated.json | grep '"status": "pass"'
    ```

- [ ] T010 [US2] Run inference with the dynamic router on the held‑out test split and record matrix selections  
  - **Script**: `code/run_router_inference.py`  
    1. Load `data/processed/diverse_prompts.csv` (test split).  
    2. Compute entropy per prompt (entropy_proxy).  
    3. Load rotation matrices (via T009) and instantiate `EntropyRouter`.  
    4. For each prompt, select matrix index, run a forward pass with `W2A4Quantizer` using the selected matrix, and generate a low‑resolution PNG image.  
    5. Write `data/processed/router_selections.json` – list of `{prompt_id, entropy, selected_matrix_index}`.  
    6. Save example images (`data/processed/generated_images/`) for the first 5 prompts.  
  - **Verification**:  
    ```bash
    python -c "import json, pathlib; s=json.load(open('data/processed/router_selections.json')); assert len(s)>=100 and all(0<=r['selected_matrix_index']<=15 for r in s)"
    ls data/processed/generated_images/ | wc -l   # ≥ 5 PNG files
    ```

---

## Phase 6 – Full evaluation (User Story 3)

- [ ] T011 [US3] Execute baseline and dynamic pipelines, compute FID/CLIP/MSE/inference‑time, run paired statistical tests, and produce the final evaluation report and figures  
  - **Orchestration**: `code/run_evaluation.py`  
    1. **Baseline** – static rotation (`static_baseline.py`) → generate images for all test prompts; compute metrics → `baseline_evaluation.json`.  
    2. **Dynamic** – router‑driven inference (T010) → `dynamic_evaluation.json`.  
    3. **MSE Reduction Validation (FR-012)** – For each prompt in the test set, compute the MSE reduction: `(MSE_static - MSE_dynamic) / MSE_static`. Verify that the router-selected rotation significantly reduces MSE relative to the static baseline.  
    4. **Statistical tests** – `code/analysis/statistical_test.py` performs paired t‑tests (or Wilcoxon when normality fails) for each metric, applies Bonferroni correction, records p‑values.  
    5. **Runtime overhead** – compute average inference‑time difference; ensure ≤ 2 %.  
    6. Assemble `data/processed/final_evaluation_report.json` matching `results_schema` (includes `rotation_index` for dynamic rows) with fields: `baseline_mean_fid`, `dynamic_mean_fid`, `fid_improvement_percent`, `baseline_mean_time_ms`, `dynamic_mean_time_ms`, `overhead_percent`, `baseline_mean_mse`, `dynamic_mean_mse`, `mse_reduction_per_prompt`, `p_values` (keys `fid`, `clip`, `mse`, `time`), `entropy_sweep_fid_variance`, `conclusion`.  
    7. Generate plots under `figures/`: `fid_comparison.png`, `runtime_overhead.png`, `entropy_vs_fid.png`.  
  - **Verification**:  
    ```bash
    grep '"overhead_percent"' data/processed/final_evaluation_report.json | grep -E '"[0-9]+(\.[0-9]+)?"'   # value ≤ 2.0
    grep '"mse_reduction_per_prompt"' data/processed/final_evaluation_report.json
    grep '"p_values"' data/processed/final_evaluation_report.json
    grep '"entropy_sweep_fid_variance"' data/processed/final_evaluation_report.json
    grep '"conclusion"' data/processed/final_evaluation_report.json
    file figures/fid_comparison.png | grep PNG
    ```

- [ ] T012 Perform a ±5 % entropy‑cutoff sensitivity sweep on the router and record FID variance (SC‑005)  
  - **Script**: `code/analysis/entropy_sweep.py`  
    1. Load original entropy bin boundaries from `clustering_report.json`.  
    2. For each bin adjust lower/upper bounds by ±5 % of the total observed entropy range, creating three modified lookup tables per bin (total = 48 tables).  
    3. Run the full dynamic inference pipeline (as in T010) for each modified table, compute FID.  
    4. Compute variance of FID across all sweeps and store as a temporary artifact `data/processed/sweep_results.json`.  
  - **Verification**:  
    ```bash
    python -c "import json, pathlib; assert pathlib.Path('data/processed/sweep_results.json').is_file()"
    ```

---

## Phase 7 – Edge‑case unit tests & security hardening

- [ ] T013 [US2] Add pytest unit tests covering out‑of‑range entropy clamping, proxy‑failure logging, and activation‑outlier handling  
  - **Files**: `tests/unit/test_edge_cases.py` with three test functions (`test_entropy_clamping`, `test_proxy_failure_logging`, `test_activation_outlier_handling`).  
  - **Verification**:  
    ```bash
    pytest tests/unit/test_edge_cases.py -q   # should report 3 passed
    ```

- [ ] T014 Harden all file‑path handling against traversal and verify integrity of downloaded assets; store SHA‑256 checksums under `data/`  
  - **Changes**  
    * Use `pathlib.Path(...).resolve()` and raise `ValueError` if the resolved path lies outside the project root.  
    * After each dataset or model download, compute SHA‑256 and append an entry to `data/checksums.json` (`{relative_path: checksum}`).  
    * Loader utilities (`code/models/loader.py`, `code/data/download_coco.py`) verify the checksum before loading; mismatches raise `RuntimeError`.  
    * Add `code/security/checksums.py` with `verify_checksum(path: str, expected: str) -> bool`.  
  - **Verification**: (simulate corruption):  
    ```bash
    echo "corrupt" >> data/raw/coco_captions.parquet
    python - <<'PY'
    from code.security.checksums import verify_checksum
    import json
    chk = json.load(open('data/checksums.json'))['data/raw/coco_captions.parquet']
    assert not verify_checksum('data/raw/coco_captions.parquet', chk)
    print("Checksum detection works")
    PY
    pytest tests/unit/test_security.py -q
    ```

---

## Phase 8 – Dependency & execution order (critical path)

1. **T001** → **T002** → **T003** → **T004** → **T005** (gate) → **T006** → **T007** → **T008** → **T009** → **T010** → **T012** → **T011** → **T013** → **T014**  

All later phases are blocked until the preceding validation tasks (`T005`, `T007`) produce a `"status":"pass"` file in `data/processed/`.  

*All tasks remain unchecked; the CI will automatically mark a task as completed only after the described artifact exists and the verification command succeeds.*