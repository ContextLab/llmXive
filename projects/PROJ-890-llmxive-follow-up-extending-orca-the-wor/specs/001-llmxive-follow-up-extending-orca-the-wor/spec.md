# Feature Specification: llmXive follow-up: extending "Orca: The World is in Your Mind"

**Feature Branch**: `001-llmxive-orca-counterfactual`  
**Created**: 2026-07-10  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Orca: The World is in Your Mind'"

## User Scenarios & Testing

### User Story 1 - Data Curation and Latent Extraction Pipeline (Priority: P1)

**User Journey**: A researcher needs to prepare the dataset and extract the necessary latent vectors from the frozen Orca model to enable the counterfactual analysis. This is the foundational step; without valid data and latent representations, no downstream modeling can occur.

**Why this priority**: This story delivers the core data assets (the curated video clips and their corresponding frozen latent vectors) required for all subsequent analysis. It is the bottleneck for the entire research project.

**Independent Test**: The pipeline can be tested by verifying that the script successfully downloads the subset of the Orca dataset, filters for physical interaction clips, and outputs a CSV containing the video IDs, the manually annotated counterfactual prompts, and the corresponding frozen latent vectors (shape verified) without requiring GPU resources.

**Acceptance Scenarios**:

1. **Given** a list of video IDs from the Orca dataset, **When** the extraction script runs on a CPU-only environment, **Then** it outputs a JSON/CSV file containing a set of valid latent vectors and their associated counterfactual prompts, and the script completes within 60 minutes.
2. **Given** a video clip that does not depict a physical interaction (e.g., a static landscape), **When** the filtering logic is applied, **Then** the clip is excluded from the final dataset, and the total count of valid clips is reduced by the number of excluded clips.

---

### User Story 2 - Counterfactual Readout Model Training and Baseline Comparison (Priority: P2)

**User Journey**: A researcher trains two distinct models: one using the extracted Orca latents (with symbolic counterfactual edits) and one using raw pixel data. They then compare the performance to determine if the latent space encodes causal priors better than raw correlation.

**Why this priority**: This story delivers the primary scientific result (the comparison of accuracies) which directly answers the research question. It validates the hypothesis that "conscious" scaffolding provides a causal advantage.

**Independent Test**: The story is tested by running the training script which produces two accuracy metrics (Latent Model vs. Baseline Pixel Model) and a paired t-test p-value, all generated on a CPU without GPU acceleration.

**Acceptance Scenarios**:

1. **Given** the dataset of curated video clips with latent vectors and raw frames, **When** the `DecisionTreeClassifier` is trained on the latent vectors with counterfactual edits, **Then** the model achieves a classification accuracy score, and the training process completes within 30 minutes on 2 CPU cores with memory usage < 7GB.
2. **Given** the same dataset, **When** an identical `DecisionTreeClassifier` is trained on raw downsampled frames to predict the *simulated* counterfactual outcome, **Then** the baseline accuracy is generated, and the system outputs a statistical comparison (p-value) between the two models.

---

### User Story 3 - Method Independence and Ablation Verification (Priority: P3)

**User Journey**: A researcher verifies that the observed causal advantage is not an artifact of the specific decision tree used or the presence of "unconscious" latent signals. They re-run the analysis with a linear probe and without the linguistic scaffolding.

**Why this priority**: This story provides robustness checks required to rule out alternative explanations (e.g., that the result is just a quirk of the decision tree or that the "unconscious" layer does the work). It strengthens the validity of the findings.

**Independent Test**: The story is tested by executing the ablation scripts which regenerate results using a linear probe and a modified latent input (excluding linguistic tokens), confirming if the performance gap persists.

**Acceptance Scenarios**:

1. **Given** the original latent vectors, **When** the readout model is changed from a Decision Tree to a Linear Probe, **Then** the performance gap between the Latent Model and the Pixel Baseline remains statistically significant (p < 0.05), confirming method independence.
2. **Given** the "unconscious" latent vectors (excluding linguistic scaffolding), **When** the readout model is trained on these, **Then** the accuracy drops significantly compared to the "conscious" latent model, isolating the contribution of the linguistic scaffolding.

---

### Edge Cases

- **What happens when** the Orca latent extraction script encounters a video file that is corrupted or missing from the HuggingFace repository? **System Behavior**: The script logs the specific video ID, skips the file, and continues processing the remaining valid files, ensuring the pipeline does not crash but flags the data loss for manual review.
- **How does the system handle** a scenario where the counterfactual prompt (e.g., "remove gravity") is semantically ambiguous or does not map cleanly to a vector arithmetic operation? **System Behavior**: The system generates a modified latent vector $z_{cf}$ using a zero-vector mask for the specific concept token, records the ambiguity in a `failed_scenarios.log`, and excludes the scenario from the final statistical test to prevent noise. The $z_{cf}$ is generated but flagged as invalid for training.
- **What happens when** the memory usage approaches the 7 GB limit during batch processing of video frames? **System Behavior**: The script automatically reduces the batch size by halving it and retries the extraction, repeating this process until memory usage is < 7GB or the batch size reaches 1.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract frozen latent vectors from the Orca model for up to 500 curated video clips depicting physical interactions, processing them in batches. If the source pool contains an insufficient number of valid clips, the system MUST fail with an explicit error. If valid clips are fewer than 500 due to corruption, the system MUST process the available valid clips (See US-1).
- **FR-002**: System MUST implement a counterfactual injection mechanism that applies vector arithmetic or masking to the latent vectors based on manual prompts, generating a modified latent representation $z_{cf}$ for each input clip, even if the prompt is later flagged as ambiguous (See US-2).
- **FR-003**: System MUST train a lightweight `DecisionTreeClassifier` on the modified latents to predict binary physical outcomes (e.g., "falls" vs. "floats") within 30 minutes on a 2-core CPU, excluding clips flagged as ambiguous (See US-2).
- **FR-004**: System MUST train an identical `DecisionTreeClassifier` on raw, downsampled video frames to establish a pixel-based baseline for performance comparison, where the target label is the outcome simulated by an independent physics engine (See US-2).
- **FR-005**: System MUST perform a paired t-test comparing the accuracy of the latent-based model against the pixel-based baseline and output a p-value to determine statistical significance (See US-2).
- **FR-006**: System MUST repeat the readout training using a linear probe to verify that the causal signal persists regardless of the specific querying mechanism (See US-3).
- **FR-007**: System MUST repeat the readout training using only "unconscious" latent vectors to isolate the contribution of the linguistic scaffolding (See US-3).
- **FR-008**: System MUST log all data processing steps, including skipped files and ambiguous prompts, to a machine-readable audit log (See Edge Cases).
- **FR-009**: System MUST verify the ground truth labels for counterfactual outcomes by simulating the physical scenario in an independent physics engine (e.g., MuJoCo or PyBullet) and confirming the simulated outcome matches the logical expectation before training the readout models (See US-2).
- **FR-010**: System MUST validate the vector arithmetic operations by comparing the predicted outcome from $z_{cf}$ against the physics engine simulation for a subset of clips to ensure the arithmetic actually corresponds to the physical concept (See US-2).

### Key Entities

- **PhysicalScenario**: Represents a single curated video clip with an associated manual annotation of the physical event and a counterfactual prompt.
- **LatentVector**: Represents the frozen Orca world latent representation for a specific video frame, including both "conscious" (linguistic) and "unconscious" components.
- **CounterfactualEdit**: Represents the transformation applied to a `LatentVector` to simulate a change in physical laws (e.g., zeroing out the gravity vector).
- **ZeroVectorMask**: A specific operation that sets the vector components corresponding to a concept token to zero, used to generate $z_{cf}$ for ambiguous prompts.
- **ReadoutModel**: Represents the trained classifier (Decision Tree or Linear Probe) used to map latents to physical outcomes.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The accuracy of the latent-based counterfactual model is measured against the accuracy of the pixel-based baseline model to determine the causal advantage (See FR-005, US-2).
- **SC-002**: The statistical significance of the performance difference between the latent and pixel models is measured using a paired t-test with a significance threshold of $p < 0.05$ (See FR-005, US-2).
- **SC-003**: The robustness of the causal signal is measured by comparing the performance gap when using a Decision Tree versus a Linear Probe as the readout mechanism (See FR-006, US-3).
- **SC-004**: The contribution of the linguistic scaffolding is measured by comparing the accuracy of the model trained on full latents versus the model trained on "unconscious" latents only (See FR-007, US-3).
- **SC-005**: The computational feasibility is measured by ensuring the total end-to-end pipeline (extraction, training, evaluation) completes within 6 hours on a 2 vCPU, 7GB RAM CPU-only runner (GitHub Actions ubuntu-latest equivalent) (See FR-001, US-1).
- **SC-006**: The methodological validity is measured by ensuring no GPU-dependent libraries (e.g., CUDA, bitsandbytes) are imported or invoked during any stage of the analysis (See FR-001, US-1).
- **SC-007**: The ground truth validity is measured by ensuring [deferred] of counterfactual labels are verified against an independent physics engine simulation (See FR-009).
- **SC-008**: The vector arithmetic validity is measured by ensuring the vector injection method correctly predicts the physics engine outcome for at least 90% of the validation clips (See FR-010).

## Assumptions

- The public Orca video dataset and associated "conscious" event annotations are available via the HuggingFace repository or arXiv supplementary materials in a format accessible without proprietary licensing.
- The curated video clips can be manually annotated with counterfactual prompts by the research team within a reasonable timeframe, and these annotations are treated as the initial hypothesis for the logical outcomes.
- **Critical**: The "conscious" linguistic scaffolding in the Orca model is represented as a distinct, accessible vector component that can be mathematically manipulated (e.g., via vector arithmetic) to simulate counterfactual edits.
- The frozen Orca model weights are compatible with a CPU-only inference environment (e.g., standard PyTorch or ONNX runtime) without requiring 8-bit quantization or CUDA acceleration.
- The physical outcomes (e.g., "object falls") for the counterfactual scenarios MUST be verified by an independent physics engine simulation; logical determination alone is insufficient and creates a tautological loop.
- The dataset size (≥450 valid clips) is sufficient to achieve statistical power for a paired t-test.
- The vector arithmetic operations used for counterfactual injection (e.g., $z_{cf} = z - v_{gravity}$) are a valid approximation of "removing" a physical law in the latent space, pending validation by FR-010.