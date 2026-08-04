# Research: Non-Neural Approximation of VLA Priors

## Methodology & Approach

The research investigates whether lightweight, non-neural probabilistic models can approximate the trajectory generation priors of large Vision-Language-Action (VLA) models. The methodology follows a three-stage pipeline: **Ingestion & Clustering**, **Model Distillation**, and **Simulation-Based Evaluation**.

### 1. Dataset Strategy

The project relies on the **Qwen-VLA** training dataset, specifically the text-action pairs required for robot manipulation tasks.

**Verified Datasets**:
- **Primary Source**: `tencent/Hy-Embodied-0.5-VLA-Data` (Parquet format).
 - **URL**: `
 - **Usage**: Ingested via `datasets.load_dataset` with `streaming=True` to manage memory.
 - **Content**: Text instructions and corresponding high-dimensional action trajectories (joint angles, end-effector poses).
- **Secondary Sources**: `bujangkiray/vlang` and `SheatNoisette/vlang-poc-dataset` are listed in the verified block but are **not** the primary source for this specific VLA trajectory analysis. They may be used for auxiliary text embedding validation if the primary dataset lacks sufficient text diversity, but the core trajectory analysis relies on the Tencent source.

**Data Availability Check**:
The primary dataset is hosted on Hugging Face and is directly downloadable via the `datasets` library. It does not require credentials or a Data Use Agreement (DUA), making it feasible for the GitHub Actions free-tier runner. The plan explicitly avoids access-gated datasets (e.g., ADNI, HCP) which would be fatal to the CI pipeline.

### 2. Kinematic Feature Extraction & Clustering

To reduce the complexity of the VLA prior, action sequences are decomposed into kinematic features. **Crucially, to address the limitations of K-means on time-series data (manifold structure), the plan does NOT use raw time-series points.** Instead, it extracts **statistical summaries** of the trajectories:
- **Velocity Statistics**: Mean, Max, and Variance of joint velocities.
- **Acceleration Statistics**: Mean, Max, and Variance of joint accelerations.
- **Joint Angle Statistics**: Mean and Range of joint angles.

These static feature vectors are normalized and used to cluster trajectories via **K-means** (as mandated by FR-002).
- **Algorithm**: K-means (scikit-learn).
- **Adaptive Clustering (FR-002a)**: The system calculates the **Silhouette Score**. If the score is < 0.25, the target cluster count ($k$) is reduced iteratively. If $k=1$ yields a low score, the system proceeds with a single global model and logs a "degenerate clustering" warning. This ensures the clustering is statistically meaningful before model fitting.
- **Rationale**: Using statistical summaries converts the time-series problem into a Euclidean space problem where K-means is valid, while still capturing the "behavioral mode" (e.g., fast vs. slow) of the trajectory.

**Manifold Robustness Mitigation**:
Robot trajectories often form complex, non-convex manifolds. To address the risk that K-means assumes spherical clusters:
- **Diagnostic**: The pipeline calculates the **Calinski-Harabasz Index** alongside the Silhouette Score.
- **Fallback**: If K-means diagnostics indicate poor fit (e.g., high intra-cluster variance despite low silhouette), the pipeline switches to **Hierarchical Agglomerative Clustering (HAC)** with Ward linkage. HAC is computationally feasible on CPU for the sample sizes expected and is better suited for non-convex structures.
- **Validation**: The chosen clustering method must yield a valid cluster count (k > 1) or a single global model with a "degenerate" warning.

### 3. Non-Neural Model Fitting & Construct Validity

For each valid cluster, a lightweight model is trained to map **frozen BERT text embeddings** to the cluster's action distribution.
- **Text Encoder**: `bert-base-uncased` (frozen, CPU-only).
- **Predictors**: Frozen BERT embeddings of the text instruction.
- **Targets**: The statistical kinematic features of the cluster's trajectories (not raw actions).
- **Models**:
 - **Decision Tree Regressor**: For deterministic trajectory generation.
 - **Gaussian Mixture Model (GMM)**: For probabilistic sampling (if variance is significant).
- **Construct Validity Gate**: Before full training, the plan computes the **Mutual Information** or **R²** between BERT embeddings and the kinematic features.
 - **Threshold**: If R² < 0.1 (or MI < threshold), the hypothesis that "text determines kinematics" is considered to have failed.
 - **Action**: If the threshold is not met, the pipeline **HALTS** model training, logs a "Hypothesis Failure" report, and proceeds directly to the negative result phase. This prevents wasted compute on a known-to-fail mapping.
- **Validation**: Held-out $R^2$ score is measured, but the primary validation metric is **Simulation Success Rate** (SC-002), acknowledging that a high $R^2$ on kinematic features does not guarantee task success.

### 4. Simulation & Statistical Evaluation

Generated trajectories are executed in **PyBullet** (CPU mode).
- **Tasks**: Grasp, Navigate, Place.
- **Metrics**: Success rate, collision count, execution time.
- **Baselines**:
 - **Random Baseline**: Uniform sampling within joint limits.
 - **VLA Proxy**: A **static reference dataset** of trajectories generated by the original Qwen-VLA model (or a pre-computed subset from the HuggingFace dataset where the model output is stored). The plan **does not** require live GPU inference. The "paired" t-test compares the non-neural model's output against this **pre-computed** VLA proxy for the **same text prompts**. This ensures reproducibility on a CPU-only runner.
- **Prompt Alignment Protocol**: To ensure the "paired" assumption is valid:
 1. The VLA Proxy artifact contains a set of `(prompt_id, prompt_text, trajectory)` pairs.
 2. The non-neural model is evaluated **only** on the `prompt_id` list extracted from this proxy.
 3. The simulation runs the non-neural model on these exact prompts.
 4. The comparison is strictly "paired" because both models are evaluated on the identical set of text instructions.
- **Statistical Test**: Paired t-tests comparing the non-neural model against the random baseline and VLA proxy on the same test prompts.
- **Significance**: $\alpha = 0.05$.
- **Fidelity Definition**: "Trajectory Fidelity" (SC-001) is defined as the percentage of tasks where the non-neural model achieves a **success rate** and **collision count** comparable to the VLA proxy. Kinematic error is a secondary check to avoid circular validation. *Note: If the spec requires kinematic error as the primary metric, the research plan will report both but prioritize the simulation outcome as the ground truth for "fidelity" to avoid tautology.*

### 5. Compute Feasibility & CPU-First Strategy

- **CPU-First**: All models (BERT, Decision Trees, GMM) are lightweight enough to run on the GitHub Actions runner.
- **No GPU Offload**: The plan **explicitly rejects** any GPU offloading logic. Task T043 (detecting CUDA errors) has been removed as it contradicted Constitution Principle VI.
- **Streaming**: Large datasets are processed via `streaming=True` to avoid OOM errors.
- **Sample Size**: If the full dataset exceeds memory, a well-defined random sample (fixed seed) is used, with power limitations acknowledged.

## Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **CPU-Only Execution** | Mandated by Constitution Principle VI and the project's goal of "Non-Neural Approximation." GPU offloading would defeat the purpose of testing lightweight, non-neural logic. |
| **Adaptive Clustering (FR-002a)** | Ensures that the "clusters" are not artifacts of noise. If data is uniform, a single model is preferred over forced, meaningless clusters. |
| **Frozen BERT** | Avoids the computational cost of fine-tuning a language model, keeping the pipeline within the 6-hour CI budget. |
| **PyBullet Simulation** | Provides a deterministic, reproducible environment for evaluating physical feasibility without requiring physical hardware. |
| **Paired T-Tests** | Required by SC-004 to establish statistical significance of the non-neural model's performance relative to baselines. |
| **Statistical Feature Engineering** | Converts time-series data to static features to satisfy K-means assumptions while retaining behavioral information. |
| **VLA Proxy as Static Dataset** | Avoids the need for live GPU inference, enabling a reproducible "paired" comparison on CPU. |
| **Manifold Robustness Mitigation** | Addresses the risk of K-means failing on non-convex trajectory manifolds by introducing HAC as a fallback. |
| **Construct Validity Gate** | Prevents wasted compute on a known-to-fail hypothesis by halting if text embeddings do not predict kinematics. |

## Risk Assessment

- **Risk**: Dataset lacks sufficient variance for clustering.
 - **Mitigation**: FR-002a reduces $k$ to 1 and logs a warning. The single model is still evaluated.
- **Risk**: BERT embeddings do not predict actions well ($R^2 < 0.1$).
 - **Mitigation**: This is a valid negative result. The plan halts training, logs "Hypothesis Failure," and reports the fidelity gap.
- **Risk**: Simulation crashes due to invalid trajectories.
 - **Mitigation**: PyBullet wrapper catches exceptions, records "failure," and continues (US-03 Edge Case).
