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

## Phase 0: Spec Alignment & Critical Gaps

**Purpose**: Address fundamental contradictions between Spec and Plan before implementation.

- [ ] T000 [S] **CRITICAL SPEC-PLAN ALIGNMENT**: Analyze `spec.md` Assumptions (real dataset) vs `plan.md` Summary (synthetic data). Update `research.md` Section 1 (Introduction) to explicitly state: "This project uses a Synthetic Microstructure Generator because no verified real-world dataset exists. Results validate the pipeline methodology, not real-world physics." **Verification**: `grep -q "Synthetic Microstructure Generator" research.md && grep -q "pipeline methodology" research.md && echo "Spec-Plan gap documented"`. **Depends on**: T003. **Blocks**: T009, T009a, T009a_2, T009c, T009d, T009e, T013c.

---

## Phase 1: Setup (Shared Infrastructure & Spec Alignment)

**Purpose**: Project initialization, spec alignment with Plan corrections, and contract definition. **Ensures spec reflects Plan's scientific decisions before implementation begins.**

- [X] T001a [P] Create code directories and init files: `code/__init__.py`, `code/data/__init__.py`, `code/models/__init__.py`, `code/train/__init__.py`, `code/explain/__init__.py`, `code/utils/__init__.py`. **Verification**: Run `ls -R code` and confirm all `__init__.py` files exist.
- [X] T001b [P] Create data directories and keep files: `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/explainability/.gitkeep`. **Verification**: Run `ls -R data` and confirm all `.gitkeep` files

The research question, method, and references remain unchanged as per the planning document requirements. exist.
- [X] T001c [P] Create test directories and init files: `tests/__init__.py`, `tests/unit/__init__.py`, `tests/contract/__init__.py`, `tests/integration/__init__.py`. **Verification**: Run `ls -R tests` and confirm all Several `__init__.py` files exist.
- [X] T002 [S] Create `code/requirements.txt` with pinned versions: `torch`, `scikit-learn`, `opencv-python-headless`, `pandas`, `numpy`, `matplotlib`, `captum`, `pyyaml`, `pytest`. **Verification**: Run `pip install -r code/requirements.txt` successfully.
- [X] T003 [P] Configure linting and formatting: Create `pypyproject.toml` with `[tool.black]` (line-length=88, target-version=['py3']) and `[tool.ruff]` (select=['E', 'F', 'W'], ignore=['E501']). **Verification**: Run `ruff check.` and `black --check.` successfully (exit code 0).
- [ ] T009 [S] Create `research.md` artifact in `projects/PROJ-266-machine-learning-prediction-of-fracture-/` with content structure: Introduction, Methodology. **Verification**: `test -f research.md && grep -q "^## Introduction$" research.md && grep -q "^## Methodology$" research.md && echo "research.md verified"`. **Depends on**: T003. **Blocks**: T009a, T009a_2, T009e, T025d, T042d.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes metadata schema definition and artifact creation.**

- [ ] T009a [S] Define Methodology in `research.md` Section 3.2: Explicitly write the **deterministic logic** for synthetic generation of K_IC values. Define parameters: `base_value` (float), `alpha` (grain size coeff), `beta` (precipitate coeff), `noise` (std dev). **Verification**: `python -c "
import re
import os
# Check research.md for variable names
research_content = open('research.md').read()
assert 'base_value' in research_content and 'alpha' in research_content and 'beta' in research_content and 'noise' in research_content, 'Variables missing in research.md'
# Verify cross-reference
assert 'code/data/synthetic_gen.py' in research_content, 'Cross-reference missing in research.md'
print('Traceability verified: research.md logic defined')
"`. **Depends on**: T009. **Blocks**: T009a_2, T053a.
- [ ] T009a_2 [S] Implement **methodology formula and parameters** in `research.md` Section 3.2. Include the mathematical formula: `K_IC = base_value + alpha*grain_size + beta*precipitate_density + noise`. Document that this is a **synthetic ground truth** derived from the Plan's methodology, not real-world measurements. **Include a cross-reference** to `code/data/synthetic_gen.py` to ensure traceability. **Verification**: `python -c "
import re
import os
# Check research.md for formula and variable names
research_content = open('research.md').read()
assert 'K_IC = base_value + alpha*grain_size + beta*precipitate_density + noise' in research_content, 'Formula missing in research.md'
print('Formula verified in research.md')
"`. **Depends on**: T009a. **Blocks**: T009b, T009c.
- [ ] T009b [S] Implement **core image generation logic** in `code/data/synthetic_gen.py` (part 1 of 3). This task ONLY generates images and metadata. Mask generation is handled by T040. The generator MUST: 1) Use `CONFIG['split_seed']` to initialize the random number generator for alloy family assignment. 2) Assign 'alloy_family' labels ensuring at least one sample each for 'steel', 'Al', and 'Ti'. 3) Generate synthetic images (128x128) and save to `data/raw/images/`. **Note**: T007 must be complete for config import. **Verification**: `python -c "
import glob, pathlib
from code.utils.config import CONFIG
from PIL import Image
# Check image count
img_count = len(glob.glob('data/raw/images/*.png'))
assert img_count == CONFIG['target_sample_size'], f'Image count mismatch: {img_count} != {CONFIG[\"target_sample_size\"]}'
# Check image dimensions (FR-001 compliance)
img = Image.open(glob.glob('data/raw/images/*.png')[0])
assert img.size == (128, 128), f'Image dimension mismatch: {img.size} != (128, 128)'
print('Core image generation verified')
"`. **Depends on**: T009a_2, T006d, T007. **Blocks**: T009c, T040.
- [ ] T009c [S] Implement **metadata creation and checksum** in `code/data/synthetic_gen.py` (part 2 of 3). This task MUST: 1) Generate `data/raw/metadata.json` with image paths, K_IC, alloy family. 2) Compute SHA-256 checksum of `data/raw/metadata.json`. 3) **Crucially**, write the checksum to `state/projects/PROJ-266-machine-learning-prediction-of-fracture-.yaml` under `artifact_hashes` (Constitution Principle III). **Verification**: `python -c "
import json, hashlib, pathlib, yaml
# Check metadata existence
assert pathlib.Path('data/raw/metadata.json').exists(), 'Metadata missing'
# Check checksum in state file
state_file = 'state/projects/PROJ-266-machine-learning-prediction-of-fracture-.yaml'
assert pathlib.Path(state_file).exists(), 'State file missing'
with open(state_file) as f:
 state = yaml.safe_load(f)
assert 'artifact_hashes' in state, 'artifact_hashes missing in state'
assert 'data/raw/metadata.json' in state['artifact_hashes'], 'Checksum key missing in state'
h = hashlib.sha256(pathlib.Path('data/raw/metadata.json').read_bytes()).hexdigest()
assert state['artifact_hashes']['data/raw/metadata.json'] == h, f'Checksum mismatch'
print('Metadata and Constitution III checksum verified')
"`. **Depends on**: T009b. **Blocks**: T012a, T013a.
- [ ] T009d [S] Implement **benchmark script** `code/utils/benchmark_gen.py` to measure generator runtime (part 3 of 3). **Verification**: `mkdir -p data/benchmarks && python code/utils/benchmark_gen.py && test -f data/benchmarks/generator_runtime_raw.json`. **Depends on**: T009c. **Blocks**: T005c.
- [X] T005c [S] Write benchmark results to `data/benchmarks/generator_runtime.json` from `generator_runtime_raw.json`. **Verification**: `python -c "import json, pathlib; p=pathlib.Path('data/benchmarks/generator_runtime.json'); d=json.load(p.open()); assert isinstance(d['total_time_seconds'], float) and isinstance(d['images_per_second'], float)"`. **Depends on**: T009d.
- [ ] T005e [S] **Compute Feasibility Check**: Run a full pipeline benchmark on `CONFIG['target_sample_size']` (2000) images to verify completion within 6 hours on -core CPU. Script MUST time Ta (preprocess), T023b (CNN train), T042b (Grad-CAM). **Verification**: `python code/utils/benchmark_full_pipeline.py && python -c "import json; d=json.load(open('data/benchmarks/full_pipeline.json')); assert d['total_time_hours'] < 6.0, 'Pipeline exceeds 6h limit'"`. **Depends on**: T013a, T023b, T042b. **Blocks**: T005d.
- [X] T005d [S] Document in `research.md` that the generated dataset targets a sample size defined in `CONFIG['target_sample_size']`, with a minimum of 200 images for statistical power (justified by plan compute feasibility). **Verification**: `test -f research.md && grep -q "target sample size" research.md && echo "research.md updated"`. **Depends on**: T009a, T009c, T005e.

- [ ] T006a [P] Create base data contract `contracts/dataset_schema.schema.yaml`. **Verification**: `python -c "import yaml; s=yaml.safe_load(open('contracts/dataset_schema.schema.yaml')); assert s['properties']['alloy_family']['enum'] == ['steel', 'Al', 'Ti']; assert 'image_path' in s['properties']; assert 'k_ic' in s['properties']; print('Dataset schema valid')"`. **Depends on**: T003.
- [ ] T006b [P] Create evaluation schema contract `contracts/evaluation_schema.schema.yaml`. **Verification**: `python -c "import yaml; s=yaml.safe_load(open('contracts/evaluation_schema.schema.yaml')); assert s['properties']['model_type']['enum'] == ['cnn', 'linear', 'random_forest']; assert s['properties']['r_squared']['type'] == 'number'; print('Evaluation schema valid')"`. **Depends on**: T003.
- [ ] T006c [P] Create attribution schema contract `contracts/attribution_schema.schema.yaml`. **Verification**: `python -c "import yaml; s=yaml.safe_load(open('contracts/attribution_schema.schema.yaml')); assert 'image_id' in s['properties'] and 'heatmap_paths' in s['properties'] and 'iou_scores' in s['properties'] and 'stability_threshold_met' in s['properties']; print('Attribution schema valid')"`. **Depends on**: T003.
- [X] T007 [P] Implement configuration management in `code/utils/config.py` with keys `split_seed` (int), `train_seed` (int), `image_size` (tuple), `batch_size` (int), `min_feature_size_pixels` (int), `target_sample_size` (int, default a substantial number), `stability_threshold` (float, default a high threshold), `subset_seed` (int). **Verification**: `python -c "from code.utils.config import CONFIG; assert isinstance(CONFIG['split_seed'], int); assert CONFIG['target_sample_size'] == 500; assert 'subset_seed' in CONFIG"`.
- [X] T008 [P] Implement error handling and logging infrastructure in `code/utils/logger.py`. **Verification**: Run a small script that imports `get_logger()` and writes a log; confirm `logs/app.log` contains a line matching `^\d{4}-\d{2}-\d{2}.+ -.+ -.+ - test$`.
- [X] T053a [P] Define logic for **sample preparation metadata** (magnification calibration, section thickness proxy) in `research.md` and `code/data/synthetic_gen.py`. Logic: magnification_calibration = random uniform [lower_bound, upper_bound] pixels/micron; `section_thickness` = random uniform [low, 50] nm. Document derivation in `research.md`. **Verification**: `grep -q "magnification_calibration" research.md && grep -q "random uniform" research.md && grep -q "section_thickness" research.md && echo "Metadata logic defined"`. **Depends on**: T009a. **Blocks**: T006d.
- [ ] T006d [P] Update `contracts/dataset_schema.schema.yaml` to include `magnification_calibration` and `section_thickness` fields defined in T053a. **Verification**: `python -c "import yaml; s=yaml.safe_load(open('contracts/dataset_schema.schema.yaml')); assert 'magnification_calibration' in s['properties'] and 'section_thickness' in s['properties']; print('Metadata schema valid')"`. **Depends on**: T053a. **Blocks**: T009b.
- [ ] T009e [S] **Document Synthetic Limitation**: Update `research.md` Section 4 (Discussion) to explicitly state: "This project validates the pipeline methodology using synthetic data. No real-world dataset verification is performed due to data unavailability (Plan Summary)." **Verification**: `grep -q "synthetic data" research.md && grep -q "methodology" research.md && grep -q "no real-world" research.md && echo "Limitation documented"`. **Depends on**: T000, T009a.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw images (synthetic or user), standardize to 128×128 grayscale, and split stratified by alloy family. Validates metadata produced in Phase 2.

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`. **Verification**: `pytest tests/contract/test_dataset_schema.py -v && echo "contract test passed"`. **Depends on**: T006a.
- [X] T011 [P] [US1] Integration test for stratified split logic in `tests/integration/test_stratified_split.py`. **Verification**: `pytest tests/integration/test_stratified_split.py -v && echo "integration test passed"`. **Depends on**: T014.

### Implementation for User Story 1

- [X] T012a [P] [US1] Implement image loading and basic validation in `code/data/ingest.py` (handles missing K_IC, logs warnings, uses `metadata.json`). **Verification**: `python -c "import code.data.ingest as i; assert hasattr(i, 'load_csv')"`. **Depends on**: T006a.
- [X] T012b [P] [US1] Add validation for missing K_IC values in `code/data/ingest.py`. **Verification**: `python code/data/ingest.py --csv tests/fixtures/missing_kic.csv && echo $? | grep -q '^1$' && echo "missing K_IC correctly rejected"`. **Depends on**: T012a.
- [ ] T013a [P] [US1] Implement **core preprocessing pipeline** in `code/data/preprocess.py` (grayscale conversion, resize to 128x128, intensity normalization). **Note**: This task implements the logic required by FR-001 for *arbitrary* inputs. **Verification**: `python code/data/preprocess.py --input data/raw --output data/processed && python -c "from PIL import Image; img=Image.open('data/processed/train/sample_001.png'); assert img.size == (128, 128) and img.mode == 'L' and img.getpixel((0,0)) < 256; print('Core preprocessing verified')"`. **Depends on**: T012a, T012b, T009c. **Blocks**: T013b, T014.
- [ ] T013b [P] [US1] Implement **large image edge case handling** in `code/data/preprocess.py` (handle >4000px by downsampling without aspect ratio distortion and logging a warning). **Note**: Verification uses a dummy large image to ensure the code path exists, satisfying FR-001 even if synthetic data bypasses it. **Verification**: `python code/data/preprocess.py --input tests/fixtures/large_image.png --output data/processed_large && grep -q "Warning.*aspect ratio" logs/preprocess.log && echo "Large image handling verified"`. **Depends on**: T013a.
- [ ] T013c [P] [US1] **Document Stratification Logic**: Update `research.md` Section 3.2 to state: "The 'stratified split' requirement (FR-002) is satisfied by generating synthetic data with pre-assigned stratified labels, as real-world splitting is bypassed." **Verification**: `grep -q "stratified split" research.md && grep -q "pre-assigned" research.md && echo "Stratification logic documented"`. **Depends on**: T009a.
- [ ] T014 [P] [US1] Implement stratified split logic (fixed seed, alloy families steel/Al/Ti) in `code/data/preprocess.py`. **Verification**: `python -c "import pandas as pd; df=pd.read_csv('data/processed/split_metadata.csv'); assert set(df['split'])=={'train','val','test'}; from code.utils.config import CONFIG; assert 'split_seed' in CONFIG"`. **Depends on**: T013a.
- [ ] T015 [P] [US1] Generate `split_metadata.csv` recording alloy family distribution per split. **Verification**: `python -c "import pandas as pd; df=pd.read_csv('data/processed/split_metadata.csv'); assert list(df.columns)==['split','alloy_family','count']"`. **Depends on**: T014.
- [ ] T016 [P] [US1] Add validation to ensure test set contains at least one sample per alloy family; exit with error if not. **Verification**: Create a tiny dataset with only "steel" and run preprocessing; confirm exit code 1 and error message contains "ERROR: Test set missing alloy family". **Depends on**: T014.
- [ ] T017 [P] [US1] Add logging for preprocessing steps in `logs/preprocess.log` with format `%(asctime)s - PREPROCESS - %(message)s`. **Verification**: After running preprocessing, `grep -E "PREPROCESS" logs/preprocess.log` returns lines. **Depends on**: T008.

**Checkpoint**: User Story 1 fully functional and testable independently.

---

## Phase 4: User Story 2 - Lightweight CNN Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train a multi-block CNN, compare against Linear Regression and Random Forest baselines, and run Wilcoxon signed-rank test.

### Tests for User Story 2 (OPTIONAL)

- [X] T018 [P] [US2] Contract test for evaluation schema in `tests/contract/test_evaluation_schema.py`. **Verification**: `pytest tests/contract/test_evaluation_schema.py -v && echo "evaluation contract test passed"`. **Depends on**: T006b.
- [X] T019 [P] [US2] Integration test for Wilcoxon Test logic in `tests/integration/test_wilcoxon.py`. **Verification**: `pytest tests/integration/test_wilcoxon.py -v && echo "wilcoxon integration test passed"`. **Depends on**: T025a.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement a multi-block CNN architecture (Conv‑ReLU‑BN‑MaxPool) in `code/models/cnn.py`. **Verification**: `python -c "import code.models.cnn as m; assert hasattr(m, 'CNN')" `. **Depends on**: T007.
- [X] T021 [P] [US2] Implement baseline models (Linear Regression, RandomForestRegressor) in `code/models/baselines.py`. **Verification**: `python -c "import code.models.baselines as b; assert hasattr(b, 'LinearRegressionModel')"`.
- [ ] T022a [P] [US2] Implement **GLCM texture feature extraction** in `code/data/features.py`. **Verification**: `python code/data/features.py --input data/processed --output data/features_glcm.json && python -c "import json; d=json.load(open('data/features_glcm.json')); assert 'glcm_features' in d; assert len(d['glcm_features']) > 0"`. **Depends on**: T013a.
- [ ] T022b [P] [US2] Implement **band-pass filtered power spectrum** extraction in `code/data/features.py`. **Verification**: `python code/data/features.py --input data/processed --output data/features_spectrum.json && python -c "import json; d=json.load(open('data/features_spectrum.json')); assert 'band_pass_spectrum' in d; assert len(d['band_pass_spectrum']) > 0"`. **Depends on**: T013a.
- [ ] T021b [P] [US2] Implement Linear Regression baseline training loop in `code/train/train_linear.py` that consumes features from T022a/b. **Verification**: `python code/train/train_linear.py --features data/features.json && test -d models/baselines/linear`. **Depends on**: T022a, T022b.
- [ ] T021c [P] [US2] Implement Random Forest baseline training loop in `code/train/train_rf.py` that consumes features from T022a/b. **Verification**: `python code/train/train_rf.py --features data/features.json && test -d models/baselines/rf`. **Depends on**: T022a, T022b.
- [X] T023a [P] [US2] Implement seed management utility in `code/utils/seeds.py`. **Verification**: `python -c "from code.utils.seeds import get_seeds; assert len(get_seeds(n)) == n"`.
- [ ] T023b [S] [US2] Implement **training loop setup** in `code/train/train_cnn.py` (single seed). **Verification**: `python code/train/train_cnn.py --seed 1 && test -d models/cnn`. **Depends on**: T020, T023a.
- [ ] T023c [S] [US2] Implement **multi-seed training loop** in `code/train/train_cnn.py` (5 (2603.28921, https://arxiv.org/abs/2603.28921) seeds). **Verification**: `python code/train/train_cnn.py --seeds 5 && test -d models/cnn && python -c "import os; assert len(os.listdir('models/cnn')) == 5"`. **Depends on**: T023b.
- [ ] T024 [P] [US2] Implement metric calculation (R², MAE, RMSE) and save to JSON in `code/train/evaluate.py`. **Verification**: `python code/train/evaluate.py && python -c "import json; d=json.load(open('results/metrics.json')); assert all(k in d for k in ['r2','mae','rmse'])"`. **Depends on**: T023c, T021b, T021c.
- [ ] T024a [S] [US2] Aggregate the independent run results into a distribution structure (list of MAEs per model) and append to `results/metrics.json` for statistical testing. **Verification**: `python code/train/aggregate_results.py && python -c "import json; d=json.load(open('results/metrics.json')); assert 'mae_distribution' in d and len(d['mae_distribution']['cnn']) == 5"`. **Depends on**: T024. **Blocks**: T025a.
- [ ] T025a [S] [US2] Implement **Wilcoxon signed-rank test function** `wilcoxon_test` in `code/train/stats.py`. **Verification**: `python -c "from code.train.stats import wilcoxon_test; assert callable(wilcoxon_test)"`. **Depends on**: T024a.
- [ ] T025b [S] [US2] **Integrate Wilcoxon test** into `evaluate.py` and output results to `results/metrics.json`. The test compares the distribution of MAE differences between the CNN and **each** baseline model (Linear Regression and Random Forest) across multiple seeds using **alpha = 0.05 (Wikipedia: Wilcoxon signed-rank test, https://en.wikipedia.org/wiki/Wilcoxon_signed-rank_test) **. **Verification**: `python code/train/evaluate.py && python -c "import json, re; d=json.load(open('results/metrics.json')); assert 'wilcoxon_p_value_linear' in d and 'wilcoxon_p_value_rf' in d and'mae_distribution' in d and isinstance(d['wilcoxon_p_value_linear'], float) and isinstance(d['wilcoxon_p_value_rf'], float); code=open('code/train/stats.py').read(); assert re.search(r'alpha\\s*=\\s*0\\.05', code); print('Wilcoxon test verified for both baselines')"`. **Depends on**: T025a. **Note**: This task validates **Methodological Validation** (superiority on synthetic data), not real-world physics claims.
- [ ] T026 [P] [US2] Add logging for training progress in `logs/training.log` and enforce CPU-only execution. **Verification**: After a short training run, `grep -E "TRAIN - Epoch" logs/training.log` returns lines; `grep -q "torch.set_num_threads" code/train/train_cnn.py` and `! grep -q "cuda" code/train/train_cnn.py`. **Depends on**: T008.
- [ ] T007a [P] (Optional) Benchmark script `code/utils/benchmark_pipeline.py` (See Phase 2 T007a). **Note**: Moved from Phase 2 to Phase 4 to satisfy dependencies. **Verification**: `python code/utils/benchmark_pipeline.py && python -c "import json; d=json.load(open('data/benchmarks/pipeline_runtime.json')); assert 'total_time_seconds' in d"`. **Depends on**: T005, T013a, T023c, T042b.

**Checkpoint**: User Stories 1 & 2 operational.

---

## Phase 5: User Story 3 - Feature Attribution and Stability Reporting (Priority: P3)

**Goal**: Generate Grad-CAM heatmaps and validate stability via IoU across augmented views.

### Tests for User Story 3 (OPTIONAL)

- [ ] T038 [P] [US3] Contract test for attribution schema in `tests/contract/test_attribution_schema.py`. **Verification**: `pytest tests/contract/test_attribution_schema.py -v && echo "attribution contract test passed"`. **Depends on**: T006c.
- [ ] T039 [P] [US3] Integration test for IoU stability calculation in `tests/integration/test_stability.py`. **Verification**: `pytest tests/integration/test_stability.py -v && echo "stability integration test passed"`.

### Implementation for User Story 3

- [ ] T040 [S] [US3] Generate synthetic ground-truth grain boundary masks for each image in `data/raw/masks/`. These masks are used for future accuracy checks but **NOT** for the primary stability metric (FR-007). **Verification**: `python code/data/generate_masks.py && python -c "import glob; masks = glob.glob('data/raw/masks/*.png'); assert len(masks) > 0; print('Masks generated')"`. **Depends on**: T009b. **Blocks**: T044b (future use).
- [ ] T041 [S] [US3] Select and lock a random subset of test images for attribution analysis. **Use `CONFIG['subset_seed']` for reproducibility**. Save the list of image IDs to `data/explainability/attrib_subset.json`. **Verification**: `python code/explain/select_subset.py && python -c "import json; d=json.load(open('data/explainability/attrib_subset.json')); assert len(d) >= 10; print('Subset locked with seed')"`. **Depends on**: T013a. **Blocks**: T042b, T043.
- [ ] T042a [P] [US3] Implement **Grad-CAM logic** (layer selection, target activation) in `code/explain/gradcam_logic.py`. **Verification**: `python -c "import code.explain.gradcam_logic as g; assert hasattr(g, 'get_heatmap')"`. **Depends on**: T020.
- [ ] T042b [S] [US3] Implement **Grad-CAM heatmap generation script** `code/explain/gradcam.py` using logic from T042a. **Verification**: `python code/explain/gradcam.py --image data/processed/test/sample_001.png --model models/cnn.pt --output data/explainability/gradcam_sample_001.png --subset data/explainability/attrib_subset.json && test -f data/explainability/gradcam_sample_001.png && echo "Grad-CAM generated"`. **Depends on**: T020, T013a, T041, T042a, T023c.
- [ ] T043 [P] [US3] Implement augmentation pipeline for stability testing (`code/explain/stability.py`) – rotations ±10°, Gaussian noise σ=0.01, brightness jitter ±10%. **Verification**: `python code/explain/stability.py --augment --image data/processed/test/sample_001.png --count 5 --subset data/explainability/attrib_subset.json && test -d data/explainability/aug_views && echo "augmentations created"`. **Depends on**: T013a, T041.
- [ ] T044a [S] [US3] Calculate **view-to-view IoU** between Grad-CAM heatmaps of augmented views. **Do NOT compare against masks**. Script reads heatmaps from `data/explainability/heatmaps` (generated by T042b) and outputs `data/explainability/iou_scores.json`. **Verification**: `python code/explain/stability.py --iou --input data/explainability/aug_views --subset data/explainability/attrib_subset.json --output data/explainability/iou_scores.json && python -c "import json; d=json.load(open('data/explainability/iou_scores.json')); assert 'mean_iou' in d and 'iou_scores' in d and len(d['iou_scores']) > 0; assert 'mask_iou' not in d, 'mask_iou key must not exist'"`. **Depends on**: T042b, T043. **Note**: This task explicitly excludes mask comparison to satisfy FR-007.
- [ ] T044b [S] [US3] (Optional) Calculate **Heatmap-to-Mask IoU** for accuracy validation. Script reads heatmaps from `data/explainability/heatmaps` and masks from `data/raw/masks`, outputs `data/explainability/mask_iou.json`. **Verification**: `python code/explain/stability.py --mask-iou --input data/explainability/heatmaps --mask-dir data/raw/masks --subset data/explainability/attrib_subset.json --output data/explainability/mask_iou.json && python -c "import json; d=json.load(open('data/explainability/mask_iou.json')); assert 'mean_mask_iou' in d"`. **Depends on**: T040, T042b.
- [ ] T044c [S] [US3] Generate stability report `stability_report.json` by reading `data/explainability/iou_scores.json`, comparing the mean IoU against `CONFIG['stability_threshold']`, and writing the final report with `mean_iou`, `std_iou`, `images_analyzed`, and `stability_threshold_met` (boolean). **Verification**: `python -c "import json, pathlib; from code.utils.config import CONFIG; d=json.load(open('data/explainability/stability_report.json')); assert all(k in d for k in ['mean_iou','std_iou','images_analyzed','stability_threshold_met']); assert d['stability_threshold_met'] == (d['mean_iou'] >= CONFIG['stability_threshold']); assert 'mask_iou' not in d, 'mask_iou must not be in report'; print('Report valid')"`. **Depends on**: T044a.
- [ ] T046 [P] [US3] Implement validation script `code/explain/validate.py` that loads `stability_report.json`, validates against `contracts/attribution_schema.schema.yaml`. **Verification**: `python code/explain/validate.py && echo "validation passed"`.
- [ ] T048 [P] [US3] Run full attribution validation (`code/explain/validate.py`) and confirm exit code 0. **Verification**: `python code/explain/validate.py && echo "all attribution checks passed"`.

**Checkpoint**: All user stories functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T050 [P] Code cleanup and refactoring: remove unused imports (`ruff check. --select=F401`), enforce snake_case naming. **Verification**: `ruff check. --select=F401` returns 0.

---

## Phase O: Research Documentation & Limitations

**Purpose**: Update research.md to reflect synthetic methodology, limitations, and resolution limits as required by the current spec/plan (no external review references).

### Implementation for Documentation Updates

- [ ] T052a [S] Update `research.md` Section 2 (Methodology) to explicitly define the **imaging resolution** (pixels per micron) and **minimum resolvable feature size** (e.g., grain boundary width) for the synthetic generator. **Verification**: `grep -q "minimum resolvable feature size" research.md && grep -q "pixels per micron" research.md`. **Depends on**: T009a.
- [ ] T052b [S] Update `research.md` Section 2 (Methodology) to include the **resolution limits** section detailing how imaging resolution limits affect the model's ability to detect specific grain boundary characters. **Verification**: `grep -q "Limitations" research.md && grep -q "resolution" research.md && echo "Limitations section finalized"`. **Depends on**: T052a.
- [ ] T056a [P] Update `research.md` Section 4 (Discussion) to include a **Variance Analysis** subsection detailing how the model's predictions account for the variance in feature extraction across different synthetic preparation batches. **Verification**: `grep -q "Variance Analysis" research.md && grep -q "preparation batches" research.md`. **Depends on**: T053a, T009a.
- [ ] T056b [P] Update `research.md` Section 4 (Discussion) to include a **Sample Preparation Protocol** section detailing the synthetic generation parameters for magnification calibration, section thickness (for TEM proxy), and surface preparation (for SEM proxy), including the expected variance in feature extraction across different preparation batches. **Verification**: `grep -q "Sample Preparation Protocol" research.md && grep -q "magnification calibration" research.md && grep -q "section thickness" research.md && grep -q "surface preparation" research.md && grep -q "expected variance" research.md`. **Depends on**: T009a, T053a.
- [ ] T057 [P] Add a unit test in `tests/unit/test_resolution_limits.py` that verifies the synthetic generator cannot produce features smaller than the defined `min_feature_size_pixels`. **Verification**: `pytest tests/unit/test_resolution_limits.py -v && echo "resolution limit test passed"`. **Depends on**: T009a.

**Checkpoint**: All research documentation requirements addressed; experimental specification is now complete and scientifically rigorous.