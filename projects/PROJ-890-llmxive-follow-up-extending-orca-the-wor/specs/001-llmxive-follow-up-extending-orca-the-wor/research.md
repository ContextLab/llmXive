# Research: llmXive follow-up: extending "Orca: The World is in Your Mind"

## Research Question
Does the "Orca" multimodal model's latent space encode causal priors regarding physical interactions (e.g., gravity, collision) better than raw pixel data, specifically when "conscious" linguistic scaffolding is manipulated via counterfactual vector arithmetic?

## Dataset Strategy

| Dataset Name | Source URL | Usage | Notes |
|--------------|------------|-------|-------|
| Orca Video Dataset (Physical Interaction Subset) | [Verified Source: See #Verified datasets block] | Primary data source for video IDs and metadata. | **Verified Source**: The plan relies exclusively on the verified dataset URL provided in the upstream resolver. If the verified source is text-only or lacks video frames, the pipeline will fail with a clear error. No assumptions about uncited repositories are made. |
| Physics Engine Ground Truth | N/A (Local Simulation) | Validation of counterfactual outcomes. | No external dataset URL required. The ground truth is generated dynamically using `mujoco` or `pybullet` on the local runner for a subset of clips (N=50). |
| Manual Annotations | `data/metadata/manual_annotations.csv` (Local) | Counterfactual prompts (e.g., "remove gravity"). | Source: Researcher-provided CSV derived from the curated video list. This is a local artifact, not an external citation. |

**Dataset Variable Fit Verification**:
- **Required Variables**: Video ID, Frame Data (or path), Counterfactual Prompt (manual annotation), Physical Outcome Label (simulated).
- **Verified Fit**: The verified dataset provides the core data structure (video IDs, frames). The "physical interaction" filter is applied based on metadata tags or the researcher-provided list of IDs. The "manual annotation" for counterfactual prompts is stored in the local CSV.
- **Gap Handling**: If the verified dataset lacks video frames (only IDs), the script will attempt to fetch frames from the *verified* source only. If the verified source does not provide frames, the pipeline will halt with a "Data Incomplete" error, rather than assuming an uncited repository.

## Methodology & Statistical Rigor

### 1. Data Curation & Latent Extraction (FR-001)
- **Method**: Download curated video IDs. Load frozen Orca model (CPU-only). Extract latent vectors for frames depicting physical interactions.
- **Handling Missing Data**: Skip corrupted files, log to `failed_scenarios.log`, continue processing.
- **Memory Safety**: Implement adaptive batch sizing (start with batch=4, halve on OOM) to stay within 7GB RAM.

### 2. Concept Localization (New Step)
- **Method**: Before performing vector arithmetic, use a **linear probing** approach on a held-out set of labeled concepts to identify the specific dimensions in the latent space corresponding to "gravity", "friction", etc.
- **Rationale**: This addresses the construct validity requirement. We do not assume $v_{gravity}$ is known; we empirically identify it.
- **Output**: A mapping of concept names to vector indices or weight vectors ($v_{gravity}$).

### 3. Counterfactual Injection (FR-002)
- **Method**: Apply vector arithmetic ($z_{cf} = z - v_{gravity}$) or masking (zero-out concept tokens) based on manual prompts and the localized concept vectors.
- **Ambiguity Handling**: If a prompt is semantically ambiguous, apply a zero-mask, flag the sample as "ambiguous" in metadata, and exclude it from *training* but include it in the *audit log*.
- **Scope**: This step runs on the full dataset (N=450) for descriptive purposes, generating $z_{cf}$ for all valid clips.

### 4. Physics Simulation & Validation (FR-009, FR-010)
- **Method**: For a random subset of 50 clips, simulate the physical scenario in `mujoco`/`pybullet` with the counterfactual condition (e.g., gravity=0).
- **Validation Metric**: **Classification Accuracy**. The metric is defined as the percentage of cases where the model trained on $z_{cf}$ correctly predicts the physics engine outcome (e.g., "floats") compared to the actual simulation result.
- **Threshold**: [deferred]. This value will be determined during a pilot run on the N=50 subset and documented here.
- **Gate Logic**: If accuracy < [deferred], the pipeline sets `causal_gate_status = "blocked"`. The pipeline **does not halt**; it proceeds with descriptive analysis (N=450) but blocks the causal comparison (FR-005) for the N=50 subset.

### 5. Model Training & Comparison (FR-003, FR-004, FR-005)
- **Models**: `DecisionTreeClassifier` (Latent vs. Pixel) and `LinearProbe` (Robustness Check).
- **Inputs & Labels**:
  - **Descriptive Baseline (N=450)**: 
    - *Latent Model*: Trained on original latents ($z$) to predict *original* physical outcomes (from video labels).
    - *Pixel Model*: Trained on raw frames to predict *original* physical outcomes (from video labels).
    - *Purpose*: Establish a correlation baseline for the full dataset.
  - **Causal Consistency Test (N=50)**:
    - *Latent Model*: Trained on edited latents ($z_{cf}$) to predict *simulated* counterfactual outcomes (from physics engine).
    - *Pixel Model*: Trained on raw frames to predict *simulated* counterfactual outcomes (from physics engine).
    - *Purpose*: Test if the latent space aligns with the physics engine's logic.
    - *Constraint*: This branch is **blocked** if `causal_gate_status` is "blocked".
- **Statistical Test**: Paired t-test comparing the accuracy of the Latent Model vs. Pixel Model **within the N=50 subset** (if gate passed).
- **Multiple Comparisons**: Since only one primary comparison (Latent vs. Pixel on the N=50 subset) is made, standard t-test is sufficient. If multiple physical laws (gravity, friction) are tested, Bonferroni correction will be applied.
- **Power Analysis**: A sample size of N=50 is the target for the causal test. If N < 30 (after filtering), the plan will explicitly state the power limitation and interpret results as exploratory. The N=450 descriptive analysis provides robustness for the correlation baseline.

### 6. Robustness Checks (FR-006, FR-007)
- **Method Independence**: Re-run with `LinearProbe`. If the gap persists, the signal is robust to the readout mechanism.
- **Linguistic Scaffolding**: Train on "unconscious" latents (excluding linguistic tokens). If accuracy drops, the scaffolding is confirmed as the causal driver.

## Limitations & Interpretation

- **Tautology Risk (Consistency Test)**: The causal comparison (N=50) tests the latent space's ability to predict the *simulation's logic*, not independent reality. The plan explicitly frames this as a "Consistency Test" (does the latent space align with the physics engine?) rather than a "Reality Test". The N=450 correlation baseline is presented as the primary evidence for "causal priors" in the real world, assuming the consistency test passes.
- **Vector Arithmetic Validity**: The assumption that vector subtraction corresponds to "removing gravity" is a **hypothesis to be tested**, not a premise. The plan includes a validation step (FR-010) to verify this. If the validation fails (accuracy < [deferred]), the causal claim is flagged as unverified, but the descriptive analysis continues.
- **Dataset Scope**: The plan relies on the verified HuggingFace dataset for the primary data. If the "physical interaction" subset cannot be automatically filtered, the plan assumes a manual curation step (researcher-provided list of IDs) is available.
- **Power Limitations**: If the valid subset for the causal test drops below N=30, the study will report the power limitation and interpret results as exploratory, not definitive.

## Decision Rationale & Constraints

- **CPU-Only Constraint**: The spec explicitly requires execution on free GitHub Actions runners (multi-core vCPU, sufficient RAM). Therefore, no GPU-dependent libraries (CUDA, bitsandbytes) are used. The Orca model is loaded in default precision or reduced precision if memory permits, but strictly on CPU.
- **Concept Localization**: The plan includes a probing step to empirically identify concept vectors, addressing the construct validity concern.
- **Dataset Scope**: The plan relies on the verified HuggingFace dataset for the primary data. If the "physical interaction" subset cannot be automatically filtered, the plan assumes a manual curation step (researcher-provided list of IDs) is available.
