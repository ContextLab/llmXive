# Data Model: Evaluating the Impact of Code Generation on Software Security

## Overview
The research pipeline manipulates three core entities, plus an auxiliary pairing construct needed for the paired statistical test:

| Entity | Purpose |
|--------|---------|
| **CodeSample** | Represents a single code snippet (human or LLM‑generated). |
| **VulnerabilityFinding** | Represents a single static‑analysis detection linked to a `CodeSample`. |
| **AnalysisResult** | Summarises aggregated counts and statistical test outcomes per vulnerability type. |
| **PairOutcome** *(new)* | Captures the binary presence/absence of a given vulnerability type for **both** members of a paired sample, enabling a proper 2×2 McNemar contingency table. |

All entities are defined by JSON‑compatible schemas stored under `contracts/`. The schemas are also used by the test suite (`tests/contract/test_contracts.py`) to validate generated artefacts.

## Entity Definitions (informal)

### CodeSample
- `sample_id`: UUID string.
- `source`: `"human"` or `"llm"`.
- `functionality_id`: Stable identifier linking paired samples (e.g., original dataset row ID).
- `syntax_valid`: Boolean.
- `functional_equivalence_verified`: Boolean.
- `raw_content`: String (the source code).
- `language`: `"python"` | `"c"` | … (derived from file extension).

### VulnerabilityFinding
- `finding_id`: UUID string.
- `code_sample_id`: UUID referencing `CodeSample`.
- `tool_source`: `"semgrep"` | `"sonarqube"`.
- `vulnerability_type`: String (e.g., `"SQL Injection"` – aligns with OWASP Top 10).
- `severity`: `"LOW"` | `"MEDIUM"` | `"HIGH"` | `"CRITICAL"`.
- `line_number`: Integer.
- `confidence_score`: Float in `[0, 1]` (Semgrep `confidence` or mapped SonarQube severity).
- `rule_id`: String (tool‑specific rule identifier).
- `validated_by_audit`: Boolean (optional; filled after manual audit).

### AnalysisResult
- `result_id`: UUID string.
- `vulnerability_type`: String.
- `human_count`: Integer (number of human samples flagged).
- `llm_count`: Integer (number of LLM samples flagged).
- `total_pairs`: Integer (size of the paired set for this type).
- `p_value`: Float (raw p‑value from McNemar’s test).
- `p_value_adj`: Float (Bonferroni‑adjusted p‑value).
- `is_significant`: Boolean (adjusted p < 0.05).
- `test_method`: String (`"McNemar"` or `"Exact McNemar"`).
- `confidence_threshold`: Float (the threshold used for this row; `null` for primary analysis).

### PairOutcome *(new)*
- `pair_id`: UUID string (matches the `functionality_id` of the two `CodeSample`s).
- `vulnerability_type`: String.
- `human_flag`: Boolean (1 = vulnerability detected in human code, 0 = not).
- `llm_flag`: Boolean (1 = vulnerability detected in LLM code, 0 = not).

These definitions are formally captured in the YAML contracts below, with `PairOutcome` added to support the paired McNemar analysis.

---

