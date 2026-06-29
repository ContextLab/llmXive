# Data Model: Neuro‑Symbolic Learning Networks

## Entity Definitions

### Problem

Represents a single mathematics or logic exercise from the source dataset.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| problem_id | string | Unique identifier for the problem | ASSISTments dataset |
| prompt_text | string | Full problem statement text | ASSISTments dataset (must verify availability) |
| solution | string | Correct solution or answer key | ASSISTments dataset (must verify availability) |
| difficulty | float | Problem difficulty score (0‑1) | Derived from ASSISTments correct_rate |
| skill_id | string | Associated skill/curriculum tag | ASSISTments dataset |

### Explanation

Represents an artifact generated for a problem under a specific condition.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| explanation_id | string | Unique identifier (hash of problem_id + condition + model_version) | Generated |
| problem_id | string | Foreign key to Problem | Problem.explanation_id |
| condition | enum | One of: "neural", "symbolic", "neuro_symbolic" | FR-002 |
| content | string | Full explanation text | Generated (LLM or rule‑based) |
| symbolic_trace | string | Formal symbolic reasoning trace (nullable for neural-only) | Generated (symbolic component) |
| model_version | string | Version of the explanation generation model | Config |
| generated_at | timestamp | UTC timestamp of generation | System |

### SimulationLog

Captures a single simulated or human student interaction.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| log_id | string | Unique identifier (hash) | Generated |
| problem_id | string | Foreign key to Problem | Problem |
| explanation_id | string | Foreign key to Explanation | Explanation |
| condition | enum | One of: "neural", "symbolic", "neuro_symbolic" | Explanation.condition |
| student_id | string | Unique identifier for student (simulated or human) | Generated |
| data_source | enum | One of: "simulated", "human_pilot", "human_real" | FR-011 |
| correct | boolean | Binary correctness flag | FR-004 |
| rt_seconds | float | Response time in seconds (0.1s precision) | FR-004 |
| comprehension_rating | integer | 1‑5 Likert scale rating | FR-004 |
| prior_knowledge_score | float | Student's prior knowledge (0‑1) | BKT simulation or human data |
| logged_at | timestamp | UTC timestamp of interaction | System |

## Data Flow

```
[ASSISTments Dataset] 
    → [Download: fetch_datasets.py] 
    → [data/raw/assistments_skill_builder.csv] (checksummed)
    → [Validate: check prompt_text, solution fields]
    
[Problem Records] 
    → [Generate: explanation_generator.py] 
    → [data/derived/explanations_neural.jsonl]
    → [data/derived/explanations_symbolic.jsonl]
    → [data/derived/explanations_neuro_symbolic.jsonl]
    
[Human Pilot Data (≥50 participants)] 
    → [Collect: IRB‑approved study]
    → [data/pilot/human_calibration.csv] (checksummed)
    
[Human Pilot Data] 
    → [Calibrate: calibration.py] 
    → [BKT Parameters: P(L0), P(T), P(S), P(G)]
    
[Calibrated BKT] 
    → [Simulate: run_simulation.py] 
    → [data/derived/simulation_logs.csv] (≥6,000 records)
    
[Human Real Data (≥200 participants)] 
    → [Collect: IRB‑approved study]
    → [data/derived/human_real_data.csv] (checksummed)
    
[Simulation Logs + Human Real Data] 
    → [Merge: analysis pipeline]
    → [data/derived/combined_dataset.csv] (≥6,200 records)
    
[Combined Dataset] 
    → [Analyze: mixed_effects.py] 
    → [data/derived/regression_results.json]
    → [data/derived/effect_sizes.json]
```

## Data Hygiene Rules

1. **Checksumming**: All files under `data/raw/` and `data/pilot/` must be checksummed; hashes recorded in `state/projects/PROJ-559-neuro-symbolic-learning-networks-bridgin.yaml`
2. **No In‑Place Modification**: Raw data files are preserved unchanged; all transformations produce new files under `data/derived/`
3. **PII Protection**: No personally identifying information in committed data; student_ids are anonymized hashes
4. **Versioning**: Each artifact carries a content hash; `updated_at` timestamp updated on artifact change

## Constraints

| Constraint | Value | Source |
|------------|-------|--------|
| Max CPU cores | 2 | GitHub Actions free‑tier (FR-008) |
| Max memory | 7 GB | GitHub Actions free‑tier (FR-008) |
| Max disk | 14 GB | GitHub Actions free‑tier |
| Max runtime | 6 h | GitHub Actions free‑tier |
| Response time precision | 0.1 seconds | FR-004 |
| Comprehension rating range | 1‑5 (inclusive) | FR-004 |
| Minimum simulated interactions | Sufficient threshold | FR-009 |
| Minimum human pilot participants | sufficient number | FR-010 |
| Minimum human real participants | Sufficient sample size for statistical power | FR-011 |
| Calibration RMSE threshold | ≤0.15 | FR-010 |
| Calibration RMSE difference | ≤0.02 | FR-010 |
| Calibration t‑test p‑value | ≥0.10 | FR-010 |
