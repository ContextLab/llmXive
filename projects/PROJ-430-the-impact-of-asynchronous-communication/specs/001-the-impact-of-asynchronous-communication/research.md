# Research: The Impact of Asynchronous Communication Delays on Team Cohesion

## Problem Statement

How does response-time variability in asynchronous communication channels influence perceived team cohesion and trust in distributed software teams?

## Hypotheses

- **H1**: Higher variance in response times (asynchronous delay) is negatively associated with team cohesion scores (composite proxy: sentiment stability + structural reciprocity).
- **H2**: This association remains significant after controlling for team size and project age, and is moderated by team size (interaction term).
- **H3**: The association is robust across different primary programming languages and project size tiers.

## Dataset Strategy

The study relies on **GitHub Public Repository Metadata**. The "Verified datasets" block provided in the prompt contains VADER training data, but the *primary* dataset for this study (GitHub events) is not a pre-packaged static dataset but must be fetched dynamically via the GitHub API. The VADER models will be loaded from the `nltk` library (standard implementation) or the verified HuggingFace URLs if a specific pre-trained model file is required, though `nltk`'s built-in VADER is standard for this task.

### Verified Sources

| Dataset | Description | Source / Loader | Status |
| :--- | :--- | :--- | :--- |
| **GitHub Events (Issues, PRs, Comments)** | Raw event logs for open-source projects. Contains timestamps, author IDs, and text content. | **GitHub REST API** (`requests` library). *Note: No static URL exists; data is fetched dynamically per spec.* | **Verified via API** |
| **VADER Sentiment Lexicon** | Pre-trained sentiment lexicon for social media text. | **NLTK** (`nltk.download('vader_lexicon')`) or **HuggingFace** (if specific parquet needed for custom training, but standard NLTK suffices for inference). | **Verified** |

*Note: The HuggingFace URLs listed in the "Verified datasets" block (`bartoszmaj/vader_sentiment_full`, etc.) are training datasets for VADER. Since VADER is a rule-based model, we do not need to train on these. We will use the standard `nltk` VADER implementation. If the spec required training a custom model, we would cite these URLs. For this study, the "dataset" is the GitHub event stream.*

## Methodology

### Phase 1: Data Ingestion & Metric Derivation (FR-001, FR-002)
1.  **Candidate Selection**: Fetch repositories sorted by stars descending. Filter for those with `[deferred: min_events]` events.
2.  **Event Extraction**: Query GitHub API for issues, PRs, and comments.
    *   *Filter*: Exclude events from authors with names ending in `[bot]` or known GitHub App IDs.
    *   *Language Filter*: Use `langdetect` (confidence **≥ 0.95**) to retain only English comments.
3.  **Temporal & Structural Metrics**:
    *   Group events by `Contributor Pair` (Author A -> Author B).
    *   Calculate `mean_delay` and `response_time_variance` for each pair.
    *   **Aggregation Strategy**: Compute project-level `response_time_variance` as the **interaction-weighted mean** of all pair variances. Pairs with more interactions receive higher weight, addressing the statistical instability of the median approach (methodology-17d46215).
    *   **Structural Metrics**: Calculate `reciprocity_ratio` (mutual responses / total responses) and `network_density` for each project to be used in the composite cohesion score.

### Phase 2: Cohesion Proxy Calculation (FR-003, FR-009, FR-011)
1.  **Sentiment Analysis**: Apply VADER to all English comments.
2.  **Composite Score Construction**:
    *   Calculate `sentiment_stability`: Standard deviation of compound scores (lower is more stable).
    *   Calculate `reciprocity_score`: Normalized reciprocity ratio.
    *   **Cohesion Proxy**: A weighted composite: `0.4 * (1 - sentiment_stability) + 0.3 * reciprocity_score + 0.3 * network_density`. This ensures the metric captures relational dynamics, not just additive sentiment (methodology-b2dd1644).
3.  **Validation (FR-009)**:
    *   Sample 50 comments per project.
    *   Perform manual coding for **'relational cohesion indicators'** (e.g., 'we', 'together', 'collaborative tone', 'acknowledgment of effort', 'conflict resolution'). **Crucially, we do NOT validate against simple positive words like 'thanks' or 'great job' to avoid tautological validation (scientific_soundness-dad9ce93).**
    *   Compute Spearman correlation between the composite VADER/structural score and the manual relational score. Target: ρ ≥ 0.5 (SC-005).

### Phase 3: Statistical Analysis (FR-004, FR-005, FR-007, FR-008)
1.  **Primary Test**: Spearman rank correlation between `response_time_variance` and `cohesion_proxy_score`.
2.  **Controlled Regression**: Linear model: `Cohesion ~ Delay_Variance + Team_Size + Project_Age + (Delay_Variance * Team_Size)`.
    *   **Interaction Term**: Added to test if the effect of delay differs by team size (methodology-dc346983).
    *   *Collinearity Check*: Calculate VIF for predictors. If VIF > 5, halt and warn (FR-008).
3.  **Secondary Tests**: Stratified correlations by language (Python, JS, Go) and team size (<10, ≥10).
    *   *Correction*: Apply Benjamini-Hochberg procedure to control False Discovery Rate (FR-007).
4.  **Sensitivity Analysis**: Repeat primary correlation using a 'pooled variance' metric and excluding pairs with < 3 interactions to ensure robustness (scientific_soundness-01609861).

### Phase 4: Visualization (FR-006)
1.  Generate scatter plot: X=`response_time_variance`, Y=`cohesion_proxy_score`.
2.  Overlay linear regression line with 95% confidence interval ribbon.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Addressed via Benjamini-Hochberg for secondary tests (FR-007).
- **Power Justification**: Sample size `[deferred: sample_size]` is treated as a community-standard default. Sensitivity analysis will sweep `[deferred: min_events]` thresholds (50, 100, 200) to verify stability.
- **Causal Framing**: All claims are **associational**. No causal inference is made regarding delay *causing* trust erosion, as the data is observational.
- **Measurement Validity**: The composite proxy is validated against manual coding of *relational* behaviors (not just positive words), ensuring the construct validity (methodology-8310e1b1, scientific_soundness-b13c5218).
- **Collinearity**: VIF check ensures predictors are not definitionally redundant. If team size and delay variance are highly collinear, the model halts.
- **Dataset Fit**: The GitHub API provides the necessary variables (timestamps, text, author IDs). No missing variable mismatch is expected for the defined scope.

## Compute Feasibility (Free Tier CI)

- **Memory**: Data is processed in chunks. Large repositories (>100k events) are skipped or sampled to stay < 7 GB RAM.
- **CPU**: VADER, `networkx` structural metrics, and statistical tests are CPU-tractable. No GPU required.
- **Runtime**: Pipeline designed to complete in < 6 hours. Rate limiting logic ensures API compliance.
- **Disk**: Intermediate files are stored in `data/` and cleaned up or compressed. Total disk usage < 14 GB.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use NLTK VADER** | Standard, lightweight, no training required. Fits CPU constraints. |
| **Interaction-Weighted Mean Aggregation** | Robust to outliers and biased by low-count pairs; aligns with FR-010 and addresses methodology-17d46215. |
| **Dynamic API Fetch** | No static dataset exists for "all open source projects". API is the only source. |
| **English-Only Filter (≥ 0.95)** | VADER is English-specific. `langdetect` ensures validity. |
| **Composite Cohesion Proxy** | Combines sentiment stability with structural metrics (reciprocity, density) to better capture the latent construct of cohesion (methodology-b2dd1644). |
| **Relational Validation Target** | Manual coding targets 'relational indicators' (e.g., 'we', 'together') rather than positive words to avoid tautology (scientific_soundness-b13c5218). |
| **Interaction Term in Regression** | Accounts for the confounding effect of team size on delay variance (methodology-dc346983). |