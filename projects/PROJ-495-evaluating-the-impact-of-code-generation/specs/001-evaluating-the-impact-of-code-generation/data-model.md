# Data Model: Evaluating the Impact of Code Generation on Code Vulnerability Density

## Entities

### CodeSample (`data/derived/file_manifest.csv`)
| Field | Type | Description |
|---|---|---|
| file_id | string (uuid) | Stable identifier for the file |
| rel_path | string | Relative path under `data/raw/` |
| source_group | enum: `llm` \| `human` | Origin of the code |
| language | enum: `python` \| `javascript` \| `java` \| `other` | Detected programming language |
| loc | integer \| null | Non‑comment, non‑blank lines of code (null if not computed) |
| status | enum: `ok` \| `parse_error` \| `skipped_size` \| `skipped_zero_loc` | Ingestion/analysis outcome |

### VulnerabilityRecord (`data/derived/findings.csv`)
| Field | Type | Description |
|---|---|---|
| finding_id | string (uuid) | Stable identifier for the finding |
| file_id | string (FK → CodeSample) | Owning file |
| tool | enum: `bandit` \| `semgrep` \| `sonarqube` | Analyzer that reported the finding |
| cwe_id | string (pattern `^CWE-[0-9]+$`) | CWE identifier |
| severity | string | Tool‑reported severity level |
| line_number | integer \| null | Source line of the finding (if available) |

### PerFileAnalysis (`data/derived/per_file_analysis.csv`)
| Field | Type | Description |
|---|---|---|
| file_id | string (FK → CodeSample) | File identifier |
| source_group | enum: `llm` \| `human` | Repeated for convenience |
| language | enum: `python` \| `javascript` \| `java` \| `other` | Language |
| loc | integer \| null | Lines of code |
| vulnerability_count | integer (≥ 0) | Total findings for the file |
| corrected_vulnerability_count | integer (≥ 0) | Vulnerability count after adjusting for audit‑derived false‑positive rate |
| cwe_ids | array of strings (`CWE-####`) | Unique CWE IDs present |
| density | number \| string (`"undefined"`) | Vulnerabilities per LOC (raw) |
| density_corrected | number \| string (`"undefined"`) | Vulnerabilities per LOC after false‑positive correction |
| tools_run | array of `bandit`/`semgrep`/`sonarqube` | Which tools produced findings |

### AnalysisResult (`results/tables/group_summary.csv` + `statistical_tests.csv`)
| Field | Type | Description |
|---|---|---|
| group | enum: `llm` \| `human` | Code source |
| n_files | integer | Files successfully analyzed |
| mean_density | number \| null | Mean vulnerability density (raw) |
| median_density | number \| null | Median density (raw) |
| sd_density | number \| null | Standard deviation (raw) |
| mean_density_corrected | number \| null | Mean density after audit correction |
| median_density_corrected | number \| null | Median corrected density |
| sd_density_corrected | number \| null | Std‑dev corrected density |
| test_name | enum: `negbin` \| `mannwhitneyu` | Test identifier |
| p_value | number \| null | Raw p‑value |
| p_adjusted | number \| null | Holm‑Bonferroni‑adjusted p‑value |
| coefficient | number \| null | NB log‑rate ratio (if applicable) |
| ci_low | number \| null | 95 % CI lower bound |
| ci_high | number \| null | 95 % CI upper bound |
| significant | boolean \| null | True if `p_adjusted` < α |
| power_estimate | number \| null | Estimated statistical power for the primary test |

### AuditRecord (`data/derived/audit_verdicts.csv`)
| Field | Type | Description |
|---|---|---|
| finding_id | string (FK → VulnerabilityRecord) | Audited finding |
| verdict | enum: `true_positive` \| `false_positive` \| blank | Human judgement |
| auditor_id | string | Identifier of the reviewer |

## Derivation Chain (Constitution III/IV)

`data/raw/*` → **Ingest** → `file_manifest.csv` → **Static analysis** → `findings.csv` & `per_file_analysis.csv` → **Density & audit‑adjusted counts** → `per_file_analysis.csv` (now includes corrected fields) → **Group summary** → `group_summary.csv` → **Statistical tests** → `statistical_tests.csv` → **Figures** → `results/figures/*`.  

Each step records its input hash, output hash, script name, and random seed (if any) in `data/derived/provenance.json`.

---


