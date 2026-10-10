# Tasks: llmXive follow-up: extending "OrbitQuant: Data-Agnostic Quantization for Image and Video Diffusion T"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by phase and user story to enable independent implementation and testing. Each task names its scientific requirement, concrete output, and observable check.

---

## Phase 1: Setup and Project Initialization

**Goal**: Establish project structure, dependencies, and basic infrastructure for all downstream work.

- [ ] T001 [P] Create project directory structure: Create directories `code/`, `code/data/`, `code/models/`, `code/analysis/`, `code/quantization/`, `code/evaluation/`, `code/validation/`, `code/runners/`, `data/raw/`, `data/processed/`, `state/`, `tests/unit/`, `tests/integration/` at repository root; create `__init__.py` in each Python package directory. **Deliverable**: Verify all directories exist and contain `__init__.py` files where appropriate using `find code/ -name '__init__.py' | wc -l` (should be ≥8). **Verification**: `ls -la code/` and `ls -la data/` show expected structure.

- [ ] T002 [P] Initialize Python dependencies and configuration: Create `requirements.txt` with `torch>=2.0`, `transformers>=4.35`, `diffusers>=0.24`, `datasets>=2.14`, `scikit-learn>=1.3`, `accelerate>=0.24`, `sentence-transformers>=2.2`, `peft>=0.6`, `numpy>=1.24`, `pandas>=2.0`, `scipy>=1.11`, `pillow>=10.0`; create `code/config.py` with hyperparameters (SEED=42, DEVICE="cpu", GPU_ESCAPE_HATCH=True, K=16), paths, and device detection logic; create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections. **Deliverable**: Verify `requirements.txt` exists and `code/config.py` can be imported without error (`python -c "from code.config import *"`). **Verification**: `cat code/config.py | grep -E "(SEED|K=16)"` confirms constants are defined.

- [ ] T003 [P] Implement GPU offload detection and escape hatch: Create `code/utils/gpu_offload.py` with a function `detect_gpu_requirement(error_log: str) -> bool` that returns True if the error message contains CUDA-related keywords (e.g., "CUDA out of memory", "cuda not available"), and a function `should_offload_to_kaggle() -> bool` that checks the GPU_ESCAPE_HATCH flag in config. This module is used by downstream tasks (T017, T046) to signal when a CPU run should be re-attempted on Kaggle's GPU runner. **Deliverable**: Verify `code/utils/gpu_offset.py` exists and both functions can be imported and called without error. **Verification**: `python -c "from code.utils.gpu_offload import detect_gpu_requirement, should_offload_to_kaggle; print(detect_gpu_requirement('CUDA out of memory'))"` returns True.

- [ ] T004 [P] Create quickstart documentation: Write `specs/001-llmxive-followup/quickstart.md` with a runnable command sequence (e.g., `pip install -r requirements.txt && python code/main.py --phase 1`) and expected output locations (`data/processed/prompts.csv`, `data/processed/correlation_results.json`). Include a brief description of input provenance (MS-COCO from HuggingFace, diverse prompts from `nlpconnect/vit-gpt2-image-captioning`). **Deliverable**: Verify `quickstart.md` exists and contains at least one runnable command with expected output paths. **Verification**: `grep -c "data/processed" specs/001-llmxive-followup/quickstart.md` returns ≥2.

---

## Phase 2: Data Acquisition and Foundational Infrastructure

**Goal**: Download real datasets, implement core model loaders and analysis infrastructure, and run the first end-to-end correlation analysis (User Story 1 MVP).

**CRITICAL**: T017 (Correlation) is the scientific gating task for all downstream work. It must complete and produce `data/processed/correlation_results.json` with p-value < 0.05 before Phase 4 (Router Implementation) can begin.

- [ ] T005 [P] Download MS-COCO validation set with captions: Implement `code/data/download_coco.py` using `datasets.load_dataset("nlpconnect/coco_captions", split="validation", streaming=False)` to fetch the full MS-COCO 2017 validation set (≈500 images with captions) to `data/raw/coco_captions/`. **CRITICAL**: Do NOT implement any fallback to synthetic data; if the HuggingFace fetch fails, the script must raise a RuntimeError with a clear message and exit with code 1. Log the exact dataset size and record the download timestamp in `state/download_log.json`. **Deliverable**: Verify `data/raw/coco_captions/` contains parquet files and `state/download_log.json` records the dataset size and timestamp. **Verification**: `ls -lh data/raw/coco_captions/` shows non-empty parquet files; `cat state/download_log.json | grep -E "(size|timestamp)"` confirms metadata.

- [ ] T006 [P] Extract MS-COCO captions as prompts: Implement `code/data/preprocess.py` to load the MS-COCO parquet from T005, extract the `caption` field from each record, and save to `data/processed/prompts.csv` with columns `[image_id, caption]`. Verify that the CSV has ≥400 non-empty caption rows. **Deliverable**: Verify `data/processed/prompts.csv` exists with correct columns and row count. **Verification**: `head -5 data/processed/prompts.csv` shows headers and sample data; `wc -l data/processed/prompts.csv` confirms ≥400 rows.

- [ ] T006d Download diverse text prompts from HuggingFace: Implement `code/data/download_diverse_prompts.py` to fetch prompts from `nlpconnect/vit-gpt2-image-captioning` dataset (validation split, ≈200 samples) using `datasets.load_dataset()`. Extract the `caption` field and save to `data/processed/diverse_prompts.csv` with columns `[prompt_id, caption, source]`. **CRITICAL**: Do NOT implement any fallback to synthetic data; if the HuggingFace fetch fails, raise RuntimeError and exit with code 1. **Deliverable**: Verify `data/processed/diverse_prompts.csv` exists with ≥150 non-empty caption rows and all three columns populated. **Verification**: `wc -l data/processed/diverse_prompts.csv` confirms ≥150 rows; `head -3 data/processed/diverse_prompts.csv` shows all columns filled; `grep -c "^" data/processed/diverse_prompts.csv` counts non-empty lines.

- [ ] T007 [P] Implement DiT model loader with GPU escape hatch: Create `code/models/flux_wan_loader.py` with function `load_dit_model(model_name: str, device: str = "cpu")` that attempts to load FLUX.1-dev or Wan 2.1 from HuggingFace (GPU path: `device="cuda"`, `load_in_8bit=True` for memory efficiency); if CUDA fails, fall back to Stable Diffusion 2.1 on CPU. Log the selected model and device to `state/model_load_log.json`. **Deliverable**: Verify the function can be called and returns a valid model object; `state/model_load_log.json` records the selected model and device. **Verification**: `python -c "from code.models.flux_wan_loader import load_dit_model; m = load_dit_model('flux'); print(type(m))"` succeeds; `cat state/model_load_log.json | grep device` shows the device used.

- [ ] T008 [P] Implement activation variance measurement hooks: Create `code/models/dit_wrapper.py` with class `DiTActivationCapture` that wraps a DiT model and injects hooks into intermediate layers to capture float32 activation tensors during the **text-to-image generation trajectory** (forward pass conditioned on a text prompt). Implement method `measure_activation_variance(prompt: str, num_steps: int = 50) -> dict` that returns `{layer_name: variance}` for all hooked layers. Store raw activation histograms (binned into 100 bins) in the returned dict. **Deliverable**: Verify the class can be instantiated and the method returns a dict with layer names as keys and numeric variance values. **Verification**: `python -c "from code.models.dit_wrapper import DiTActivationCapture; print('OK')"` succeeds; test that variance values are positive floats.

- [ ] T009 [P] Implement lightweight semantic entropy proxy: Create `code/analysis/entropy_proxy.py` with function `compute_semantic_entropy(prompt: str, num_samples: int = 5, model_name: str = "distilbert-base-uncased") -> float` that uses a small transformer (DistilBERT or similar, <100M parameters) to generate multiple paraphrases of the input prompt via sampling, cluster the embeddings, and compute entropy as `-sum(p_i * log(p_i))` where `p_i` is the proportion of samples in cluster `i`. **Edge case handling**: If the lightweight LLM proxy times out or fails, log the error and return a sentinel value (e.g., `None`); the calling code (T017) will handle the fallback. **Deliverable**: Verify the function can be called on a sample prompt and returns a float in [0, 10]. **Verification**: `python -c "from code.analysis.entropy_proxy import compute_semantic_entropy; e = compute_semantic_entropy('a simple prompt'); print(type(e), 0 <= e <= 10)"` succeeds.

- [ ] T010 [P] Implement W2A4 quantization engine: Create `code/quantization/w2a4_engine.py` with class `W2A4Quantizer` that implements weight-2-bit, activation-4-bit quantization. Include method `quantize_activation(activation: torch.Tensor, rotation_matrix: torch.Tensor = None) -> torch.Tensor` that optionally applies a rotation matrix before quantization. Store quantization parameters (scale, zero-point) for later analysis. **Deliverable**: Verify the class can be instantiated and the quantize_activation method accepts a tensor and optional rotation matrix. **Verification**: `python -c "from code.quantization.w2a4_engine import W2A4Quantizer; q = W2A4Quantizer(); print('OK')"` succeeds.

- [ ] T011 [P] Implement static OrbitQuant baseline: Create `code/quantization/static_baseline.py` with function `get_static_rotation_matrix(dim: int, seed: int = 42) -> torch.Tensor` that generates a single fixed rotation matrix (the original OrbitQuant RPBH basis) for the given activation dimension. This is used as the baseline for comparison in T036. **Deliverable**: Verify the function returns an orthogonal matrix (QR decomposition check: `Q @ Q.T ≈ I`). **Verification**: `python -c "from code.quantization.static_baseline import get_static_rotation_matrix; M = get_static_rotation_matrix(768); print((M @ M.T).diag().mean())"` returns ≈1.0 (diagonal of identity).

- [ ] T017 [US1] Run end-to-end correlation analysis (MVP): Implement `code/run_correlation.py` orchestration script that executes the following pipeline:
  1. Load prompts from `data/processed/diverse_prompts.csv` (from T006d).
  2. For each prompt, compute semantic entropy using `code/analysis/entropy_proxy.py` (T009); if proxy fails, log the error and skip the prompt.
  3. Load the DiT model using `code/models/flux_wan_loader.py` (T007).
  4. Run a **text-to-image generation pass** conditioned on the prompt (using the caption as the sole conditioning input) to generate intermediate activations.
  5. Capture activation variance using `code/models/dit_wrapper.py` (T008) for all hooked layers.
  6. Aggregate entropy and variance across all valid prompts; compute Pearson correlation coefficient and p-value using `scipy.stats.pearsonr()`.
  7. Save results to `data/processed/correlation_results.json` with schema: `{correlation: float, p_value: float, n_prompts: int, layers_analyzed: [str], entropy_range: [min, max], variance_range: [min, max]}`.
  8. Log the exact command used, random seeds, and timestamps to `state/correlation_log.json`.
  
  **CRITICAL**: This task is the primary scientific hypothesis test. It MUST complete and produce valid results before Phase 4 (Router Implementation) can begin. **Deliverable**: Verify `data/processed/correlation_results.json` exists and contains all required fields with valid numeric values. **Verification**: `python -c "import json; r = json.load(open('data/processed/correlation_results.json')); print('p_value:', r['p_value'], 'n:', r['n_prompts'])"` succeeds and p_value is in [0, 1].

- [ ] T023b [P] Validate correlation hypothesis (gating check): Implement `code/validation/validate_correlation.py` to verify that `data/processed/correlation_results.json` exists and contains a p-value < 0.05. If validation passes, write `state/correlation_validated.json` with `{status: "pass", timestamp: ...}`; if it fails, write `{status: "fail", reason: "p_value >= 0.05"}` and halt further execution. **Deliverable**: Verify that the script runs without error and produces `state/correlation_validated.json` with a status field. **Verification**: `cat state/correlation_validated.json | grep status` shows "pass" or "fail".

**Checkpoint**: Correlation hypothesis tested. If T023b passes (p < 0.05), proceed to Phase 4 (Router Implementation). If not, the project may pivot or stop.

---

## Phase 3: Unit Tests for Core Modules

**Goal**: Implement focused correctness tests for entropy, variance measurement, and quantization logic before integration.

- [ ] T012 [P] [US1] Unit test for semantic entropy calculation: Create `tests/unit/test_entropy.py` with test cases:
  - Test that `compute_semantic_entropy()` returns a float in [0, 10] for valid prompts.
  - Test that two identical prompts return the same entropy (determinism with fixed seed).
  - Test that a longer/more complex prompt returns higher entropy than a simple prompt.
  - Test that the function handles timeout gracefully (returns None or raises ValueError).
  
  **Deliverable**: Verify `tests/unit/test_entropy.py` exists and `pytest tests/unit/test_entropy.py` passes with ≥3 passing assertions. **Verification**: `pytest tests/unit/test_entropy.py -v` shows "PASSED" for all test cases.

- [ ] T013 [P] [US1] Unit test for activation variance measurement: Create `tests/unit/test_activation_variance.py` with test cases:
  - Test that `DiTActivationCapture.measure_activation_variance()` returns a dict with layer names as keys.
  - Test that variance values are positive floats.
  - Test that the histogram_bins field is a list of non-negative numbers summing to approximately the number of samples.
  
  **Deliverable**: Verify `tests/unit/test_activation_variance.py` exists and `pytest tests/unit/test_activation_variance.py` passes. **Verification**: `pytest tests/unit/test_activation_variance.py -v` shows "PASSED" for all assertions.

- [ ] T030 [P] [US3] Unit test for metric calculation: Create `tests/unit/test_metrics.py` with test cases:
  - Test that `compute_fid()` returns a non-negative float.
  - Test that `compute_clip_score()` returns a float in [0, 1].
  - Test that `compute_mse()` returns a non-negative float.
  
  **Deliverable**: Verify `tests/unit/test_metrics.py` exists and `pytest tests/unit/test_metrics.py` passes. **Verification**: `pytest tests/unit/test_metrics.py -v` shows "PASSED" for all assertions.

---

## Phase 4: Router Implementation and Clustering (Conditional on T023b)

**Goal**: Implement the dynamic rotation router and derive the 16 pre-optimized rotation matrices from the correlation data.

**CRITICAL**: This phase ONLY begins if T023b passes (p < 0.05). If T023b fails, these tasks are skipped and the project uses the static baseline.

- [ ] T022 [P] [US2] Derive rotation matrices from entropy-based clustering: Implement `code/analysis/clustering.py` that:
  1. Loads the correlation data from `data/processed/correlation_results.json` (T017) to extract the entropy values for all valid prompts.
  2. Splits the prompts into a **train split** (80%) and **test split** (20%) using a fixed random seed.
  3. On the train split, performs K-Means clustering (K=16) on the entropy values to create 16 entropy bins.
  4. For each bin, collects the activation variance histograms from the corresponding prompts and computes the centroid of the histogram distribution in the activation space.
  5. Derives a rotation matrix for each bin (e.g., via SVD on the covariance of the activation histograms) and saves as `.npy` files in `data/processed/rotation_matrices/matrix_0.npy`, `matrix_1.npy`, ..., `matrix_15.npy`.
  6. Generates `data/processed/clustering_report.json` with schema: `{layers_used: [str], dataset_split: {train_count: int, test_count: int}, entropy_bins: [{min: float, max: float, matrix_index: int}], matrices: [{cluster_id: int, entropy_range_min: float, entropy_range_max: float, matrix_shape: [int, int], matrix_data_ref: str, derived_from_split: "train"}]}`.
  
  **Deliverable**: Verify that `data/processed/rotation_matrices/` contains 16 `.npy` files and `data/processed/clustering_report.json` exists with all required fields and valid structure. **Verification**: `ls data/processed/rotation_matrices/ | wc -l` returns 16; `python -c "import json; r = json.load(open('data/processed/clustering_report.json')); print('matrices:', len(r['matrices']))"` returns 16.

- [ ] T022c [P] [US2] Generate quantized activations using derived matrices: Implement `code/run_quantization_validation.py` that:
  1. Loads the test split prompts from T022.
  2. For each prompt, loads the corresponding rotation matrix from `data/processed/rotation_matrices/`.
  3. Runs a generation pass to capture activations (using T008).
  4. Applies the rotation matrix and W2A4 quantization (T010) to the activations.
  5. Saves the quantized activation tensors and metadata to `data/processed/quantized_activations.json` with schema: `[{prompt_id: str, layer_name: str, quantized_values: [float], rotation_index: int}]`.
  
  **Deliverable**: Verify `data/processed/quantized_activations.json` exists and contains ≥100 records with all required fields. **Verification**: `python -c "import json; r = json.load(open('data/processed/quantized_activations.json')); print('records:', len(r))"` returns ≥100.

- [ ] T019 [US2] Compute MSE quantization error: Implement `code/analysis/mse_validator.py` with function `compute_quantization_mse(float32_activations: torch.Tensor, quantized_activations: torch.Tensor) -> float` that computes Mean Squared Error between the original float32 activations and the quantized versions. Run this on the quantized activations from T022c and save results to `data/processed/mse_results.json` with schema: `{mean_mse: float, std_mse: float, mse_by_layer: {layer_name: float}}`. **Deliverable**: Verify `data/processed/mse_results.json` exists with numeric MSE values. **Verification**: `python -c "import json; r = json.load(open('data/processed/mse_results.json')); print('mean_mse:', r['mean_mse'])"` returns a positive float.

- [ ] T024 [P] [US2] Implement dynamic router lookup logic: Create `code/analysis/router.py` with class `EntropyRouter` that:
  1. Loads the entropy bins from `data/processed/clustering_report.json`.
  2. Implements method `select_rotation_index(entropy_score: float) -> int` that maps an entropy score to the corresponding matrix index (0-15).
  3. Handles edge cases: if entropy is out-of-range, clamp to the nearest boundary (index 0 or 15).
  4. Logs out-of-range occurrences to `state/router_edge_cases.json` for audit.
  
  **Deliverable**: Verify the class can be instantiated and the method returns an integer in [0, 15] for any input entropy. **Verification**: `python -c "from code.analysis.router import EntropyRouter; r = EntropyRouter(); idx = r.select_rotation_index(5.5); print(0 <= idx <= 15)"` returns True.

- [ ] T025 [US2] Integrate router into W2A4 quantization engine: Update `code/quantization/w2a4_engine.py` to:
  1. Accept an `EntropyRouter` instance in the constructor.
  2. Modify the `quantize_activation()` method to optionally use the router to select a rotation matrix based on an entropy score passed as a parameter.
  3. Apply the selected rotation matrix (or the static baseline if router is None) before quantization.
  
  **Deliverable**: Verify that `W2A4Quantizer` can be instantiated with a router and the quantize_activation method accepts an entropy parameter. **Verification**: `python -c "from code.quantization.w2a4_engine import W2A4Quantizer; q = W2A4Quantizer(router=None); print('OK')"` succeeds.

- [ ] T028 [US2] Implement matrix loader and validator: Create `code/analysis/load_matrices.py` with function `load_rotation_matrices(clustering_report_path: str) -> list[torch.Tensor]` that:
  1. Loads `data/processed/clustering_report.json`.
  2. Verifies that all required keys are present (layers_used, dataset_split, entropy_bins, matrices).
  3. Loads each rotation matrix from the file paths specified in `matrices[*].matrix_data_ref`.
  4. Validates that each matrix is orthogonal (QR check: `Q @ Q.T ≈ I`) and has unit norm.
  5. Returns a list of 16 matrices in order.
  6. Raises ValueError if any matrix is missing, non-orthogonal, or has incorrect shape.
  
  **Deliverable**: Verify the function can be called and returns a list of 16 torch.Tensor objects. **Verification**: `python -c "from code.analysis.load_matrices import load_rotation_matrices; mats = load_rotation_matrices('data/processed/clustering_report.json'); print(len(mats))"` returns 16.

- [ ] T029 [US2] Implement router inference orchestration: Create `code/run_router_inference.py` that:
  1. Loads test split prompts from T022.
  2. Computes entropy for each prompt (T009).
  3. Loads rotation matrices using T028.
  4. Selects the appropriate matrix using the router (T024).
  5. Runs generation with the selected rotation applied (T025).
  6. Logs the selected matrix index and entropy score for each prompt to `data/processed/router_selections.json` with schema: `[{prompt_id: str, entropy: float, selected_matrix_index: int}]`.
  
  **Deliverable**: Verify `data/processed/router_selections.json` exists and contains ≥100 records. **Verification**: `python -c "import json; r = json.load(open('data/processed/router_selections.json')); print('records:', len(r))"` returns ≥100.

---

## Phase 5: Router Testing and Sensitivity Analysis

**Goal**: Validate router correctness and robustness to entropy threshold variations.

- [ ] T020 [P] [US2] Unit test for router lookup logic: Create `tests/unit/test_router.py` with test cases:
  - Test that `EntropyRouter.select_rotation_index()` returns an integer in [0, 15] for any entropy value.
  - Test that clamping works: entropy < min returns 0, entropy > max returns 15.
  - Test that the same entropy consistently returns the same index (determinism).
  
  **Deliverable**: Verify `tests/unit/test_router.py` exists and `pytest tests/unit/test_router.py` passes. **Verification**: `pytest tests/unit/test_router.py -v` shows "PASSED" for all assertions.

- [ ] T021 [P] [US2] Integration test for rotation application: Create `tests/integration/test_rotation_application.py` that:
  - Tests that applying a rotation matrix to activations followed by quantization produces a valid quantized tensor.
  - Tests that the static baseline and dynamic router paths both produce quantized outputs with the same shape.
  
  **Deliverable**: Verify `tests/integration/test_rotation_application.py` exists and `pytest tests/integration/test_rotation_application.py` passes. **Verification**: `pytest tests/integration/test_rotation_application.py -v` shows "PASSED".

- [ ] T035 [US3] Sensitivity analysis on entropy thresholds: Implement `code/analysis/sensitivity.py` that:
  1. Loads the clustering report from T022.
  2. Sweeps the entropy bin boundaries by ±5% of the total observed entropy range (from T017).
  3. For each swept configuration, re-runs the router on the test split and records the FID score (from T032).
  4. Saves results to `data/processed/sensitivity_analysis.json` with schema: `{sweep_range: [min_percent, max_percent], fid_variance: float, fid_by_sweep: {percent: float}}`.
  
  **Deliverable**: Verify `data/processed/sensitivity_analysis.json` exists with numeric FID variance values. **Verification**: `python -c "import json; r = json.load(open('data/processed/sensitivity_analysis.json')); print('variance:', r['fid_variance'])"` returns a positive float.

---

## Phase 6: Evaluation and Comparison

**Goal**: Generate images using both static baseline and dynamic router, compute perceptual metrics, and perform statistical testing.

- [ ] T032 [US3] Implement perceptual metric calculators: Create `code/evaluation/metrics.py` with functions:
  - `compute_fid(generated_images: list[PIL.Image], reference_images: list[PIL.Image]) -> float`: Compute Fréchet Inception Distance using a CPU-compatible implementation (e.g., `pytorch-fid` with InceptionV3).
  - `compute_clip_score(generated_images: list[PIL.Image], prompts: list[str]) -> float`: Compute CLIP similarity score using `clip-score` library.
  - `compute_mse(float32_tensor: torch.Tensor, quantized_tensor: torch.Tensor) -> float`: Compute Mean Squared Error.
  
  **Deliverable**: Verify all three functions can be imported and called without error. **Verification**: `python -c "from code.evaluation.metrics import compute_fid, compute_clip_score, compute_mse; print('OK')"` succeeds.

- [ ] T033 [P] [US3] Implement wall-clock timing: Create `code/evaluation/timing.py` with function `measure_inference_time(model, prompt: str, num_runs: int = 5) -> float` that:
  1. Runs the model inference on the given prompt `num_runs` times.
  2. Records the wall-clock time for each run (excluding the first warm-up run).
  3. Returns the mean inference time in milliseconds.
  
  **Deliverable**: Verify the function returns a positive float. **Verification**: `python -c "from code.evaluation.timing import measure_inference_time; t = measure_inference_time(model, 'test'); print(t > 0)"` returns True.

- [ ] T034 [US3] Implement statistical testing: Create `code/analysis/statistical_test.py` with function `paired_ttest_with_correction(baseline_metrics: list[float], dynamic_metrics: list[float], apply_bonferroni: bool = True) -> dict` that:
  1. Performs a paired t-test using `scipy.stats.ttest_rel()`.
  2. If `apply_bonferroni=True` and the number of comparisons > 3, applies Bonferroni correction (divide alpha by number of comparisons).
  3. Returns `{t_statistic: float, p_value: float, mean_diff: float, significant: bool}`.
  
  **Deliverable**: Verify the function returns a dict with all required fields. **Verification**: `python -c "from code.analysis.statistical_test import paired_ttest_with_correction; r = paired_ttest_with_correction([1,2,3], [1.1,2.1,3.1]); print('p_value' in r)"` returns True.

- [ ] T036 [US3] Run full evaluation pipeline: Implement `code/run_evaluation.py` orchestration script that:
  1. Loads test split prompts from T022.
  2. Runs inference with the **static baseline** (T011) on all test prompts; generate images and measure FID, CLIP, MSE, and inference time for each prompt. Save results to `data/processed/baseline_evaluation.json` with schema: `[{prompt_id: str, fid: float, clip_score: float, mse: float, inference_time_ms: float}]`.
  3. Runs inference with the **dynamic router** (T029) on the same test prompts; save results to `data/processed/dynamic_evaluation.json` with the same schema plus `rotation_index: int`.
  4. Computes paired t-tests (T034) comparing FID, CLIP, MSE, and inference time between the two methods; save p-values to `data/processed/statistical_tests.json` with schema: `{fid_pvalue: float, clip_pvalue: float, mse_pvalue: float, time_pvalue: float, significant_metrics: [str]}`.
  5. Computes the mean inference time overhead: `overhead_percent = 100 * (dynamic_mean_time - baseline_mean_time) / baseline_mean_time`; save to `data/processed/final_evaluation_report.json` with schema: `{baseline_mean_fid: float, dynamic_mean_fid: float, fid_improvement_percent: float, baseline_mean_time_ms: float, dynamic_mean_time_ms: float, overhead_percent: float, p_values: {...}, conclusion: str}`.
  
  **Deliverable**: Verify that all four output files exist and contain valid numeric values. **Verification**: `ls data/processed/ | grep -E "(baseline|dynamic|statistical|final)" | wc -l` returns 4; `python -c "import json; r = json.load(open('data/processed/final_evaluation_report.json')); print('overhead:', r['overhead_percent'])"` returns a numeric value.

- [ ] T031 [P] [US3] Integration test for end-to-end pipeline: Create `tests/integration/test_full_pipeline.py` that:
  - Tests that the full pipeline (correlation → clustering → router → evaluation) produces valid outputs at each stage.
  - Tests that the final evaluation report contains all required fields.
  
  **Deliverable**: Verify `tests/integration/test_full_pipeline.py` exists and `pytest tests/integration/test_full_pipeline.py` passes. **Verification**: `pytest tests/integration/test_full_pipeline.py -v` shows "PASSED".

---

## Phase 7: Robustness and Edge Case Handling

**Goal**: Address reviewer concerns regarding data hygiene, error handling, and runtime efficiency.

- [ ] T042 [P] Enforce fail-loud data loading: Refactor `code/data/download_diverse_prompts.py` to:
  1. Remove any `try/except` blocks that silently fall back to synthetic data.
  2. If the HuggingFace dataset fetch fails (HTTP 404, TimeoutError, EmptyDatasetError), raise a RuntimeError with a message like "Failed to fetch diverse prompts from HuggingFace: {error}".
  3. Let the error propagate so the execution stage can retry with a verified real data source.
  
  **Deliverable**: Verify that the script raises an error (not returns synthetic data) when the fetch fails. **Verification**: Manually test with an invalid dataset name and confirm RuntimeError is raised.

- [ ] T043 [P] Implement proxy failure fallback: Refactor `code/analysis/entropy_proxy.py` to:
  1. Wrap the lightweight LLM inference in a try-except block.
  2. If the proxy times out or raises an error, log the failure to `state/proxy_failures.json` with `{prompt_id: str, error: str, timestamp: ...}`.
  3. Return `None` to signal failure; the calling code (T017) will skip this prompt or use a fallback entropy value (e.g., median entropy from previous runs).
  4. Do NOT fabricate or substitute synthetic entropy values.
  
  **Deliverable**: Verify that `state/proxy_failures.json` is created and populated when the proxy fails. **Verification**: Manually trigger a proxy timeout and confirm the failure is logged.

- [ ] T044 [P] Implement streaming for large datasets: Refactor `code/analysis/correlation.py` to:
  1. Process the MS-COCO dataset in chunks of 50 prompts.
  2. For each chunk, compute entropy, run generation, capture variance, and accumulate statistics online (running mean, running variance).
  3. Log chunk processing progress to `state/correlation_progress.json` with `{chunks_processed: int, total_chunks: int, current_correlation: float}`.
  4. Ensure memory usage stays below 2GB (verify with `psutil.Process().memory_info().rss`).
  
  **Deliverable**: Verify that the script processes chunks and memory usage remains below 2GB. **Verification**: `cat state/correlation_progress.json | tail -1` shows final chunk count; run with `memory_profiler` to confirm peak memory < 2GB.

- [ ] T045 [P] Validate rotation matrix orthogonality: Refactor `code/analysis/load_matrices.py` to add validation checks:
  1. For each loaded rotation matrix, compute `Q @ Q.T` and verify that the diagonal is ≈1.0 and off-diagonals are ≈0.0 (orthogonality check).
  2. Compute the L2 norm and verify it is ≈1.0 (unit norm check).
  3. If any matrix fails validation, raise ValueError with details.
  
  **Deliverable**: Verify that invalid matrices are rejected. **Verification**: Manually create a non-orthogonal matrix and confirm ValueError is raised when loading.

---

## Phase 8: GPU Execution and Scaling

**Goal**: Validate GPU offload path and ensure scaled-down computation fits Kaggle's free GPU constraints.

- [ ] T046 [P] Validate GPU offload detection and escape hatch: Implement `code/run_gpu_validation.py` that:
  1. Attempts to load FLUX.1-dev with `device="cuda"` and `load_in_8bit=True` on a small batch (5 prompts).
  2. If CUDA fails (catches RuntimeError with "CUDA" in message), logs the failure to `state/gpu_validation_log.json` with `{status: "cpu_fallback", device: "cpu", model: "flux"}`.
  3. If CUDA succeeds, logs `{status: "gpu_success", device: "cuda", model: "flux", vram_used_gb: float}`.
  4. The execution stage uses this log to decide whether to re-run the CPU task on Kaggle's GPU runner.
  
  **Deliverable**: Verify `state/gpu_validation_log.json` exists and contains a status field. **Verification**: `cat state/gpu_validation_log.json | grep status` shows "gpu_success" or "cpu_fallback".

- [ ] T047 [P] Implement scaled GPU execution mode: Refactor `code/analysis/entropy_proxy.py` to accept command-line arguments:
  1. `--sample-size=N`: Number of paraphrase samples per prompt (default 5 for GPU, can be higher for CPU).
  2. `--prompt-count=M`: Number of prompts to process (default 200 for GPU, can be higher for CPU).
  3. Log the exact counts used to `state/execution_config.json` with `{sample_size: int, prompt_count: int, mode: "gpu" | "cpu"}`.
  4. Ensure total VRAM usage on Kaggle GPU (16GB) stays below 12GB by using 8-bit quantization and small batch sizes.
  
  **Deliverable**: Verify that the script accepts these arguments and logs them. **Verification**: `python code/analysis/entropy_proxy.py --sample-size=5 --prompt-count=200` and check `state/execution_config.json`.

- [ ] T048 [P] Implement chunk-based processing for correlation: Refactor `code/analysis/correlation.py` to:
  1. Process MS-COCO in chunks of 50 prompts (adjustable via `--chunk-size` argument).
  2. Use a generator pattern to load and process one chunk at a time, accumulating statistics without holding the full batch in memory.
  3. Log "Chunk processed: X/Y" for each batch to stdout and `state/correlation_progress.json`.
  4. Ensure memory footprint stays below 2GB on CPU and 12GB on GPU.
  
  **Deliverable**: Verify that chunks are processed and memory usage is logged. **Verification**: `cat state/correlation_progress.json | grep "Chunk"` shows progress messages.

---

## Phase 9: Documentation and Reproducibility

**Goal**: Document the methods, results, and reproduce the full workflow from declared inputs.

- [ ] T037 [P] Refactor runners into modular structure: Consolidate `code/run_correlation.py`, `code/run_router_inference.py`, and `code/run_evaluation.py` into a modular runner framework:
  1. Create `code/runners/base_runner.py` with abstract `BaseRunner` class.
  2. Implement `code/runners/correlation_runner.py`, `code/runners/router_runner.py`, `code/runners/evaluation_runner.py` as concrete subclasses.
  3. Create `code/main.py` that orchestrates all runners in sequence: `python code/main.py --phase 1-3` runs all phases.
  4. Update `specs/001-llmxive-followup/quickstart.md` with the new command.
  
  **Deliverable**: Verify that `code/main.py` can be called and executes the full pipeline. **Verification**: `python code/main.py --phase 1-3 --help` shows usage; `python code/main.py --phase 1` completes without error.

- [ ] T038 [P] Implement memory-efficient streaming: Refactor `code/data/download_coco.py` to:
  1. Use `datasets.load_dataset(..., streaming=False)` but process in chunks to avoid holding the entire dataset in memory.
  2. Implement a generator that yields batches of 50 images at a time.
  3. Verify peak memory usage < 2GB with `memory_profiler`.
  4. Add a benchmark script `tests/unit/test_memory.py` that runs the generator and logs peak memory.
  
  **Deliverable**: Verify `tests/unit/test_memory.py` runs and confirms memory < 2GB. **Verification**: `pytest tests/unit/test_memory.py -v` shows "PASSED" and memory log is generated.

- [ ] T039 [P] Add unit tests for edge cases: Create `tests/unit/test_edge_cases.py` with test cases:
  - Test that entropy out-of-range is clamped correctly (entropy < min → index 0, entropy > max → index 15).
  - Test that proxy failure is logged and fallback is applied (median rotation index is used).
  - Test that activation outliers are handled gracefully (logged to `state/outlier_log.json`, default to median).
  
  **Deliverable**: Verify `tests/unit/test_edge_cases.py` exists and `pytest tests/unit/test_edge_cases.py` passes. **Verification**: `pytest tests/unit/test_edge_cases.py -v` shows "PASSED" for all assertions.

- [ ] T040 [P] Implement security and validation hardening: Add to `code/config.py` and `code/data/download_coco.py`:
  1. Sanitize file paths in data loading: use `pathlib.Path` and reject paths with `..` or absolute paths.
  2. Validate model checksums against `state/artifact_hashes.json` before loading; raise error on mismatch.
  3. Create `state/artifact_hashes.json` with SHA-256 hashes of all downloaded files and model weights.
  4. Update hashes after every run.
  
  **Deliverable**: Verify that `state/artifact_hashes.json` is created and checksums are validated. **Verification**: `cat state/artifact_hashes.json | head -3` shows hash entries; manually corrupt a file and confirm checksum validation fails.

- [ ] T049 Write methods and results documentation: Create `specs/001-llmxive-followup/methods_and_results.md` that:
  1. Describes the correlation analysis methodology (entropy computation, variance measurement, Pearson r test).
  2. Reports the correlation coefficient, p-value, and effect size from T017.
  3. Describes the clustering and rotation matrix derivation (T022).
  4. Reports the FID, CLIP, MSE, and runtime metrics from T036 with error bars and statistical significance.
  5. Includes figures: scatter plot of entropy vs. variance (from T017), FID improvement bar chart (from T036), sensitivity analysis curve (from T035).
  6. Discusses limitations (e.g., limited dataset size, proxy approximation, generalization to other models).
  
  **Deliverable**: Verify `methods_and_results.md` exists and contains all required sections and figures. **Verification**: `grep -c "^#" specs/001-llmxive-followup/methods_and_results.md` returns ≥5 (sections); `ls data/processed/*.png | wc -l` returns ≥3 (figures).

- [ ] T050 Validate reproducibility and generate final report: Implement `code/run_full_reproducibility_check.py` that:
  1. Re-runs the entire pipeline from T001 through T036 using the documented inputs and seeds.
  2. Verifies that all output files match the expected schema and contain valid numeric values.
  3. Compares the final metrics against a baseline (saved from the first successful run).
  4. Generates `state/reproducibility_report.json` with `{status: "pass" | "fail", all_artifacts_present: bool, schema_validation: bool, metric_stability: bool, timestamp: ...}`.
  
  **Deliverable**: Verify `state/reproducibility_report.json` exists and shows status "pass". **Verification**: `cat state/reproducibility_report.json | grep status` shows "pass"; `cat state/reproducibility_report.json | grep metric_stability` shows true.

---

## Dependencies and Execution Order

### Critical Path (Blocking Sequence)

1. **Phase 1 (Setup)**: T001, T002, T003, T004 — Must complete before any other phase.
2. **Phase 2 (Data & Foundational)**: T005, T006, T006d, T007, T008, T009, T010, T011, T017 — Must complete in order; T017 is the gating task.
3. **Phase 2.5 (Validation Gate)**: T023b — Must pass (p < 0.05) before Phase 4 can begin.
4. **Phase 4 (Router)**: T022, T022c, T019, T024, T025, T028, T029 — Conditional on T023b passing; depends on T017 results.
5. **Phase 5 (Testing)**: T020, T021, T035 — Depends on Phase 4 completion.
6. **Phase 6 (Evaluation)**: T032, T033, T034, T036 — Depends on Phase 5 completion.
7. **Phase 7 (Robustness)**: T042, T043, T044, T045 — Can run in parallel with Phase 6.
8. **Phase 8 (GPU)**: T046, T047, T048 — Can run in parallel with Phase 7; T046 is independent of T022.
9. **Phase 9 (Documentation)**: T037, T038, T039, T040, T049, T050 — Depends on Phase 6 completion.

### Parallel Opportunities

- **Phase 1**: All tasks [P] can run in parallel.
- **Phase 2 (Foundational)**: T005, T006, T006d, T007, T008, T009, T010, T011 can run in parallel; T017 depends on all of them.
- **Phase 3 (Tests)**: T012, T013, T030 can run in parallel.
- **Phase 4 (Router)**: T022, T022c, T019 are sequential; T024, T025, T028, T029 depend on earlier tasks but can overlap.
- **Phase 5 (Testing)**: T020, T021, T035 can run in parallel.
- **Phase 6 (Evaluation)**: T032, T033, T034 can run in parallel; T036 depends on all of them.
- **Phase 7 (Robustness)**: T042, T043, T044, T045 can run in parallel.
- **Phase 8 (GPU)**: T046, T047, T048 can run in parallel.
- **Phase 9 (Documentation)**: T037, T038, T039, T040 can run in parallel; T049, T050 depend on Phase 6.

### User Story Dependencies

- **User Story 1 (P1)**: Implemented by T017 (Phase 2). Must succeed (p < 0.05) before US2 can begin.
- **User Story 2 (P2)**: Implemented by T022–T029 (Phase 4). Depends on US1 success (T023b).
- **User Story 3 (P3)**: Implemented by T032–T036 (Phase 6). Depends on US2 completion.

---

## Checkpoint and Gating

**After Phase 2 (Foundational)**: T017 produces `data/processed/correlation_results.json`. If p-value < 0.05, proceed to Phase 4. If p-value ≥ 0.05, the project may pivot or stop.

**After Phase 4 (Router)**: T029 produces `data/processed/router_selections.json`. Verify that 16 rotation matrices are correctly selected and applied.

**After Phase 6 (Evaluation)**: T036 produces `data/processed/final_evaluation_report.json`. Verify that the dynamic router overhead is ≤ 2% and FID/CLIP improvements are statistically significant (p < 0.05).

**After Phase 9 (Documentation)**: T050 produces `state/reproducibility_report.json`. Verify that all artifacts are present, schemas are valid, and metrics are stable across runs.

---

## Notes on Revision and Artifact Preservation

- Completed tasks (marked [X]) retain their identity and status; do not erase or regenerate them.
- Rejected tasks (marked [ ]) have been re-planned to produce verifiable deliverables (real files with expected schemas).
- New tasks (T042–T050) address specific reviewer concerns regarding data hygiene, error handling, GPU execution, and reproducibility.
- All scientific requirements from spec.md and plan.md are preserved; no constraints or success criteria have been omitted.
- The project remains a single-phase research study with 8–15 substantive implementation tasks, grouped by scientific objective and execution order.
