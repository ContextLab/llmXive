# Data Model: Evaluating the Impact of Code Generation on Software Security

## Overview
The pipeline manipulates four core entities (three from the original spec plus one added for the paired statistical test). Each entity is defined by a JSON Schema stored under `contracts/`.

| Entity | Purpose |
|--------|---------|
| **CodeSample** | Represents a single code snippet (human or LLM‑generated). |
| **VulnerabilityFinding** | Represents a single static‑analysis detection linked to a `CodeSample`. |
| **PairOutcome** | Captures the binary presence/absence of a given vulnerability type for both members of a paired sample, enabling a 2×2 McNemar contingency table. |
| **AnalysisResult** | Summarises aggregated counts and statistical test outcomes per vulnerability type. |

All schemas are validated by the test suite (`tests/contract/test_contracts.py`) and are referenced in the CI contracts.

## Entity Summaries (informal)

### CodeSample
- `sample_id` (UUID) – unique identifier.  
- `source` (`"human"` | `"llm"`).  
- `functionality_id` (string) – stable identifier linking the human and LLM versions.  
- `syntax_valid` (bool).  
- `functional_equivalence_verified` (bool).  
- `raw_content` (string).  
- `language` (string, e.g., `"python"`).  
- `lines_of_code` (integer, optional) – **LOC** metric required by FR‑011.  
- `cyclomatic_complexity` (integer, optional) – computed via radon (confounder metric).  
- `length` (integer, optional) – token count (retained for possible secondary analyses).

### VulnerabilityFinding
- `finding_id` (UUID).  
- `code_sample_id` (UUID).  
- `tool_source` (`"semgrep"` | `"sonarqube"` | `"bandit"` | `"codeql"`).  
- `vulnerability_type` (string, OWASP category).  
- `severity` (`"LOW"` | `"MEDIUM"` | `"HIGH"` | `"CRITICAL"`).  
- `line_number` (int ≥ 1).  
- `confidence_score` (float ∈ [0, 1]).  
- `rule_id` (string).  
- `validated_by_audit` (bool, optional).

### PairOutcome *(new)*
- `pair_id` (UUID) – same as `functionality_id`.  
- `vulnerability_type` (string).  
- `human_flag` (bool).  
- `llm_flag` (bool).

### AnalysisResult
- `result_id` (UUID).  
- `vulnerability_type` (string).  
- `human_count` (int ≥ 0).  
- `llm_count` (int ≥ 0).  
- `total_pairs` (int ≥ 0).  
- `p_value` (float ∈ [0, 1]).  
- `p_value_adj` (float ∈ [0, 1]).  
- `is_significant` (bool).  
- `test_method` (`"McNemar"` | `"Exact McNemar"`).  
- `confidence_threshold` (float ∈ [0, 1] | null).

These definitions are formally captured in the YAML contracts provided alongside this document.

---

