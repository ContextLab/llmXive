# Data Model: The Influence of Simulated Social Status on Risk-Taking Behavior

## Entities

### Participant

*   `participant_id`: Unique identifier for each participant (integer).
*   `status_level`:  Social status level of the observed agent (categorical: "high", "low").
*   `observed_behavior`: Observed behavior of the agent (categorical: "risky", "conservative").
*   `risk_taking_score`: Participant's score on a risk-taking measure (numeric, continuous or binary depending on data source).

## Data Schema (CSV)

```yaml
$schema: 'http://json-schema.org/draft-07/schema#'
type: array
items:
  type: object
  properties:
    participant_id:
      type: integer
      description: Unique identifier for the participant.
    status_level:
      type: string
      enum: ['high', 'low']
      description: Social status of observed agent.
    observed_behavior:
      type: string
      enum: ['risky', 'conservative']
      description: Observed behavior of the agent.
    risk_taking_score:
      type: number
      description: Participant's risk-taking score (continuous or binary).
  required:
    - participant_id
    - status_level
    - observed_behavior
    - risk_taking_score
```

## Data Relationships

The data is structured as a flat file, with each row representing a single observation from a participant. There are no explicit relationships between entities beyond the shared `participant_id` which facilitates repeated measures analysis, if applicable.

## Assumptions

*   `risk_taking_score` can be either continuous or binary depending on the chosen data source/simulation parameters.
*   The dataset will include sufficient observations to support a mixed-effects regression model with adequate statistical power (deferred).
*   Data types are appropriately represented and validated during preprocessing. **Data validation will verify that all `participant_id` values are integers, flagging any inconsistencies for manual review.**
