# Tasks: Machine Learning Prediction of Fracture Toughness from Microstructure Images

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must wait for dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure & Spec Alignment)

**Purpose**: Project initialization, spec alignment with Plan corrections, and contract definition. **Ensures spec reflects Plan's scientific decisions before implementation begins.**

- [X] T001a [P] Create code directories and init files: `code/__init__.py`, `code/data/__init__.py`, `code/models/__init__.py`, `code/train/__init__.py`, `code/explain/__init__.py`, `code/utils/__init__.py`. **Verification**: Run `ls -R code` and confirm all 6 `__init__.py` files exist.
- [X] T001b [P] Create data directories and keep files: `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/explainability/.gitkeep`. **Verification**: Run `ls -R data` and confirm all 3 `.gitkeep` files exist.
- [X] T001c [P] Create test directories and init files: `tests/__init__.py`, `tests/unit/__init__.py`, `tests/contract/__init__.py`, `tests/integration/__init__.py`. **Verification**: Run `ls -R tests` and confirm all 4 `__init__.py` files exist.
- [X] T002 [S] Create `code/requirements.txt` with pinned versions: `torch`, `scikit-learn`, `opencv-python-headless`, `pandas`, `numpy`, `matplotlib`, `captum`, `pyyaml`, `pytest`. **Verification**: Run `pip install -r code/requirements.txt` successfully.
- [X] T003 [P] Configure linting and formatting: Create `pyproject.toml` with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (select=['E', 'F', 'W'], ignore=['E501']). **Verification**: Run `ruff check.` and `black --check.` successfully (exit code 0).
- [ ] T009 [S] Create `research.md` artifact in `projects/PROJ-266-machine-learning-prediction-of-fracture-/` with content structure: Introduction, Methodology, Resolution Limits, Results, Discussion. **Verification**: `test -f research.md && grep -q "^## Introduction$" research.md && grep -q "^## Methodology$" research.md && grep -q "^## Resolution Limits$" research.md && grep -q "^## Results$" research.md && grep -q "^## Discussion$" research.md && echo "research.md verified"`. **Depends on**: T003. **Blocks**: T009a, T025d, T042d.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes metadata schema definition and artifact creation.**

- [ ] T009a [S] Define Methodology in `research.md` Section 3.2: Explicitly write the **deterministic logic** for synthetic generation of K_IC values. Define parameters for the logic (e.g., base_value, alpha, beta, noise) and document that this is a **synthetic ground truth** derived from the Plan's methodology, not real-world measurements, to maintain traceability. **Verification**: `grep -q "deterministic logic" research.md && grep -q "synthetic ground truth" research.md && grep -q "ground truth" research.md && echo "Methodology defined"`. **Depends on**: T009. **Blocks**: T005, T053a.
- [ ] T006a [P] Create base data contracts in `contracts/`: `dataset_schema.schema.yaml` and `evaluation_schema.schema.yaml`. **Verification**: `python -c "import yaml, pathlib; s1=yaml.safe_load(open('contracts/dataset_schema.schema.yaml')); s2=yaml.safe_load(open('contracts/evaluation_schema.schema.yaml')); assert s1['properties']['alloy_family']['enum'] == ['steel', 'Al', 'Ti']; assert 'image_path' in s1['properties']; assert 'k_ic' in s1['properties']; assert s2['properties']['model_type']['enum'] == ['cnn', 'linear', 'random_forest']; assert s2['properties']['r_squared']['type'] == 'number'; print('Schemas valid')"`. **Depends on**: T003.
- [ ] T006b [P] Create attribution schema contract `contracts/attribution_schema.schema.yaml`. **Verification**: `python -c "import yaml; s=yaml.safe_load(open('contracts/attribution_schema.schema.yaml')); assert 'image_id' in s['properties'] and 'heatmap_paths' in s['properties'] and 'iou_scores' in s['properties'] and 'stability_threshold_met' in s['properties']; print('Attribution schema valid')"`. **Depends on**: T003.
- [X] T007 [P] Implement configuration management in `code/utils/config.py` with keys `split_seed` (int), `train_seed` (int), `image_size` (tuple), `batch_size` (int), `min_feature_size_pixels` (int), `target_sample_size` (int). **Verification**: `python -c "from code.utils.config import CONFIG; assert isinstance(CONFIG['split_seed'], int)"`.
- [X] T008 [P] Implement error handling and logging infrastructure in `code/utils/logger.py`. **Verification**: Run a small script that imports `get_logger()` and writes a log; confirm `logs/app.log` contains a line matching `^\d{4}-\d{2}-\d{2}.+ -.+ -.+ - test$`.
- [X] T053a [P] Define logic for **sample preparation metadata** (magnification calibration, section thickness proxy) in `research.md` and `code/data/synthetic_gen.py`. Logic: `magnification_calibration` = random uniform over a range of pixels/micron; `section_thickness` = random uniform [10, 50] nm. Document derivation in `research.md`. **Verification**: `grep -q "magnification_calibration" research.md && grep -q "random uniform" research.md && grep -q "section_thickness" research.md && echo "Metadata logic defined"`. **Depends on**: T009a. **Blocks**: T053, T006c.
- [ ] T006c [P] Update `contracts/dataset_schema.schema.yaml` to include `magnification_calibration` and `section_thickness` fields defined in T053a. **Verification**: `python -c "import yaml; s=yaml.safe_load(open('contracts/dataset_schema.schema.yaml')); assert 'magnification_calibration' in s['properties'] and 'section_thickness' in s['properties']; print('Metadata schema valid')"`. **Depends on**: T053a. **Blocks**: T005.
- [ ] T053 [P] Implement **sample preparation metadata** generation in `code/data/synthetic_gen.py` using the logic defined in T053a. **Verification**: `python -c "import json; m=json.load(open('data/raw/metadata.json')); assert 'magnification_calibration' in m[0] and 'section_thickness' in m[0]"`. **Depends on**: T053a. **Blocks**: T005.
- [ ] T005 [S] Implement synthetic microstructure generator logic in `code/data/synthetic_gen.py` to produce **target sample size** images (defined in `CONFIG['target_sample_size']`) with **synthetic ground truth** K_IC values using the logic defined in `research.md` Section 3.2 (T009a). The generator MUST assign 'alloy_family' labels ensuring at least one sample each for 'steel', 'Al', and 'Ti'. **Note**: Due to the unavailability of the real "Metallurgical Microstructure–Fracture Toughness" dataset, this task implements a synthetic generator as justified in the Plan. **Verification**: `python -c "import glob, json; img_count=len(glob.glob('data/raw/*.png')); assert img_count >= 200; meta=json.load(open('data/raw/metadata.json')); assert len(meta) == img_count; families=set([m['alloy_family'] for m in meta]); assert families == {'steel', 'Al', 'Ti'}; assert all('magnification_calibration' in m for m in meta)"`. **Depends on**: T009a, T053, T006c. **Blocks**: T005b, T012a.
- [ ] T005b [S] Implement benchmark script `code/utils/benchmark_gen.py` to measure generator runtime. **Verification**: `mkdir -p data/benchmarks && python code/utils/benchmark_gen.py && test -f data/benchmarks/generator_runtime_raw.json`. **Depends on**: T005.
- [ ] T005c [S] Write benchmark results to `data/benchmarks/generator_runtime.json` from `generator_runtime_raw.json`. **Verification**: `python -c "import json, pathlib; p=pathlib.Path('data/benchmarks/generator_runtime.json'); d=json.load(p.open()); assert isinstance(d['total_time_seconds'], float) and isinstance(d['images_per_second'], float)"`. **Depends on**: T005b.
- [ ] T005d [S] Document in `research.md` that the generated dataset targets a sample size defined in `CONFIG['target_sample_size']`, with a minimum of 200 images for statistical power (justified by plan compute feasibility). **Verification**: `test -f research.md && grep -q "target sample size" research.md && echo "research.md updated"`. **Depends on**: T009a, T005.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw images (synthetic or user), standardize to 128×128 grayscale, and split stratified by alloy family. Validates metadata produced in Phase 2.

### Tests for User Story 1 (OPTIONAL)

- [ ] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`. **Verification**: `pytest tests/contract/test_dataset_schema.py -v && echo "contract test passed"`. **Depends on**: T006a.
- [ ] T011 [P] [US1] Integration test for stratified split logic in `tests/integration/test_stratified_split.py`. **Verification**: `pytest tests/integration/test_stratified_split.py -v && echo "integration test passed"`. **Depends on**: T014.

### Implementation for User Story 1

- [ ] T012a [P] [US1] Implement image loading and basic validation in `code/data/ingest.py` (handles missing K_IC, logs warnings, uses `metadata.json`). **Verification**: `python -c "import code.data.ingest as i; assert hasattr(i, 'load_csv')"`. **Depends on**: T006a.
- [ ] T012b [P] [US1] Add validation for missing K_IC values in `code/data/ingest.py`. **Verification**: `python code/data/ingest.py --csv tests/fixtures/missing_kic.csv && echo $? | grep -q '^1$' && echo "missing K_IC correctly rejected"`. **Depends on**: T012a.
- [ ] T013 [P] [US1] Implement preprocessing pipeline in `code/data/preprocess.py` (grayscale conversion, resize to 128x128, intensity normalization, handle large images by downsampling **without aspect ratio distortion** and **logging a warning**). **Note**: The synthetic generator produces 128x128 images directly; the >4000px edge case is handled by design but the code must support it for real data ingestion. **Verification**: `python code/data/preprocess.py --input data/raw --output data/processed && python -c "from PIL import Image; img=Image.open('data/processed/train/sample_001.png'); assert img.size == (128, 128) and img.mode == 'L' and img.getpixel((0,0)) < 256; assert 'aspect_ratio' in open('logs/preprocess.log').read() or 'Warning' in open('logs/preprocess.log').read()"`. **Depends on**: T012a, T012b.
- [ ] T014 [P] [US1] Implement stratified split logic (fixed seed, alloy families steel/Al/Ti) in `code/data/preprocess.py`. **Verification**: `python -c "import pandas as pd; df=pd.read_csv('data/processed/split_metadata.csv'); assert set(df['split'])=={'train','val','test'}; from code.utils.config import CONFIG; assert 'split_seed' in CONFIG"`. **Depends on**: T013.
- [ ] T015 [P] [US1] Generate `split_metadata.csv` recording alloy family distribution per split. **Verification**: `python -c "import pandas as pd; df=pd.read_csv('data/processed/split_metadata.csv'); assert list(df.columns)==['split','alloy_family','count']"`. **Depends on**: T014.
- [ ] T016 [P] [US1] Add validation to ensure test set contains at least one sample per alloy family; exit with error if not. **Verification**: Create a tiny dataset with only "steel" and run preprocessing; confirm exit code 1 and error message contains "ERROR: Test set missing alloy family". **Depends on**: T014.
- [ ] T017 [P] [US1] Add logging for preprocessing steps in `logs/preprocess.log` with format `%(asctime)s - PREPROCESS - %(message)s`. **Verification**: After running preprocessing, `grep -E "PREPROCESS" logs/preprocess.log` returns lines. **Depends on**: T008.

**Checkpoint**: User Story 1 fully functional and testable independently.

---

## Phase 4: User Story 2 - Lightweight CNN Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train a multi-block CNN, compare against Linear Regression and Random Forest baselines, and run Wilcoxon signed-rank test.

### Tests for User Story 2 (OPTIONAL)

- [ ] T018 [P] [US2] Contract test for evaluation schema in `tests/contract/test_evaluation_schema.py`. **Verification**: `pytest tests/contract/test_evaluation_schema.py -v && echo "evaluation contract test passed"`. **Depends on**: T006a.
- [ ] T019 [P] [US2] Integration test for Wilcoxon Test logic in `tests/integration/test_wilcoxon.py`. **Verification**: `pytest tests/integration/test_wilcoxon.py -v && echo "wilcoxon integration test passed"`. **Depends on**: T025a.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement a multi-block CNN architecture (Conv‑ReLU‑BN‑MaxPool) in `code/models/cnn.py`. **Verification**: `python -c "import code.models.cnn as m; assert hasattr(m, 'CNN')" `. **Depends on**: T007.
- [ ] T021 [P] [US2] Implement baseline models (Linear Regression, RandomForestRegressor) in `code/models/baselines.py`. **Verification**: `python -c "import code.models.baselines as b; assert hasattr(b, 'LinearRegressionModel')"`.
- [ ] T022 [P] [US2] Implement texture feature extraction (GLCM, **band-pass filtered power spectra**) in `code/data/features.py`. **Verification**: `python code/data/features.py --input data/processed --output data/features.json && python -c "import json; d=json.load(open('data/features.json')); assert isinstance(d, dict); assert 'band_pass_spectrum' in str(d)"`. **Depends on**: T013.
- [ ] T021b [S] [US2] Implement baseline training loop in `code/train/train_baselines.py` that consumes features from T022. **Verification**: `python code/train/train_baselines.py --features data/features.json && test -d models/baselines`. **Depends on**: T022.
- [ ] T023a [P] [US2] Implement seed management utility in `code/utils/seeds.py`. **Verification**: `python -c "from code.utils.seeds import get_seeds; assert len(get_seeds(n)) == n"`.
- [ ] T023b [P] [US2] Implement training loop with multiple independent seeds in `code/train/train_cnn.py`. **Verification**: `python code/train/train_cnn.py --seeds 5 && test -d models/cnn`. **Depends on**: T020, T023a.
- [ ] T024 [P] [US2] Implement metric calculation (R², MAE, RMSE) and save to JSON in `code/train/evaluate.py`. **Verification**: `python code/train/evaluate.py && python -c "import json; d=json.load(open('results/metrics.json')); assert all(k in d for k in ['r2','mae','rmse'])"`. **Depends on**: T023b, T021b.
- [ ] T024a [S] [US2] Aggregate the independent run results into a distribution structure (list of MAEs per model) and append to `results/metrics.json` for statistical testing. **Verification**: `python code/train/aggregate_results.py && python -c "import json; d=json.load(open('results/metrics.json')); assert 'mae_distribution' in d and len(d['mae_distribution']['cnn']) == 5"`. **Depends on**: T024. **Blocks**: T025a.
- [ ] T025a [S] [US2] Implement Wilcoxon signed-rank test function `wilcoxon_test` in `code/train/stats.py`, integrate into `evaluate.py`, and output results to `results/metrics.json`. The test compares the distribution of MAE differences between the CNN and each baseline model across multiple seeds using **alpha = 0.05**. **Verification**: `python code/train/evaluate.py && python -c "import json; d=json.load(open('results/metrics.json')); assert 'wilcoxon_p_value' in d and 'mae_distribution' in d and isinstance(d['wilcoxon_p_value'], float); import ast; code=open('code/train/stats.py').read(); assert 'alpha=0.05' in code or 'alpha = 0.05' in code"`. **Depends on**: T024a.
- [ ] T026 [P] [US2] Add logging for training progress in `logs/training.log` and enforce CPU-only execution. **Verification**: After a short training run, `grep -E "TRAIN - Epoch" logs/training.log` returns lines; `grep -q "torch.set_num_threads" code/train/train_cnn.py` and `! grep -q "cuda" code/train/train_cnn.py`. **Depends on**: T008.
- [ ] T007a [P] (Optional) Benchmark script `code/utils/benchmark_pipeline.py` (See Phase 2 T007a). **Note**: Moved from Phase 2 to Phase 4 to satisfy dependencies. **Verification**: `python code/utils/benchmark_pipeline.py && python -c "import json; d=json.load(open('data/benchmarks/pipeline_runtime.json')); assert 'total_time_seconds' in d"`. **Depends on**: T005, T013, T023b, T042.

**Checkpoint**: User Stories 1 & 2 operational.

---

## Phase 5: User Story 3 - Feature Attribution and Stability Reporting (Priority: P3)

**Goal**: Generate Grad-CAM heatmaps and validate stability via IoU across augmented views.

### Tests for User Story 3 (OPTIONAL)

- [ ] T038 [P] [US3] Contract test for attribution schema in `tests/contract/test_attribution_schema.py`. **Verification**: `pytest tests/contract/test_attribution_schema.py -v && echo "attribution contract test passed"`. **Depends on**: T006b.
- [ ] T039 [P] [US3] Integration test for IoU stability calculation in `tests/integration/test_stability.py`. **Verification**: `pytest tests/integration/test_stability.py -v && echo "stability integration test passed"`.

### Implementation for User Story 3

- [ ] T041 [S] [US3] Select and lock a random subset of test images for attribution analysis. Save the list of image IDs to `data/explainability/attrib_subset.json`. **Verification**: `python code/explain/select_subset.py && python -c "import json; d=json.load(open('data/explainability/attrib_subset.json')); assert len(d) >= 10"`. **Depends on**: T013. **Blocks**: T042, T043.
- [ ] T042 [S] [US3] Implement Grad-CAM heatmap generation in `code/explain/gradcam.py` using the last convolutional layer and the output neuron activation as the target. **Verification**: `python code/explain/gradcam.py --image data/processed/test/sample_001.png --model models/cnn.pt --output data/explainability/gradcam_sample_001.png --subset data/explainability/attrib_subset.json && test -f data/explainability/gradcam_sample_001.png && echo "Grad-CAM generated"`. **Depends on**: T020, T013, T041.
- [ ] T043 [P] [US3] Implement augmentation pipeline for stability testing (`code/explain/stability.py`) – rotations ±10°, Gaussian noise σ=0.01, brightness jitter ±10%. **Verification**: `python code/explain/stability.py --augment --image data/processed/test/sample_001.png --count 5 --subset data/explainability/attrib_subset.json && test -d data/explainability/aug_views && echo "augmentations created"`. **Depends on**: T013, T041.
- [ ] T044 [P] [US3] Calculate IoU between Grad-CAM heatmaps of augmented views. The script MUST read augmented views from `data/explainability/aug_views` (generated by T043) and output the IoU scores to `data/explainability/iou_scores.json`. **Verification**: `python code/explain/stability.py --iou --input data/explainability/aug_views --subset data/explainability/attrib_subset.json --output data/explainability/iou_scores.json && python -c "import json; d=json.load(open('data/explainability/iou_scores.json')); assert 'mean_iou' in d and 'iou_scores' in d and len(d['iou_scores']) > 0"`. **Depends on**: T042, T043.
- [ ] T045 [P] [US3] Generate stability report `stability_report.json` with schema `{ "mean_iou": float, "std_iou": float, "images_analyzed": int }`. **Verification**: `python -c "import json; d=json.load(open('data/explainability/stability_report.json')); assert all(k in d for k in ['mean_iou','std_iou','images_analyzed'])"`. **Depends on**: T044.
- [ ] T046 [P] [US3] Implement validation script `code/explain/validate.py` that loads `stability_report.json`, validates against `contracts/attribution_schema.schema.yaml`. **Verification**: `python code/explain/validate.py && echo "validation passed"`.
- [ ] T048 [P] [US3] Run full attribution validation (`code/explain/validate.py`) and confirm exit code 0. **Verification**: `python code/explain/validate.py && echo "all attribution checks passed"`.

**Checkpoint**: All user stories functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T050 [P] Code cleanup and refactoring: remove unused imports (`ruff check. --select=F401`), enforce snake_case naming. **Verification**: `ruff check. --select=F401` returns 0.
- [ ] T051 [P] Finalize `research.md` with a "Limitations" section explicitly stating how imaging resolution limits affect the model's ability to detect specific grain boundary characters. **Verification**: `grep -q "Limitations" research.md && grep -q "resolution" research.md && echo "Limitations section finalized"`. **Depends on**: T009.

---

## Phase O: Research-Stage Review Remediation (Rosalind Franklin Simulated)

**Purpose**: Address specific reviewer concerns regarding experimental specification, imaging resolution, and statistical confidence intervals (Review ID: `rosalind-franklin-simulated__2026-06-27__research.md`).

### Implementation for Review Remediation

- [ ] T052 [S] [Review] Update `research.md` Section 2 (Methodology) to explicitly define the **imaging resolution** (pixels per micron) and **minimum resolvable feature size** (e.g., grain boundary width) for the synthetic generator. **Verification**: `grep -q "minimum resolvable feature size" research.md && grep -q "pixels per micron" research.md`. **Depends on**: T009.
- [ ] T056 [P] [Review] Update `research.md` Section 4 (Discussion) to include a **Variance Analysis** subsection detailing how the model's predictions account for the variance in feature extraction across different synthetic preparation batches. **Verification**: `grep -q "Variance Analysis" research.md && grep -q "preparation batches" research.md`. **Depends on**: T053, T009.
- [ ] T057 [P] [Review] Add a unit test in `tests/unit/test_resolution_limits.py` that verifies the synthetic generator cannot produce features smaller than the defined `min_feature_size_pixels`. **Verification**: `pytest tests/unit/test_resolution_limits.py -v && echo "resolution limit test passed"`. **Depends on**: T055.
- [ ] T058 [P] [Review] Update `research.md` to include a **Sample Preparation Protocol** section detailing the synthetic generation parameters for magnification calibration, section thickness (for TEM proxy), and surface preparation (for SEM proxy), including the expected variance in feature extraction across different preparation batches. **Verification**: `grep -q "Sample Preparation Protocol" research.md && grep -q "magnification calibration" research.md && grep -q "section thickness" research.md && grep -q "surface preparation" research.md && grep -q "expected variance" research.md`. **Depends on**: T009, T053a.

**Checkpoint**: All research-stage review concerns addressed; experimental specification is now complete and scientifically rigorous.