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
- [ ] T002 [S] Create `code/requirements.txt` with pinned versions: `torch`, `scikit-learn`, `opencv-python-headless`, `pandas`, `numpy`, `matplotlib`, `captum`, `pyyaml`, `pytest`. **Verification**: Run `pip install -r code/requirements.txt` successfully.
- [ ] T003 [P] Configure linting and formatting: Create `pyproject.toml` with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (select=['E', 'F', 'W'], ignore=['E501']). **Verification**: Run `ruff check.` and `black --check.` successfully (exit code 0).
- [ ] T009 [S] Create `research.md` artifact in `projects/PROJ-266-machine-learning-prediction-of-fracture-/` with content structure: Introduction, Methodology, Resolution Limits, Results, Discussion. **Verification**: `test -f research.md && grep -q "Introduction" research.md && grep -q "Methodology" research.md && grep -q "Resolution Limits" research.md && grep -q "Results" research.md && grep -q "Discussion" research.md && echo "research.md verified"`. **Depends on**: T003. **Blocks**: T025d, T042d.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes metadata schema definition and artifact creation.**

- [ ] T004a [P] Create data directory structure (`data/raw`, `data/processed`, `data/explainability`). **Verification**: `test -d data/raw && test -d data/processed && test -d data/explainability && echo "Data dirs created"`.
- [X] T004b [P] Implement checksum validation infrastructure in `code/data/ingest.py`. **Verification**: Run `python -c "import code.data.ingest as i; assert hasattr(i, 'validate_checksum')"`.
- [ ] T006a [S] Create base data contracts in `contracts/`: `dataset_schema.schema.yaml` and `evaluation_schema.schema.yaml`. **Verification**: `python -c "import yaml, pathlib; assert yaml.safe_load(open('contracts/dataset_schema.schema.yaml')).get('properties'); assert yaml.safe_load(open('contracts/evaluation_schema.schema.yaml')).get('properties')"`.
- [ ] T006b [P] Create attribution schema contract `contracts/attribution_schema.schema.yaml`. **Verification**: `python -c "import yaml; s=yaml.safe_load(open('contracts/attribution_schema.schema.yaml')); assert 'image_id' in s['properties']"`.
- [ ] T007 [P] Implement configuration management in `code/utils/config.py` with keys `split_seed` (int), `train_seed` (int), `image_size` (tuple), `batch_size` (int). **Verification**: `python -c "from code.utils.config import CONFIG; assert isinstance(CONFIG['split_seed'], int)"`.
- [ ] T008 [P] Implement error handling and logging infrastructure in `code/utils/logger.py`. **Verification**: Run a small script that imports `get_logger()` and writes a log; confirm `logs/app.log` contains a line matching `^\d{4}-\d{2}-\d{2}.+ -.+ -.+ - test$`.
- [ ] T005 [S] Implement synthetic microstructure generator logic in `code/data/synthetic_gen.py` to produce **≥ 2,000** images with physics-informed K_IC values using the formula defined in `research.md` Section 3.2. **Verification**: `python -c "import glob, json; assert len(glob.glob('data/raw/*.png')) >= 2000; meta=json.load(open('data/raw/metadata.json')); assert len(meta) >= 2000" AND python code/utils/benchmark_gen.py && python -c "import json; d=json.load(open('data/benchmarks/generator_runtime.json')); assert d['total_time_seconds'] < 3600"`. **Depends on**: T009. **Blocks**: T025d, T042d.
- [ ] T005b [S] Implement and run benchmark script `code/utils/benchmark_gen.py` to measure generator runtime and write `data/benchmarks/generator_runtime.json`. **Verification**: `python code/utils/benchmark_gen.py && python -c "import json, pathlib; p=pathlib.Path('data/benchmarks/generator_runtime.json'); d=json.load(p.open()); assert isinstance(d['total_time_seconds'], float) and isinstance(d['images_per_second'], float)"`. **Depends on**: T005.
- [ ] T005d [S] Document in `research.md` that the generated dataset targets ≥ 2,000 images as an implementation choice, exceeding the spec's soft target of ≥ 500 images. **Verification**: `test -f research.md && grep -q "targets ≥ 2,000 images" research.md && echo "research.md updated"`. **Depends on**: T009, T005.
- [ ] T007a [P] (Optional) Add a script `code/utils/benchmark_pipeline.py` to measure full pipeline runtime, writing `data/benchmarks/pipeline_runtime.json`. **Verification**: `python code/utils/benchmark_pipeline.py && python -c "import json; d=json.load(open('data/benchmarks/pipeline_runtime.json')); assert 'total_time_seconds' in d"`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw images (synthetic or user), standardize to 128×128 grayscale, and split stratified by alloy family. Validates metadata produced in Phase 2.

### Tests for User Story 1 (OPTIONAL)

- [ ] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`. **Verification**: `pytest tests/contract/test_dataset_schema.py -v && echo "contract test passed"`. **Depends on**: T006a.
- [ ] T011 [P] [US1] Integration test for stratified split logic in `tests/integration/test_stratified_split.py`. **Verification**: `pytest tests/integration/test_stratified_split.py -v && echo "integration test passed"`. **Depends on**: T014.

### Implementation for User Story 1

- [ ] T012a [P] [US1] Implement image loading and basic validation in `code/data/ingest.py` (handles missing K_IC, logs warnings). **Verification**: `python -c "import code.data.ingest as i; assert hasattr(i, 'load_csv')"`. **Depends on**: T006a.
- [ ] T012b [P] [US1] Add validation for missing K_IC values in `code/data/ingest.py`. **Verification**: `python code/data/ingest.py --csv tests/fixtures/missing_kic.csv && echo $? | grep -q '^1$' && echo "missing K_IC correctly rejected"`. **Depends on**: T012a.
- [ ] T013 [P] [US1] Implement preprocessing pipeline in `code/data/preprocess.py` (grayscale conversion, resize to 128x128, intensity normalization, handle large images by downsampling). **Verification**: `python code/data/preprocess.py --input data/raw --output data/processed && python -c "from PIL import Image; img=Image.open('data/processed/train/sample_001.png'); assert img.size == (128, 128) and img.mode == 'L'"`. **Depends on**: T012a.
- [ ] T013a [P] [US1] Log warnings in `logs/preprocess.log` for images resized from >4000px resolution, noting aspect ratio preservation. **Verification**: Run on large image; `grep -q "WARNING: Downsampled from" logs/preprocess.log`. **Depends on**: T013.
- [ ] T014 [P] [US1] Implement stratified split logic (fixed seed, alloy families steel/Al/Ti) in `code/data/preprocess.py`. **Verification**: `python -c "import pandas as pd; df=pd.read_csv('data/processed/split_metadata.csv'); assert set(df['split'])=={'train','val','test'}"`. **Depends on**: T013.
- [ ] T015 [P] [US1] Generate `split_metadata.csv` recording alloy family distribution per split. **Verification**: `python -c "import pandas as pd; df=pd.read_csv('data/processed/split_metadata.csv'); assert list(df.columns)==['split','alloy_family','count']"`. **Depends on**: T014.
- [ ] T016 [P] [US1] Add validation to ensure test set contains at least one sample per alloy family; exit with error if not. **Verification**: Create a tiny dataset with only "steel" and run preprocessing; confirm exit code 1 and error message contains "ERROR: Test set missing alloy family". **Depends on**: T014.
- [ ] T017 [P] [US1] Add logging for preprocessing steps in `logs/preprocess.log` with format `%(asctime)s - PREPROCESS - %(message)s`. **Verification**: After running preprocessing, `grep -E "PREPROCESS" logs/preprocess.log` returns lines. **Depends on**: T008.

**Checkpoint**: User Story 1 fully functional and testable independently.

---

## Phase 4: User Story 2 - Lightweight CNN Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train 3‑block CNN, compare against Linear Regression and Random Forest baselines, and run Wilcoxon signed-rank test.

### Tests for User Story 2 (OPTIONAL)

- [ ] T018 [P] [US2] Contract test for evaluation schema in `tests/contract/test_evaluation_schema.py`. **Verification**: `pytest tests/contract/test_evaluation_schema.py -v && echo "evaluation contract test passed"`. **Depends on**: T006a.
- [ ] T019 [P] [US2] Integration test for Wilcoxon Test logic in `tests/integration/test_wilcoxon.py`. **Verification**: `pytest tests/integration/test_wilcoxon.py -v && echo "wilcoxon integration test passed"`. **Depends on**: T025a.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement a multi-block CNN architecture (Conv‑ReLU‑BN‑MaxPool) in `code/models/cnn.py`. **Verification**: `python -c "import code.models.cnn as m; assert hasattr(m, 'CNN')" `. **Depends on**: T007.
- [ ] T021 [P] [US2] Implement baseline models (Linear Regression, RandomForestRegressor) in `code/models/baselines.py`. **Verification**: `python -c "import code.models.baselines as b; assert hasattr(b, 'LinearRegressionModel')"`.
- [ ] T022 [P] [US2] Implement texture feature extraction (GLCM, power spectra) in `code/data/features.py`. **Verification**: `python code/data/features.py --input data/processed --output data/features.json && python -c "import json; d=json.load(open('data/features.json')); assert isinstance(d, dict)"`. **Depends on**: T013.
- [ ] T023a [P] [US2] Implement seed management utility in `code/utils/seeds.py`. **Verification**: `python -c "from code.utils.seeds import get_seeds; assert get_seeds(5) == [42,43,44,45,46]"`.
- [ ] T023b [P] [US2] Implement training loop with multiple independent seeds in `code/train/train_cnn.py`. **Verification**: `python code/train/train_cnn.py --seeds 5 && test -d models/cnn`. **Depends on**: T020, T023a.
- [ ] T024 [P] [US2] Implement metric calculation (R², MAE, RMSE) and save to JSON in `code/train/evaluate.py`. **Verification**: `python code/train/evaluate.py && python -c "import json; d=json.load(open('results/metrics.json')); assert all(k in d for k in ['r2','mae','rmse'])"`. **Depends on**: T023b.
- [ ] T025a [S] [US2] Implement Wilcoxon signed-rank test function `wilcoxon_test` in `code/train/stats.py`, integrate into `evaluate.py`, and output results to `results/metrics.json`. The test compares the distribution of MAE differences between the CNN and each baseline model across multiple seeds. **Verification**: `python code/train/evaluate.py && python -c "import json; d=json.load(open('results/metrics.json')); assert 'wilcoxon_p_value' in d"`. **Depends on**: T024.
- [ ] T026 [P] [US2] Add logging for training progress in `logs/training.log`. **Verification**: After a short training run, `grep -E "TRAIN - Epoch" logs/training.log` returns lines. **Depends on**: T008.

**Checkpoint**: User Stories 1 & 2 operational.

---

## Phase 5: User Story 3 - Feature Attribution and Stability Reporting (Priority: P3)

**Goal**: Generate Grad-CAM heatmaps and validate stability via IoU across augmented views.

### Tests for User Story 3 (OPTIONAL)

- [ ] T038 [P] [US3] Contract test for attribution schema in `tests/contract/test_attribution_schema.py`. **Verification**: `pytest tests/contract/test_attribution_schema.py -v && echo "attribution contract test passed"`. **Depends on**: T006b.
- [ ] T039 [P] [US3] Integration test for IoU stability calculation in `tests/integration/test_stability.py`. **Verification**: `pytest tests/integration/test_stability.py -v && echo "stability integration test passed"`.

### Implementation for User Story 3

- [ ] T042 [S] [US3] Implement Grad-CAM heatmap generation in `code/explain/gradcam.py` using the last convolutional layer and the output neuron activation as the target. **Verification**: `python code/explain/gradcam.py --image data/processed/test/sample_001.png --model models/cnn.pt --output data/explainability/gradcam_sample_001.png && test -f data/explainability/gradcam_sample_001.png && echo "Grad-CAM generated"`. **Depends on**: T020.
- [ ] T043 [P] [US3] Implement augmentation pipeline for stability testing (`code/explain/stability.py`) – rotations ±10°, Gaussian noise σ=0.01, brightness jitter ±10%. **Verification**: `python code/explain/stability.py --augment --image data/processed/test/sample_001.png --count 5 && test -d aug_views && echo "augmentations created"`.
- [ ] T044 [P] [US3] Calculate IoU between Grad-CAM heatmaps of augmented views. **Verification**: `python code/explain/stability.py --iou --input data/explainability/augmented/ && python -c "import json; d=json.load(open('data/explainability/iou_scores.json')); assert 'mean_iou' in d"`.
- [ ] T045 [P] [US3] Generate stability report `stability_report.json` with schema `{ "mean_iou": float, "std_iou": float, "images_analyzed": int }`. **Verification**: `python -c "import json; d=json.load(open('data/explainability/stability_report.json')); assert all(k in d for k in ['mean_iou','std_iou','images_analyzed'])"`.
- [ ] T046 [P] [US3] Implement validation script `code/explain/validate.py` that loads `stability_report.json`, validates against `contracts/attribution_schema.schema.yaml`. **Verification**: `python code/explain/validate.py && echo "validation passed"`.
- [ ] T048 [P] [US3] Run full attribution validation (`code/explain/validate.py`) and confirm exit code 0. **Verification**: `python code/explain/validate.py && echo "all attribution checks passed"`.

**Checkpoint**: All user stories functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T047a [P] Implement benchmark script `code/utils/benchmark_pipeline.py` to measure full pipeline runtime, outputting `data/benchmarks/pipeline_runtime.json` with fields `total_time_seconds` and `pipeline_steps`. **Verification**: `python code/utils/benchmark_pipeline.py && python -c "import json; d=json.load(open('data/benchmarks/pipeline_runtime.json')); assert 'total_time_seconds' in d"`. **Depends on**: T005, T013, T023b, T042.
- [ ] T047b [P] Run pipeline benchmark on full dataset. **Verification**: `python code/utils/benchmark_pipeline.py && test -f data/benchmarks/pipeline_runtime.json && echo "pipeline benchmark completed"`.
- [ ] T050 [P] Code cleanup and refactoring: remove unused imports (`ruff check. --select=F401`), enforce snake_case naming. **Verification**: `ruff check. --select=F401` returns 0.
- [ ] T051 [P] Finalize `research.md` with a "Limitations" section explicitly stating how imaging resolution limits affect the model's ability to detect specific grain boundary characters. **Verification**: `grep -q "Limitations" research.md && grep -q "resolution" research.md && echo "Limitations section finalized"`. **Depends on**: T009.

---

## Phase O: Research-Stage Review Remediation (Rosalind Franklin Simulated)

**Purpose**: Address specific reviewer concerns regarding experimental specification, imaging resolution, and statistical confidence intervals (Review ID: `rosalind-franklin-simulated__2026-06-27__research.md`).

### Implementation for Review Remediation

- [ ] T052 [S] [Review] Update `research.md` Section 2 (Methodology) to explicitly define the **imaging resolution** (pixels per micron) and **minimum resolvable feature size** (e.g., grain boundary width) for the synthetic generator. **Verification**: `grep -q "minimum resolvable feature size" research.md && grep -q "pixels per micron" research.md`. **Depends on**: T009.
- [ ] T053 [S] [Review] Extend `code/data/synthetic_gen.py` to generate and store **sample preparation metadata** (magnification calibration, section thickness proxy, surface preparation protocol) in `data/raw/metadata.json` for every synthetic image. **Verification**: `python -c "import json; m=json.load(open('data/raw/metadata.json')); assert 'magnification_calibration' in m[0] and 'section_thickness' in m[0]"`. **Depends on**: T005.
- [ ] T054 [P] [Review] Implement **statistical confidence interval calculation** for extracted texture features (GLCM) in `code/data/features.py`. The script must compute 95% CI for mean texture energy and contrast across the batch. **Verification**: `python code/data/features.py --ci 95 && python -c "import json; d=json.load(open('data/features.json')); assert 'confidence_intervals' in d['metadata']"`. **Depends on**: T022.
- [ ] T055 [S] [Review] Add a validation step in `code/utils/config.py` to enforce a **minimum feature size threshold** relative to the 128x128 image dimensions, raising an error if synthetic generation parameters would create features smaller than 2 pixels (Nyquist limit). **Verification**: `python -c "from code.utils.config import CONFIG; assert CONFIG['min_feature_size_pixels'] >= 2"`. **Depends on**: T007.
- [ ] T056 [P] [Review] Update `research.md` Section 4 (Discussion) to include a **Variance Analysis** subsection detailing how the model's predictions account for the variance in feature extraction across different synthetic preparation batches. **Verification**: `grep -q "Variance Analysis" research.md && grep -q "preparation batches" research.md`. **Depends on**: T054.
- [ ] T057 [P] [Review] Add a unit test in `tests/unit/test_resolution_limits.py` that verifies the synthetic generator cannot produce features smaller than the defined `min_feature_size_pixels`. **Verification**: `pytest tests/unit/test_resolution_limits.py -v && echo "resolution limit test passed"`. **Depends on**: T055.

**Checkpoint**: All research-stage review concerns addressed; experimental specification is now complete and scientifically rigorous.
