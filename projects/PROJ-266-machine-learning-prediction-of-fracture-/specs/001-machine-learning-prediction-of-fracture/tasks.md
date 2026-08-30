# Tasks: Machine Learning Prediction of Fracture Toughness from Microstructure Images

**Input**: Design documents from `/specs/001-gene-regulation/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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
- [X] T002 [P] Initialize Python 3.11 project with `code/requirements.txt` containing exact pinned versions: `torch==2.1.0+cpu`, `scikit-learn==1.3.2`, `opencv-python-headless==4.8.1.78`, `pandas==2.1.3`, `numpy==1.26.2`, `matplotlib==3.8.2`, `captum==0.7.0`, `pytest==7.4.3`, `black==23.12.1`, `ruff==0.1.8`. **Verification**: Run `pip install -r code/requirements.txt` successfully.
- [X] T003 [P] Configure linting and formatting: Create `pyproject.toml` with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (select=['E', 'F', 'W'], ignore=['E501']). **Verification**: Run `ruff check .` and `black --check .` successfully (exit code 0).
- [ ] T009 [P] Create `research.md` artifact in `projects/PROJ-266-machine-learning-prediction-of-fracture-/` with content structure: Introduction, Methodology, Resolution Limits, Results, Discussion. **Verification**: `test -f research.md && grep -q "Introduction" research.md && grep -q "Methodology" research.md && grep -q "Resolution Limits" research.md && grep -q "Results" research.md && grep -q "Discussion" research.md && echo "research.md verified"`. **Depends on**: T003. **Blocks**: T025d, T042b, T037.

### Spec Alignment Tasks (Phase 1 - Critical for Single Source of Truth)

- [ ] T005e [P] Verify that `spec.md` still states the sample‑size assumption as “≥ 500 images”. **Verification**: `grep -q "≥ 500 images" spec.md && echo "Spec sample size assumption verified"` . **Depends on**: None.
- [ ] T006c [P] Verify that `spec.md` does **not** require a JSON side‑car file for each image (CSV‑only input). **Verification**: `! grep -q "JSON sidecar" spec.md && echo "Spec JSON side‑car requirement verified"` . **Depends on**: None.
- [ ] T025e [P] Verify that `spec.md` still requires a Wilcoxon signed‑rank test for FR‑005. **Verification**: `grep -q "Wilcoxon signed-rank test" spec.md && echo "Spec Wilcoxon requirement verified"` . **Depends on**: None.
- [ ] T042c [P] Verify that `spec.md` still requires Grad‑CAM heatmaps for FR‑006/FR-007. **Verification**: `grep -q "Grad-CAM" spec.md && echo "Spec Grad-CAM requirement verified"` . **Depends on**: None.
- [ ] T006d [P] Verify that SC‑003 does not define a hard IoU threshold. **Verification**: `! grep -q "mean_iou >" spec.md && echo "Spec IoU threshold not defined"` . **Depends on**: None.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes metadata schema definition and artifact creation.**

- [ ] T004a [P] Create data directory structure (`data/raw`, `data/processed`, `data/explainability`). **Verification**: `test -d data/raw && test -d data/processed && test -d data/explainability && echo "Data dirs created"`.
- [X] T004b [P] Implement checksum validation infrastructure in `code/data/ingest.py`. **Verification**: Run `python -c "import code.data.ingest as i; assert hasattr(i, 'validate_checksum')"` .
- [ ] T005 [P] Implement synthetic microstructure generator logic in `code/data/synthetic_gen.py` to produce **≥ 2,000** images with physics-informed K_IC values. **Verification**: `python -c "import glob, json; assert len(glob.glob('data/raw/*.png')) >= 2000; meta=json.load(open('data/raw/metadata.json')); assert len(meta) >= 2000"` . **Depends on**: T005e.
- [ ] T005b [P] Implement benchmark script `code/utils/benchmark_gen.py` to measure generator runtime and write `data/benchmarks/generator_runtime.json`. **Verification**: `python code/utils/benchmark_gen.py && python -c "import json, pathlib; p=pathlib.Path('data/benchmarks/generator_runtime.json'); d=json.load(p.open()); assert isinstance(d['total_time_seconds'], float) and isinstance(d['images_per_second'], float)"` . **Depends on**: T005.
- [ ] T005c [P] Run generator benchmark and verify output. **Verification**: `python code/utils/benchmark_gen.py && python -c "import json; d=json.load(open('data/benchmarks/generator_runtime.json')); assert 'total_time_seconds' in d and isinstance(d['total_time_seconds'], float); assert 'images_per_second' in d and isinstance(d['images_per_second'], float); print('Benchmark verified')"` . **Depends on**: T005b.
- [ ] T005d [P] Validate dataset size assumption: write a note in `research.md` documenting that the generated dataset exceeds the spec’s ≥ 500 image assumption. **Verification**: `test -f research.md && grep -q "Spec assumed ≥500; generated ≥2000 images" research.md && echo "research.md updated"` . **Depends on**: T009, T005.
- [ ] T006a [P] Create base data contracts in `contracts/`: `dataset_schema.schema.yaml` and `evaluation_schema.schema.yaml`. **Verification**: `python -c "import yaml, pathlib; assert yaml.safe_load(open('contracts/dataset_schema.schema.yaml')).get('properties'); assert yaml.safe_load(open('contracts/evaluation_schema.schema.yaml')).get('properties')"` .
- [ ] T006b [P] Create attribution schema contract `contracts/attribution_schema.schema.yaml`. **Verification**: `python -c "import yaml; s=yaml.safe_load(open('contracts/attribution_schema.schema.yaml')); assert 'image_id' in s['properties']"` .
- [ ] T007 [P] Implement configuration management in `code/utils/config.py` with keys `split_seed` (int), `train_seed` (int), `image_size` (tuple), `batch_size` (int). **Verification**: `python -c "from code.utils.config import CONFIG; assert isinstance(CONFIG['split_seed'], int) and isinstance(CONFIG['stability_iou_threshold'], float)"` .
- [ ] T008 [P] Implement error handling and logging infrastructure in `code/utils/logger.py`. **Verification**: Run a small script that imports `get_logger()` and writes a log; confirm `logs/app.log` contains a line matching `^\d{4}-\d{2}-\d{2} .+ - .+ - .+ - test$` .
- [ ] T031 [P] (Optional) Extend synthetic generator to emit optional JSON side‑car files (`image_001.png.json`) adhering to the dataset schema. **Verification**: After running generator, `test -f data/raw/image_001.png.json && python -c "import json; json.load(open('data/raw/image_001.png.json'))"` .
- [ ] T054 [P] Implement `calculate_resolution_limit` utility in `code/utils/metrics.py` that computes the Rayleigh criterion from `resolution_um`. **Verification**: `python -c "from code.utils.metrics import calculate_resolution_limit; assert isinstance(calculate_resolution_limit(0.1), float)"` .
- [ ] T007a [P] (Optional) Add a script `code/utils/benchmark_pipeline.py` to measure full pipeline runtime, writing `data/benchmarks/pipeline_runtime.json`. **Verification**: `python code/utils/benchmark_pipeline.py && python -c "import json; d=json.load(open('data/benchmarks/pipeline_runtime.json')); assert 'total_time_seconds' in d"` .

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw images (synthetic or user), standardize to 128×128 grayscale, and split stratified by alloy family. Validates metadata produced in Phase 2.

### Tests for User Story 1 (OPTIONAL)

- [ ] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`. **Verification**: `pytest tests/contract/test_dataset_schema.py -v && echo "contract test passed"` . **Depends on**: T006a.
- [ ] T011 [P] [US1] Integration test for stratified split logic in `tests/integration/test_stratified_split.py`. **Verification**: `pytest tests/integration/test_stratified_split.py -v && echo "integration test passed"` . **Depends on**: T014.

### Implementation for User Story 1

- [ ] T012a [P] [US1] Implement image loading and basic validation in `code/data/ingest.py` (handles missing K_IC, logs warnings). **Verification**: `python -c "import code.data.ingest as i; assert hasattr(i, 'load_csv')"` . **Depends on**: T006c.
- [ ] T012b [P] [US1] Add validation for missing K_IC values in `code/data/ingest.py`. **Verification**: `python code/data/ingest.py --csv tests/fixtures/missing_kic.csv && echo $? | grep -q '^1$' && echo "missing K_IC correctly rejected"` . **Depends on**: T012a.
- [ ] T013 [P] [US1] Implement preprocessing pipeline in `code/data/preprocess.py` (grayscale conversion, resize to 128x128, intensity normalization). **Verification**: `python code/data/preprocess.py --input data/raw --output data/processed && python -c "from PIL import Image; img=Image.open('data/processed/train/sample_001.png'); assert img.size == (128, 128) and img.mode == 'L'"` . **Depends on**: T012a.
- [ ] T014 [P] [US1] Implement stratified split logic (seed 42, alloy families steel/Al/Ti) in `code/data/preprocess.py`. **Verification**: `python -c "import pandas as pd; df=pd.read_csv('data/processed/split_metadata.csv'); assert set(df['split'])=={'train','val','test'}"` . **Depends on**: T013.
- [ ] T015 [P] [US1] Generate `split_metadata.csv` recording alloy family distribution per split. **Verification**: `python -c "import pandas as pd; df=pd.read_csv('data/processed/split_metadata.csv'); assert list(df.columns)==['split','alloy_family','count']"` . **Depends on**: T014.
- [ ] T016 [P] [US1] Add validation to ensure test set contains at least one sample per alloy family; exit with error if not. **Verification**: Create a tiny dataset with only “steel” and run preprocessing; confirm exit code 1 and error message contains “ERROR: Test set missing alloy family”. **Depends on**: T014.
- [ ] T017 [P] [US1] Add logging for preprocessing steps in `logs/preprocess.log` with format `%(asctime)s - PREPROCESS - %(message)s`. **Verification**: After running preprocessing, `grep -E "PREPROCESS" logs/preprocess.log` returns lines. **Depends on**: T008.

**Checkpoint**: User Story 1 fully functional and testable independently.

---

## Phase 4: User Story 2 - Lightweight CNN Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train 3‑block CNN, compare against Linear Regression and Random Forest baselines, and run Wilcoxon signed-rank test.

### Tests for User Story 2 (OPTIONAL)

- [ ] T018 [P] [US2] Contract test for evaluation schema in `tests/contract/test_evaluation_schema.py`. **Verification**: `pytest tests/contract/test_evaluation_schema.py -v && echo "evaluation contract test passed"` . **Depends on**: T006a.
- [ ] T019 [P] [US2] Integration test for Wilcoxon test logic in `tests/integration/test_wilcoxon.py`. **Verification**: `pytest tests/integration/test_wilcoxon.py -v && echo "wilcoxon integration test passed"` . **Depends on**: T025a.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement 3‑block CNN architecture (Conv‑ReLU‑BN‑MaxPool) in `code/models/cnn.py`. **Verification**: `python -c "import code.models.cnn as m; assert hasattr(m, 'CNN')" ` . **Depends on**: T007.
- [ ] T021 [P] [US2] Implement baseline models (Linear Regression, RandomForestRegressor) in `code/models/baselines.py`. **Verification**: `python -c "import code.models.baselines as b; assert hasattr(b, 'LinearRegressionModel')"` .
- [ ] T022 [P] [US2] Implement texture feature extraction (GLCM, power spectra) in `code/data/features.py`. **Verification**: `python code/data/features.py --input data/processed --output data/features.json && python -c "import json; d=json.load(open('data/features.json')); assert isinstance(d, dict)"` . **Depends on**: T013.
- [ ] T023a [P] [US2] Implement seed management utility in `code/utils/seeds.py`. **Verification**: `python -c "from code.utils.seeds import get_seeds; assert get_seeds(5) == [42,43,44,45,46]"` .
- [ ] T023b [P] [US2] Implement training loop with multiple independent seeds in `code/train/train_cnn.py`. **Verification**: `python code/train/train_cnn.py --seeds 5 && test -d models/cnn` . **Depends on**: T020, T023a.
- [ ] T024 [P] [US2] Implement metric calculation (R², MAE, RMSE) and save to JSON in `code/train/evaluate.py`. **Verification**: `python code/train/evaluate.py && python -c "import json; d=json.load(open('results/metrics.json')); assert all(k in d for k in ['r2','mae','rmse'])"` . **Depends on**: T023b.
- [ ] T025a [P] [US2] Implement Permutation Test function `permutation_test` returning statistic and p_value. **Verification**: `python -c "from code.train.stats import permutation_test; stat, p = permutation_test([1,2,3],[2,3,4]); assert isinstance(stat, float) and isinstance(p,float)"` .
- [ ] T025b [P] [US2] Integrate Permutation Test call in `code/train/evaluate.py`. **Verification**: `python code/train/evaluate.py && python -c "import json; d=json.load(open('results/metrics.json')); assert 'permutation_p_value' in d"` .
- [ ] T025c [P] [US2] Format Permutation Test output JSON in `code/train/evaluate.py`. **Verification**: Same as T025b.
- [ ] T026 [P] [US2] Add logging for training progress in `logs/training.log`. **Verification**: After a short training run, `grep -E "TRAIN - Epoch" logs/training.log` returns lines. **Depends on**: T008.

**Checkpoint**: User Stories 1 & 2 operational.

---

## Phase 5: User Story 3 - Feature Attribution and Stability Reporting (Priority: P3)

**Goal**: Generate InputXGrad heatmaps and validate stability via IoU across augmented views.

### Tests for User Story 3 (OPTIONAL)

- [ ] T038 [P] [US3] Contract test for attribution schema in `tests/contract/test_attribution_schema.py`. **Verification**: `pytest tests/contract/test_attribution_schema.py -v && echo "attribution schema test passed"` . **Depends on**: T006b.
- [ ] T039 [P] [US3] Integration test for IoU stability calculation in `tests/integration/test_stability.py`. **Verification**: `pytest tests/integration/test_stability.py -v && echo "stability integration test passed"` .

### Implementation for User Story 3

- [ ] T042 [P] [US3] Implement InputXGrad heatmap generation in `code/explain/inputxgrad.py`. **Verification**: `python code/explain/inputxgrad.py --image data/processed/test/sample_001.png --model models/cnn.pt --output data/explainability/inputxgrad_sample_001.png && test -f data/explainability/inputxgrad_sample_001.png && echo "InputXGrad generated"` . **Depends on**: T020.
- [ ] T043 [P] [US3] Implement augmentation pipeline for stability testing (`code/explain/stability.py`) – rotations ±10°, Gaussian noise σ=0.01, brightness jitter ±10%. **Verification**: `python code/explain/stability.py --augment --image data/processed/test/sample_001.png --count 5 && test -d aug_views && echo "augmentations created"` .
- [ ] T044 [P] [US3] Calculate IoU between InputXGrad heatmaps of augmented views. **Verification**: `python code/explain/stability.py --iou --input data/explainability/augmented/ && python -c "import json; d=json.load(open('data/explainability/iou_scores.json')); assert 'mean_iou' in d"` .
- [ ] T045 [P] [US3] Generate stability report `stability_report.json` with schema `{ "mean_iou": float, "std_iou": float, "images_analyzed": int }`. **Verification**: `python -c "import json; d=json.load(open('data/explainability/stability_report.json')); assert all(k in d for k in ['mean_iou','std_iou','images_analyzed'])"` .
- [ ] T046 [P] [US3] Implement validation script `code/explain/validate.py` that loads `stability_report.json`, validates against `contracts/attribution_schema.schema.yaml`. **Verification**: `python code/explain/validate.py && echo "validation passed"` .
- [ ] T048 [P] [US3] Run full attribution validation (`code/explain/validate.py`) and confirm exit code 0. **Verification**: `python code/explain/validate.py && echo "all attribution checks passed"` .

**Checkpoint**: All user stories functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T047a [P] Implement benchmark script `code/utils/benchmark_pipeline.py` to measure full pipeline runtime, outputting `data/benchmarks/pipeline_runtime.json` with fields `total_time_seconds` and `pipeline_steps`. **Verification**: `python code/utils/benchmark_pipeline.py && python -c "import json; d=json.load(open('data/benchmarks/pipeline_runtime.json')); assert 'total_time_seconds' in d"` . **Depends on**: T005, T013, T023b, T042.
- [ ] T047b [P] Run pipeline benchmark on full dataset. **Verification**: `python code/utils/benchmark_pipeline.py && test -f data/benchmarks/pipeline_runtime.json && echo "pipeline benchmark completed"` .
- [ ] T050 [P] Code cleanup and refactoring: remove unused imports (`ruff check . --select=F401`), enforce snake_case naming. **Verification**: `ruff check . --select=F401` returns 0.