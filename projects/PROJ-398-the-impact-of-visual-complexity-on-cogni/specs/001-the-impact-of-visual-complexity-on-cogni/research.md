# Research: Visual Complexity & Cognitive Load

## Domain Background

Visual complexity is a known predictor of cognitive load, but the specific mechanism in remote meeting contexts (where backgrounds are static or video loops) is under-researched. High complexity (clutter, high entropy) may increase extraneous cognitive load, reducing resources for the primary task.

**Key Concepts**:
- **Visual Complexity**: Quantified by Shannon Entropy (information content), Color Variance (dispersion), and Object Count (semantic density).
- **Cognitive Load**: Measured via NASA-TLX (subjective) and Reaction Time (objective).
- **Context**: Remote work meetings, where participants are exposed to varying background complexities.

## Dataset Strategy

The project relies on **Curated Real-World Meeting Backgrounds** (verified, checksummed local archive) and **Primary Data Collection**:

| Dataset / Source | Type | Usage | Verification Status |
| :--- | :--- | :--- | :--- |
| **Real Meeting Backgrounds** | Curated Real-World Video Frames | Stimuli for Pilot & Main Study. A verified subset of a public meeting background video repository, locally stored and checksummed. Extracted frames preserve lighting, depth, and temporal dynamics. | **Verified**: Checksum recorded in `state/`. No synthetic generation. |
| **Human Pilot Ratings** | Primary | n=20 participants rate real images. Used to validate automated metrics (FR-006). | **Verified**: Collected via `code/pilot/app.py`. |
| **Main Study Data** | Primary | n=50-100 real participants complete NASA-TLX/RT tasks on real clips. | **Verified**: Collected via `code/main_study/app.py`. |
| **NASA-TLX Scale** | Instrument | Standardized self-report scale (Hart & Staveland, 1988). | **Verified**: Standard psychometric instrument. |
| **CPU-Compatible Metrics** | Algorithm | Entropy (scikit-image), Variance (numpy), Object Count (YOLOv8n CPU). | **Verified**: Standard algorithms; CPU-optimized implementation. |

### Stratification & Factorial Feasibility
To support the required factorial design (Complexity x Task Difficulty):
1.  **Variance Check**: The curated real-world dataset will be pre-filtered to ensure it contains sufficient images across Low, Medium, and High complexity bins (based on pilot human ratings).
2.  **Stratification**: The main study will only present images from these validated bins. If the real dataset lacks sufficient variance in a specific bin, the study will be paused and the dataset re-curated.
3.  **Interaction Isolation**: By ensuring a balanced distribution of complexity levels across both 1-back and 2-back task conditions, the interaction effect will be isolatable in the LMM.

## Methodological Approach

### Phase 1: Stimulus Curation & Metric Validation (P0/P1)
1.  **Curate Stimuli**: Select a diverse set of unique *real* meeting background images with varying complexity.
2.  **Compute Automated Metrics**: Run `entropy`, `variance`, `yolo_object_count` on each image.
3.  **Human Pilot**: Recruit participants to rate images (1-10).
4.  **Validation**: Compute Pearson correlation between human ratings and automated metrics.
    -   *Success*: r > 0.5.
    -   *Failure*: Flag pipeline; adjust metric weighting.
    -   *Note*: Human ratings serve as the **independent ground truth** for validation only.
    -   **Metric Freeze**: After validation, the mapping/weights for automated metrics are **frozen**. The pilot data is **excluded** from the main analysis to prevent circularity.

### Phase 2: Main Study Data Collection (P2/P4)
1.  **Counterbalancing**: Generate random orderings for stimulus presentation to control for order effects.
2.  **Baseline Task**: Administer simple RT task before experimental trials.
3.  **Experimental Trials**: Show clips (with real backgrounds) -> Administer NASA-TLX -> Administer RT task.
4.  **Full Factorial Within-Subjects Design**: **Every participant** completes **both** 1-back and 2-back tasks across the full range of complexity levels. This ensures the interaction effect (Complexity x Task Difficulty) can be isolated as a within-subject effect in the LMM.
5.  **Data Integrity**: Flag incomplete responses; do not impute.

### Phase 3: Statistical Analysis (P3)
1.  **Preprocessing**: Calculate delta RT (Trial RT - Baseline RT). Normalize NASA-TLX.
2.  **Multicollinearity Check**: Compute VIF for predictors (Entropy, Variance, Count).
    -   If VIF > 5: Apply PCA or combine predictors.
3.  **Linear Mixed-Effects Model (LMM)**:
    -   Fixed Effects: Visual Complexity, Task Difficulty (1-back/2-back), Interaction.
    -   Random Effects: (1 | Participant_ID).
    -   Outcome: NASA-TLX Score, Delta RT.
4.  **Multiple Comparison Correction**: Apply Benjamini-Hochberg to p-values of multiple predictors.
5.  **Sensitivity Analysis**: Sweep alpha (0.01, 0.05, 0.1) and report stability (SD of effect sizes).
6.  **Null Simulation**: Run 1000 iterations using **Residual Permutation**.
    -   **Method**: 
        1. Fit the reduced model (without the predictor of interest) to the real data.
        2. Extract the residuals from this fit.
        3. Permute the residuals randomly.
        4. Reconstruct the response variable using the fitted values from the reduced model + permuted residuals.
        5. Fit the *full* model (with the predictor) to this reconstructed data.
        6. Record the test statistic (e.g., t-value) for the predictor.
    -   **Rationale**: This preserves the random effects structure and the correlation structure of the data under the null hypothesis, providing a valid estimate of the Family-Wise Error Rate (FWER) without the computational infeasibility of re-estimating random effects parameters for every permutation iteration.

## Statistical Rigor & Feasibility

-   **Multiple Comparisons**: Benjamini-Hochberg (FDR) applied to all hypothesis tests (Entropy, Variance, Count).
-   **Power Analysis**: Target n=50-100 participants to detect d=0.5 with power=0.80 (G*Power).
-   **Causal Claims**: Observational within-subjects design. Claims limited to *associational* effects.
-   **Measurement Validity**: NASA-TLX is a validated instrument. Automated metrics validated against human pilot (independent ground truth).
-   **Collinearity**: VIF check mandatory. If Entropy and Variance are highly correlated, report descriptive relationship only, no independent effect claims.
-   **Compute Feasibility**:
 - YOLOvn (CPU) on high-resolution images: approximately several seconds per image. A set of images will be processed, requiring [deferred]. Well within NFR (seconds for 10 images).
    -   LMM on n=100: <1s.
    -   Total Runtime: <1 hour on CPU.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Real-World Stimuli** | Synthetic images lack ecological validity. Real images ensure the study measures "meeting background" complexity as experienced by users. |
| **Participant-Level Permutation (Residual)** | Preserves the random effects structure of the LMM during null simulation, ensuring valid exchangeability assumptions without the computational cost of re-estimating random effects for every iteration. |
| **LMM over ANOVA** | Handles missing data better and accounts for participant variability (random effects) in repeated measures. |
| **No Imputation** | Spec requires flagging missing data (US-2, SC-003) rather than filling it, to avoid bias. |
| **Full Factorial Within-Subjects** | Required to isolate the Complexity x Task Difficulty interaction effect as a within-subject effect. |