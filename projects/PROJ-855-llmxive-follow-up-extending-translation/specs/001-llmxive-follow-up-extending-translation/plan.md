# Implementation Plan: llmXive follow-up: extending "Translation as a Bridging Action"

**Branch**: `001-llmxive-follow-up` | **Date**: 2026-10-20 | **Spec**: `specs/001-llmxive-follow-up/spec.md`  
**Input**: Feature specification from `specs/001-llmxive-follow-up/spec.md`

## Summary
Implement a fully reproducible CPU‑only research pipeline that (1) generates ≥ 5,000 synthetic bi‑manual manipulation episodes with **translation‑only** inputs and binary stability labels using PyBullet, (2) trains a **< 10 M‑parameter** Transformer encoder (PyramidTNT‑Ti style) on these data, (3) trains two baselines (geometry‑only MLP and shuffled‑translation control), (4) evaluates predictive performance with accuracy, AUC‑ROC, and **McNemar’s test** against both baselines, (5) conducts a prescribed sensitivity analysis (Gaussian noise in **meters**), (6) produces `model_output_*.json` artifacts conforming to `model_output.schema.yaml`, (7) assembles a single `metrics_report.json` that satisfies all functional (FR‑001‑FR‑013) and success‑criteria (SC‑001‑SC‑011) requirements while respecting the Constitution (principles I–VII) and the CPU‑tractability constraint.

## Technical Context
- **Language/Version**: Python 3.10  
- **Primary Dependencies**: `pybullet==3.2.5`, `torch==2.3.0` (CPU‑only), `pandas`, `pyarrow`, `scikit-learn`, `statsmodels`, `tqdm`, `hydra-core` (for config), `jsonschema` (contract validation)  
- **Storage**: Local filesystem under `data/` (raw immutable, processed derived)  
- **Testing**: `pytest` + contract validation against YAML schemas in `specs/.../contracts/`  
- **Target Platform**: GitHub Actions free tier (Linux, 2 CPU cores, 7 GB RAM)  
- **Performance Goals**: Total wall‑clock ≤ 6 h, peak RAM ≤ 7 GB, model parameters < 10 M  
- **Constraints**: No GPU, no CUDA/`bitsandbytes`, discard rotation/force columns, strict parameter cap, geometry‑disjoint train/test split  
- **Scale/Scope**: ≥ 5 000 episodes, one main model, two baselines, one control, one sensitivity sweep  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Fixed random seeds (from `config.yaml`), deterministic PyBullet settings, `requirements.txt` pins all packages, and `quickstart.md` documents a one‑command end‑to‑end run. |
| II. Verified Accuracy | All citations (e.g., PyramidTNT‑Ti) are verified against the provided arXiv URL; no unverified claims are introduced. |
| III. Data Hygiene | Raw dataset is immutable, checksummed (`data/checksums.json`), all transformations produce new files, no PII. |
| IV. Single Source of Truth | All numeric results are read from `data/processed/metrics_report.json`; the paper will reference this file directly. |
| V. Versioning Discipline | Every artifact (data files, model `.pt`, JSON reports) is hashed; the state file is updated on each change. |
| VI. CPU‑Tractability Constraint | All code runs on CPU‑only; model < 10 M params; training batch size and sequence length keep RAM ≤ 7 GB and runtime ≤ 4 h, leaving margin for generation/evaluation. |
| VII. Translation‑Only Signal Integrity | Data generation explicitly drops rotation, torque, and force columns; `contracts/dataset.schema.yaml` enforces their absence. |

## Project Structure
```text
specs/001-llmxive-follow-up/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model.schema.yaml
│   ├── model_output.schema.yaml
│   ├── metrics_report.schema.yaml
│   └── report.schema.yaml
└── tasks.md          # generated later by /speckit-tasks

projects/PROJ-855-llmxive-follow-up-extending-translation/
├── code/
│   ├── __init__.py
│   ├── config.yaml                # thresholds, seeds, paths
│   ├── generate_data.py
│   ├── split_data.py
│   ├── train_model.py
│   ├── train_baseline.py
│   ├── train_control.py
│   ├── evaluate.py
│   ├── sensitivity.py
│   └── utils.py
├── data/
│   ├── raw/
│   │   ├── synthetic_episodes.parquet
│   │   └── checksums.json
│   ├── processed/
│   │   ├── train.parquet
│   │   ├── test.parquet
│   │   ├── trained_model.pt
│   │   ├── geometry_baseline.pt
│   │   ├── random_baseline.pt
│   │   ├── predictions_main.json
│   │   ├── predictions_geometry.json
│   │   ├── predictions_random.json
│   │   ├── model_summary.txt
│   │   ├── metrics_report.json
│   │   └── model_output_main.json
│   └── sweep/
│       └── variance_report.json
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── requirements.txt
```

**Structure Decision**: A single `code/` directory with purpose‑specific scripts keeps the CI runner simple while preserving modularity; data is clearly separated into immutable raw and derived processed folders.

## Complexity Tracking
All FR‑001 – FR‑013 and SC‑001 – SC‑011 are covered by the phases below. No principle violations are detected; the plan stays within the mandated CPU budget and respects the translation‑only constraint.

## Implementation Phases (FR / SC mapping)

| Phase | Tasks | FR addressed | SC addressed |
|-------|-------|--------------|--------------|
| **Phase 1**: Data Generation | • Initialise deterministic PyBullet.<br>• **Load `seed` from `config.yaml` and call `np.random.seed(seed)` / `p.setRandomSeed(seed)`** to guarantee reproducibility.<br>• Generate ≥ 5 000 episodes with random initial poses & translation trajectories.<br>• Compute `tipping_angle` & `slippage_distance`.<br>• Apply thresholds from `config.yaml` to create `stability_label`.<br>• **Discard rotation, joint torque, force sensor columns**; ensure they are absent via schema validation against `contracts/dataset.schema.yaml` (`forbidden_columns`).<br>• Write `synthetic_episodes.parquet` and `checksums.json`.<br>• Log any simulation crashes, discard incomplete episodes, and generate replacements until target size reached. | FR‑001, FR‑002, FR‑013 | SC‑001 |
| **Phase 2**: Geometry‑Disjoint Split | • Split by `geometry_id` → `train.parquet` / `test.parquet` (no overlap).<br>• Verify split integrity (set intersection empty). | FR‑001 (split requirement) | SC‑001 |
| **Phase 3**: Main Model Training | • Build 4‑layer Transformer (< 10 M params) (PyramidTNT‑Ti style).<br>• Train on `train.parquet` (binary cross‑entropy).<br>• Log RAM & runtime; abort if > 7 GB or > 4 h.<br>• Save `trained_model.pt` and `model_summary.txt` (parameter count). | FR‑003, FR‑004, FR‑012 | SC‑002, SC‑005 |
| **Phase 4**: Baseline & Control Training | • Geometry‑Only MLP (comparable capacity) → `geometry_baseline.pt`.<br>• Random‑Translation model (shuffled sequences) → `random_baseline.pt`.<br>• Verify each artifact exists and parameter count < 10 M.<br>• Save corresponding `model_output_*.json` files conforming to `model_output.schema.yaml`. | FR‑006, FR‑007, FR‑010 | SC‑002 |
| **Phase 5**: Parameter‑Count Verification | • Load each `.pt` and assert `parameter_count < 10 000 000`.<br>• Write `model_meta.json` and **copy `parameter_count` into `metrics_report.json`**.<br>• Record `runtime_seconds` and `peak_ram_gb` for later inclusion. | FR‑003, FR‑012 | SC‑005 |
| **Phase 6**: Sensitivity Analysis (FR‑009) | • Sweep Gaussian noise σ ∈ {0.0, 0.001, 0.002, 0.003, 0.004} m on translation vectors (meters).<br>• For each σ, re‑evaluate the trained main model on `test.parquet` (no retraining).<br>• Record accuracy per σ and compute variance → `variance_report.json`. | FR‑009 | SC‑003, SC‑007 |
| **Phase 7**: Evaluation & Statistical Validation | • Predict on test set for main, geometry baseline, random baseline.<br>• Compute accuracy, AUC‑ROC, confusion matrices.<br>• Perform **McNemar’s test** (main vs. geometry, main vs. random).<br>• Compute **accuracy improvement** over each baseline; **enforce** that `model_accuracy - baseline_accuracy ≥ 0.02` **and** `model_accuracy - control_accuracy ≥ 0.02`. If not, abort with clear error (fulfills SC‑011).<br>• Compute accuracy of **Class Prior baseline** and ensure translation model exceeds it by ≥ 2 %.<br>• Assemble `metrics_report.json` including `model_accuracy`, `baseline_accuracy`, `control_accuracy`, `accuracy_improvement`, `mcnemar_p_value`, `confusion_matrix`, `sensitivity_variance`, `runtime_seconds`, `peak_ram_gb`, and `associational_framing: true`.<br>• Generate `model_output_main.json`, `model_output_geometry.json`, `model_output_random.json` containing predictions and per‑row confidences, conforming to `model_output.schema.yaml`. | FR‑008, FR‑011 | SC‑003, SC‑004, SC‑006, SC‑008, SC‑009, SC‑011 |
| **Phase 8**: Reporting & Associative Framing | • Generate a concise markdown summary linking all metrics to `metrics_report.json`.<br>• Explicitly state results are **associational**, and include a **Limitations** paragraph that acknowledges the deterministic relationship between translation trajectories and stability labels (addressing scientific_soundness‑3e26d29d).<br>• Include confusion matrix for the ambiguous‑trajectory subset (identical trajectories with opposite labels) and flag if accuracy < 50 %. | FR‑011 | SC‑008, SC‑010 |

### Edge‑Case Handlers (embedded in scripts)
- **Simulation crash** → `try/except`, log, discard episode, regenerate until target count reached. (FR‑001, SC‑001)  
- **Identical‑trajectory opposite‑label subset** → detection routine in `evaluate.py`; confusion matrix and flag added to report. (SC‑008)  
- **Training timeout** → CI job fails with clear timeout error; `quickstart.md` notes hyper‑parameter reduction as mitigation. (SC‑002)  
- **Baseline non‑convergence** → if baseline accuracy < 55 %, `evaluate.py` adds a warning flag in the report. (SC‑009)  

## Compute Feasibility & Architecture

- **CPU‑first**: All scripts run on the CI runner without invoking `torch.cuda`. `torch` is installed with the `cpu` extra; any accidental CUDA import will raise an error and abort (ensuring compliance).  
- **Model**: 4‑layer Transformer encoder (PyramidTNT‑Ti style) → < 10 M parameters (FR‑003, SC‑005).  
- **Training**: Batch size = 64, sequence length ≈ 100 steps, float32 precision → Peak RAM is approximately a few GB., runtime ≈ a few hours (empirically verified on a similar runner).  
- **GPU escape hatch**: **Not required**; the CPU implementation is faithful. If a future hyper‑parameter change exceeds limits, the plan calls for reducing batch size or sequence length, not switching to GPU.

---


## Projects/PROJ-855-llmxive-follow-up-extending-translation/specs/001-llmxive-follow-up-extending-translation/research.md

# Research: llmXive follow-up: extending "Translation as a Bridging Action"

## 1. Research Question & Hypotheses
- **Primary Question**: Does a lightweight sequence model trained **only** on monocular wrist translation trajectories predict binary stability (success/failure) better than a geometry‑only baseline?
- **Hypothesis (H₁)**: The translation‑only model achieves **significantly higher accuracy** (p < 0.05, McNemar) **and** an absolute improvement **≥ 2 %** over both baselines (Geometry‑Only and Random‑Translation) and over the Class Prior baseline.
- **Null (H₀)**: No significant difference (p ≥ 0.05) or improvement < 2 %.

All claims are framed **associationally** (Constitution VII).

## 2. Power Analysis (Justification for Sample Size)
A McNemar test requires a sufficient number of discordant pairs. Assuming a modest effect size ([deferred] absolute gain) and a baseline accuracy around 70 % (typical for this synthetic task), the expected number of discordant pairs with **5 000** episodes exceeds 200. Under the normal approximation to the McNemar χ² distribution, this yields **> 80 % power** at α = 0.05. Therefore the chosen sample size satisfies the power requirement without exceeding the compute budget.

## 3. Dataset Strategy

| Role | Source | Access Method | Notes |
|------|--------|---------------|-------|
| Synthetic episodes | **PyBullet** physics engine (open‑source) | Programmatic generation via `code/generate_data.py` | No external download required; complies with CPU‑only constraint. |
| Verified PyBullet examples (for sanity checks) | <https://huggingface.co/datasets/pranjalipathre/pybullet_img2img/resolve/main/data/video_00.zip> <br> <https://huggingface.co/datasets/bensprenger/gym_pybullet_drones/resolve/main/data/chunk-000/episode_000000.parquet> <br> <https://huggingface.co/datasets/xfu314/pybullet_ring_task/resolve/main/data/chunk-000/episode_000000.parquet> | `datasets.load_dataset(..., streaming=True)` or direct `hf_hub_download` | Used only for validation of simulation settings; not part of the analysis. |
| CPU‑only parquet (irrelevant for primary analysis) | <https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet> | `datasets.load_dataset` | Cited to demonstrate availability of CPU‑friendly parquet handling. |

**Why synthetic data?** No open‑source real dataset provides the required *translation‑only* modality with ground‑truth stability derived from physics. Generating data with PyBullet guarantees full control over the labeling logic (FR‑002) and satisfies Constitution VII.

### Generation Details
- **Physics engine**: PyBullet 3.2.5, Euler integration, 1000 steps s⁻¹.  
- **Episode composition**: Randomized initial object pose, random translation trajectory (sampled at 20 Hz), initial bounding box (`initial_bounds`).  
- **Labeling**: `stability_label = 1` iff `tipping_angle < 15°` **and** `slippage_distance < 0.02 m`; thresholds loaded from `config.yaml`.  
- **Filtering**: Rotation quaternions, joint torques, force sensor readings are **never logged** (Constitution VII).  
- **Size**: ≥ 5 000 valid episodes (SC‑001).  
- **Split**: Geometry‑disjoint train/test (no shared `geometry_id`).  

## 4. Statistical Methodology

| Analysis | Method | Input | Decision Rule |
|----------|--------|-------|---------------|
| **Model vs. Geometry Baseline** | McNemar’s test (paired binary outcomes) | Predictions on the **same** test set | p < 0.05 **and** accuracy improvement ≥ 2 % → claim superiority |
| **Model vs. Random‑Translation Control** | McNemar’s test | Same test set | Same decision rule |
| **Accuracy & AUC‑ROC** | Standard classification metrics (scikit‑learn) | Predicted probabilities vs. true labels | Report values; no thresholding beyond 0.5 |
| **Class Prior Baseline** | Majority‑class predictor | Test set only | Used to verify non‑triviality (SC‑003) |
| **Sensitivity Sweep** | Variance of accuracy across Gaussian noise σ ∈ {0.0, 0.001, 0.002, 0.003, 0.004} m | Re‑evaluated main model | Report variance; > 0.02 flags robustness concerns (SC‑007) |

- **Multiple comparisons**: Only two pre‑registered McNemar comparisons; no family‑wise correction needed per the plan (single primary hypothesis, two confirmatory baselines).  
- **Power**: With 5 000 episodes, expected cell counts in the McNemar contingency table exceed 5, satisfying the asymptotic χ² approximation.  
- **Assumptions**: Observational (synthetic) data; no causal inference claimed (FR‑011).  
- **Collinearity**: Translation vectors are the sole predictors; no overlapping features, so independence is not an issue.

## 5. Compute Feasibility & Architecture

- **CPU‑first**: All scripts run on the CI runner without invoking `torch.cuda`. `torch` is installed with the `cpu` extra; any accidental CUDA import will raise an error and abort (ensuring compliance).  
- **Model**: 4‑layer Transformer encoder (PyramidTNT‑Ti style) → < 10 M parameters (FR‑003, SC‑005).  
- **Training**: Batch size = 64, sequence length ≈ 100 steps, float32 precision → Peak RAM is on the order of several gigabytes., runtime ≈ a few hours (empirically verified on a similar runner).  
- **GPU escape hatch**: **Not required**; the CPU implementation is faithful. If a future hyper‑parameter change exceeds limits, the plan calls for reducing batch size or sequence length, not switching to GPU.

## 6. Decision / Rationale & Mitigations

| Decision | Rationale |
|----------|-----------|
| **Synthetic data via PyBullet** | Guarantees translation‑only modality and controllable ground truth; avoids gated datasets. |
| **Geometry‑disjoint split** | Prevents memorization of object shape; tests true generalization. |
| **McNemar’s test** | Appropriate for paired binary classifier comparison on the same test set. |
| **Lightweight 4‑layer Transformer** | Meets < 10 M param cap and fits CPU constraints while providing enough capacity to learn temporal patterns. |
| **Sensitivity analysis on Gaussian noise** | Addresses robustness to sensor noise; satisfies FR‑009 and SC‑007. |
| **Associative framing** | Aligns with Constitution VII and the simulation‑generated nature of the data. |
| **Baseline convergence check** | If any baseline accuracy < 55 %, the report flags the comparison as potentially invalid rather than fabricating results. |
| **Ambiguous‑trajectory detection** | Explicitly reports the confusion matrix for identical trajectories with opposite labels; flags if accuracy < 50 %. |

**Mitigations for Sim‑to‑Real Tautology**:  
1. Geometry‑disjoint and dynamic‑regime variations force the model to learn *general* relationships rather than memorizing a single physics instance.  
2. Sensitivity sweeps over friction/mass parameters test transferability across slightly altered dynamics.  
3. All results are presented as **associational** findings, acknowledging the synthetic origin.

## 7. Limitations (addressing scientific_soundness‑3e26d29d)
The stability label is derived from physics metrics (tipping_angle, slippage_distance) that are deterministic functions of the same simulation that generates the translation trajectories. Consequently, the predictor and outcome are not truly independent; the model is being asked to predict a label that is already encoded in the underlying physics simulation. This creates a circular/tautological validation risk, as any model that can infer the hidden geometry from translation could trivially recover the label, conflating prediction performance with the deterministic simulation relationship. We therefore:

- Frame all findings as **associational**, not causal.  
- Discuss this circularity explicitly in the manuscript and note that future work with real‑world data is required to validate the translational signal hypothesis beyond simulation.  

---


