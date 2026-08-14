# Data Model: The Influence of Simulated Social Status on Risk-Taking Behavior

## I. Entities & Attributes

*   **Participant**:
    *   `participant_id` (integer, unique identifier)
    *   `status_level` (categorical: "high", "low") - Observed status of the agent.
    *   `observed_behavior` (categorical: "risky", "conservative") - Behavior exhibited by the observed agent.
    *   `risk_taking_score` (numeric) - Participant's score on a validated risk-taking measure.

## II. Relationships

The data will be structured as either between-subjects or within-subjects, depending on the chosen experimental design. Within-subjects designs will require an additional `session_id` to identify repeated measures from the same participant.

## III. Data Types & Constraints

*   `participant_id`: Integer > 0
*   `status_level`: Controlled vocabulary: "high", "low".
*   `observed_behavior`: Controlled vocabulary: "risky", "conservative".
*   `risk_taking_score`: Numeric (continuous or discrete, depending on the chosen instrument).

## IV. Data Quality Considerations

*   Missing values will be imputed using appropriate methods (e.g., mean imputation, multiple imputation) or handled through listwise deletion if the missing data rate is low.
*   Outliers will be identified and addressed using sensitivity analysis techniques (see `research.md`).
*   Data validation checks will ensure that all categorical variables adhere to the defined controlled vocabularies.
