# Data Model: llmXive follow‑up – Graph‑augmented Verifier Study

## 1. Raw Dataset (`raw_parquet`)
- **Location**: `data/raw/` (three parquet files downloaded from the verified URLs).  
- **Schema (informal)**: columns include `image_id`, `prompt`, `source_image_path`, etc., exactly as provided by InstructPix2Pix. No modification is performed.

## 2. Curated Prompt CSV (`curated_prompts.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `prompt_id` | string | Deterministic UUID for the prompt. |
| `instruction_type` | enum(`conflicting`, `neutral`) | Ground‑truth label (balanced groups of equal size). |
| `prompt_text` | string | Full natural‑language instruction. |
| `synthetic_score` | number (0.0‑1.0) | Rule‑based feasibility heuristic (used only for internal diagnostics; **not** for evaluation). |
| `human_score` | number (0.0‑1.0) | Independent human‑annotated feasibility score (primary ground‑truth). |
| `checksum` | string | SHA‑256 of the original parquet row (data hygiene). |

File path: `data/results/curated_prompts.csv`.

## 3. Human Validation CSV (`human_validation.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `prompt_id` | string | Links to `curated_prompts.csv`. |
| `human_rating` | number (0.0‑1.0) | Average rating from crowd workers. |
| `annotation_source` | string | e.g., `"MTurk"` or `"internal_form"`. |

File path: `data/results/human_validation.csv`.

## 4. Constraint Graph JSON (`graph_<prompt_id>.json`)
```yaml
graph_id: string          # same as prompt_id
nodes:
  - id: string            # e.g., "node_1"
    label: string         # principle phrase
    type: enum("principle")
edges:
  - source: string        # node id
    target: string        # node id
    label: enum("temporal-precedes", "contradiction")
    weight: number
metadata:
  parser_version: string
  parse_timestamp: string   # ISO‑8601
```
Stored under `data/results/graphs/`.

## 5. Baseline Scores CSV (`baseline_scores.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `prompt_id` | string | Links to `curated_prompts.csv`. |
| `verifier_score` | number (0.0‑1.0) | Alignment score from baseline verifier. |
| `human_score` | number (0.0‑1.0) | Copied from `curated_prompts.csv`. |
| `alignment_delta` | number | `verifier_score - human_score`. |

File path: `data/results/baseline_scores.csv`.

## 6. Augmented Scores CSV (`augmented_scores.csv`)
Same columns as `baseline_scores.csv` plus:
| Column | Type | Description |
|--------|------|-------------|
| `condition` | enum(`graph_augmented`, `control_filler`, `control_empty`) | Indicates which context was used. |

File path: `data/results/augmented_scores.csv`.

## 7. Final Evaluation Report (`report.json`)
```yaml
report_version: "1.0.0"
generated_at: "2026-10-22T12:00:00Z"
runtime_seconds: integer
memory_peak_gb: number
tests:
  primary:
    $ref: "#/definitions/test_result"
  robustness:
    $ref: "#/definitions/test_result"
multiple_comparison_correction:
  type: object
  required:
    - method
    - alpha
    - adjusted_p_values
  properties:
    method:
      type: string
      enum: ["benjamini_hochberg", "bonferroni"]
    alpha:
      type: number
      minimum: 0
      maximum: 1
    adjusted_p_values:
      type: object
      required:
        - primary
        - robustness
      properties:
        primary:
          type: number
          minimum: 0
          maximum: 1
        robustness:
          type: number
          minimum: 0
          maximum: 1
definitions:
  test_result:
    type: object
    required:
      - test_name
      - method
      - p_value
      - effect_size
      - ci_95
      - corrected
    properties:
      test_name:
        type: string
      method:
        type: string
        enum: ["paired_t_test", "wilcoxon"]
      p_value:
        type: number
        minimum: 0
        maximum: 1
      effect_size:
        type: number
        description: "Cohen's d for t‑test or rank‑biserial for Wilcoxon."
      ci_95:
        type: array
        minItems: 2
        maxItems: 2
        items:
          type: number
      corrected:
        type: boolean
        description: "True if p‑value has been corrected for multiple comparisons."
```
File path: `analysis/report.json`.

All CSV files are UTF‑8 encoded, line‑terminated with `\n`. JSON files are pretty‑printed with 2‑space indentation.

---
