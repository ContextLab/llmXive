# Data Model: llmXive Follow-up: Semantic Divergence Diagnostic for Agentic Reasoning

## 1. Entity Relationship Diagram (Conceptual)

```mermaid
erDiagram
    ProblemInstance ||--o{ ToolMapping : "has"
    ProblemInstance ||--o{ ToolDistribution : "retrieves"
    ProblemInstance ||--o{ DivergenceMetric : "calculates"
    ProblemInstance ||--o{ RLOutcome : "correlates_with"
    DivergenceMetric ||--o{ Prediction : "predicts"

    ProblemInstance {
        string problem_id PK
        string thinking_prefix
        string[] ground_truth_tools
        number difficulty "Normalized difficulty score (0‑1) from MathVista metadata."
    }
    ToolMapping {
        string problem_id PK
        string[] ground_truth_tools
    }
    ToolDistribution {
        string[] retrieved_tool_ids
        number[] bm25_scores
        number[] centroid_embedding "DistilBERT 768‑dim vector."
    }
    DivergenceMetric {
        number cosine_similarity "∈ [‑1, 1]"
        number semantic_divergence_score "1 - cosine_similarity"
    }
    RLOutcome {
        number failure_rate "∈ [0, 1]"
        string success_failure "Derived: Failure if failure_rate ≥ 0.5"
    }
    Prediction {
        string predicted_outcome "Success | Failure"
        number prediction_probability "∈ [0, 1]"
    }
```

## 2. Data Flow

1. **Ingestion**: `ProblemInstance` loaded from MathVista (Parquet).  
2. **Tool Mapping**: `ToolMapping` CSV (checksum‑verified) supplies `ground_truth_tools`. **If missing**, a deterministic synthetic mapping based on `difficulty` is generated (see Research.md).  
3. **Retrieval**: `ToolDistribution` generated via BM25 over `tool_descriptions.csv`. **If missing**, a synthetic tool corpus is generated (see Research.md).  
4. **Embedding**: `thinking_prefix` and each retrieved tool description → DistilBERT vectors.  
5. **Metric Calculation**: `DivergenceMetric` derived from vectors.  
6. **Enrichment**: `RLOutcome` joined from external `rl_failure_rates.csv`. **If missing**, synthetic failure rates are generated independently from the tool mapping (see Research.md).  
7. **Analysis**: Logistic regression → `Prediction`. (K‑Means clustering is used only for risk‑group labeling, not as a predictor.)

All transformations produce new files; original raw files remain unchanged, satisfying Constitution Principle III.

## 3. Schema Definitions (refer to contracts)

- `ProblemInstance` → `contracts/dataset.schema.yaml` (includes optional `difficulty`).  
- `ToolDistribution`, `DivergenceMetric`, `RLOutcome`, `Prediction` → `contracts/output.schema.yaml`.
