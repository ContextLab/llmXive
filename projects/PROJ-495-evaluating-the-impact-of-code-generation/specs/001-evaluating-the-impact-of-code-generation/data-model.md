# Data Model: Evaluating the Impact of Code Generation on Code Vulnerability Density

## Entities

### CodeSample (`data/derived/file_manifest.csv`, one row per file)
| Field | Type | Description |
|---|---|---|
| file_id | string (uuid) | Stable ID |
| rel_path | string | Path under `data/raw/` |
| source_group | enum: `llm` \| `human` | Code origin |
| language | enum: `python` \| `javascript` \| `java` \| `other` | Detected language |
| loc | integer | Non-comment, non-blank lines (computed in Phase 3) |
| status | enum: `ok` \| `parse_error` \| `skipped_size` | Ingest/analysis status |

### VulnerabilityRecord (`data/derived/findings.csv`, one row per finding)
| Field | Type | Description |
|---|---|---|
| finding_id | string (uuid) | Stable ID |
| file_id | string (FK → CodeSample) | Owning file |
| tool | enum: `bandit` \| `semgrep` | Detecting tool |
| cwe_id | string | e.g. `CWE-79` |
| severity | string | Tool-reported severity |
| line_number | integer | Finding location |

### AnalysisResult (`results/tables/group_summary.csv` + `statistical_tests.csv`)
| Field | Type | Description |
|---|---|---|
| group | enum: `llm` \| `human` | Group |
| n_files | integer | Files analyzed |
| mean_density / median_density / sd_density | float | Summary stats |
| test_name | enum: `negbin` \| `mannwhitneyu` | Test |
| p_value, p_adjusted | float | Raw and BH-adjusted p |
| coefficient, ci_low, ci_high | float | NB group coefficient (log rate ratio) |

### AuditRecord (`data/derived/audit_verdicts.csv`)
| Field | Type | Description |
|---|---|---|
| finding_id | string (FK → VulnerabilityRecord) | Audited finding |
| verdict | enum: `true_positive` \| `false_positive` \| blank | Human verdict |
| auditor_id | string | Auditor identifier |

## Derivation chain (Constitution III/IV)

`data/raw/*` → (ingest) → `file_manifest.csv` → (static analysis) → `findings.csv`, `per_file_analysis.csv` → (density) → `per_file_density.csv`, `group_summary.csv` → (stats) → `statistical_tests.csv` → (figures) → `results/figures/*`. Each step appends a record to `data/derived/provenance.json` (input hash, output hash, script, seed).
