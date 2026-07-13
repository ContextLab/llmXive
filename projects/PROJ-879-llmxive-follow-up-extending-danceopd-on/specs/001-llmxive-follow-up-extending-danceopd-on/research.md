# Research: llmXive follow-up: extending "DanceOPD: On-Policy Generative Field Distillation"

## Research Questions

1. **Compressibility**: Can the dynamic, state-dependent routing logic of the DanceOPD teacher model be approximated by static Decision Trees with high fidelity (Routing Consistency)?
2. **Complexity Threshold**: Is there a sharp threshold in `max_depth` where routing accuracy saturates, or does it degrade linearly?
3. **Fidelity Impact**: Does a drop in routing consistency (due to shallow trees) result in a statistically significant degradation in image quality (FID, CLIP Score)?

## Dataset Strategy

### Source Verification
The project utilizes the following verified datasets for prompt sampling. No other datasets are used.

| Dataset | Source URL | Usage |
|:--- |:--- |:--- |
| **ImageNet-1K (Resized)** | ` | Primary source for prompt embeddings and visual content for teacher inference. |
| **LAION-400M** | ` | Secondary source for prompt diversity to ensure full range of routing triggers. |
| **TeacherRoutingDataset** | *No verified source* | **Generated Artifact**. This dataset is created by the project code by running the pre-trained DanceOPD teacher on the above sources. It is *not* downloaded.

### Data Processing Pipeline
1. **Sampling**: Randomly sample a diverse set of images from the verified ImageNet and LAION sources to ensure diversity.
2. **Feature Extraction**: Use the pre-trained DanceOPD teacher (loaded into CPU memory) to process each sample.
 * *Constraint*: The teacher model weights must be verified via `check_weights.py` before loading.
 * *Memory Handling*: Process in small batches to prevent RAM exhaustion on the constrained runner environment. Stream results to disk immediately.
3. **Label Capture**: For each step in the teacher's generation process, record the `routing_label` (expert ID selected) and the `velocity_vector`.
4. **Dataset Construction**: Save as `TeacherRoutingDataset.parquet` with columns: `prompt_embedding`, `noise_level`, `routing_label`, `velocity_vector`.
5. **Split**: [deferred] Train, [deferred] Test. Ensure stratified split by `routing_label` to maintain class balance.

### Dataset-Variable Fit Verification
* **Requirement**: The dataset must contain `prompt_embedding`, `noise_level`, `routing_label`, and `velocity_vector`.
* **Verification**: The `generate_teacher.py` script explicitly extracts these four fields. If the teacher model architecture changes or fails to output a `velocity_vector` for a specific step, the sample is logged and excluded (Edge Case: Undefined Expert Path).
* **Risk**: If the teacher model requires a specific noise schedule not present in the raw dataset, the `noise_level` will be synthesized based on the diffusion step index, which is standard in DanceOPD. This is a valid derivation, not a missing variable.

## Methodology

### Phase 1: Teacher Data Generation (FR-001)
* **Method**: Load pre-trained DanceOPD weights. Iterate over sampled prompts.
* **Output**: `data/processed/teacher_routing_dataset.parquet`.
* **Constraint**: Must run on CPU. If the full model is too large for 7 GB RAM, the plan assumes the "Assumption about data/environment" allows for loading a smaller subset of weights or a quantized version that fits, provided it does not require CUDA. If the full model cannot fit, the pipeline aborts with a clear error.

### Phase 2: Static Approximation Training (FR-002, FR-003)
* **Method**: Train `scikit-learn.DecisionTreeClassifier` models.
* **Hyperparameters**: `max_depth` ranging from 2 to 20 (step 2).
* **Metric**: Routing Consistency (Accuracy) on the held-out test set.
* **Validation**: Train/Test split. Report both to detect overfitting (Edge Case: Overfitting).

### Phase 3: CPU-Only Fidelity Evaluation (FR-004, FR-005)
* **Pre-flight**: Verify Euler integrator stability for all expert fields in the dataset with a small pilot.
* **Method**:
 1. **Step 3a: Generate Teacher Baseline**: Select a subset of test images. Run the Teacher model with its ground truth routing to generate a set of images. Calculate FID and CLIP scores for this baseline set.
 2. **Step 3b: Generate Tree Approximations**: For the SAME test images, run the trained Decision Tree to predict `routing_label`. **Invoke the specific expert field logic** using the tree-predicted label to generate the `velocity_vector`. Run a simple Euler integrator (identical step size and count as the Teacher) to generate the final image.
 3. **Step 3c: Metric Calculation**: Calculate FID and CLIP Score for the Tree-generated images.
 4. **Step 3d: Total Error Evaluation**: **Do NOT filter** the dataset to "Matched-Routing" cases. Include ALL samples (both matched and mismatched) in the calculation to capture the total system error attributable to the static approximator.
* **Metrics**:
 * **FID**: Calculated using a CPU-compatible implementation (e.g., `torch-fidelity` with CPU mode or a custom implementation using `torchvision` features) on the **distribution** of generated images.
 * **CLIP Score**: Calculated using `clip` library in CPU mode on a per-sample basis.
* **Interpretation of FID Degradation**: The plan acknowledges that FID degradation conflates (1) routing error and (2) inherent differences in expert field outputs. Results will be framed as "Total System Error" rather than pure routing error.
* **Constraint**: The Euler integrator must use fixed step size and step count (e.g., 50 steps, step_size=0.01) **identical for both Teacher and Tree** to ensure the integrator is not a confounding variable.

### Phase 4: Statistical Significance (FR-006, SC-003)
* **Pilot Variance Estimation**: Run a pilot with N=50 samples. Estimate the variance of FID scores (bootstrap on distributions) and CLIP scores.
* **Power Check**: Calculate achieved power for detecting a medium effect size (d=0.5) with the pilot variance.
* **Dynamic N**: If power < 0.8, extend the sample size (up to runtime limit) and re-run evaluation. If time runs out, report the achieved power for the completed N.
* **Statistical Tests**:
 * **FID**: Perform a bootstrap hypothesis test (1,000 resamples) on the **distributions** of generated images (Teacher vs. Tree). Do not use a t-test on per-sample FID scores as they do not exist.
 * **CLIP Score**: Perform a paired t-test on per-sample CLIP scores.
* **Significance Level**: $\alpha = 0.05$.
* **Multiple Comparisons**: Apply Bonferroni correction or FDR control to p-values across multiple `max_depth` configurations.

## Statistical Rigor & Assumptions

* **Multiple Comparisons**: Since multiple `max_depth` configurations are tested, a Bonferroni correction or False Discovery Rate (FDR) control will be applied to the p-values of the fidelity drop tests to control family-wise error.
* **Causal Inference**: This is an observational study of model approximation. Claims are framed as "associational" between tree depth and fidelity. No randomization of the teacher model is performed; the teacher is the fixed baseline.
* **Measurement Validity**: FID and CLIP Score are standard metrics in generative modeling. The implementation uses standard libraries to ensure validity.
* **Collinearity**: `prompt_embedding` and `noise_level` may be correlated in the diffusion process. The Decision Tree handles non-linear interactions, but the plan acknowledges that "independent effects" of features are not claimed; only the aggregate predictive power matters.
* **Power Limitation**: The assumption of sufficient power is replaced by a dynamic calculation. If the 6-hour limit is reached before achieving power >= 0.8, the system will report the results for the completed subset and explicitly state the achieved power.

## Compute Feasibility Rationale

* **CPU-Only**: All operations (Teacher inference, Tree training, Euler integration) are designed for CPU.
 * *Teacher Inference*: The most expensive step. Limited to a constrained sample size and batch processing to fit 7 GB RAM.
 * *Tree Training*: `scikit-learn` is highly optimized for CPU and will run in seconds/minutes.
 * *Euler Integration*: A simple loop over 50 steps per image is trivial for CPU.
* **Memory**: Data is streamed. Models are small (Decision Trees).
* **Time**: A time-based limit serves as the hard constraint. The pipeline includes a `timer.py` module to gracefully stop and save partial results if the limit is exceeded.