# Data Model: Evaluating Automated Code Review Tools Effectiveness

## Entities

### Repository
- `owner`: str (GitHub owner)
- `name`: str (Repo name)
- `primary_language`: str (Java, Python, JavaScript, Go)
- `star_count`: int
- `commit_activity`: str (High, Medium, Low)
- `license`: str
- `clone_url`: str
- `commit_sha`: str

### Tool Issue
- `tool_name`: str (SonarQube, DeepSource, CodeClimate)
- `issue_id`: str
- `issue_type`: str (bug, security, style)
- `severity`: str (Critical, Major, Minor, Info)
- `file_path`: str
- `line_number`: int
- `description`: str
- `repository_id`: str (FK to Repository)

### Human Annotation
- `comment_id`: str
- `comment_text`: str
- `extracted_type`: str (bug, security, style) - *Retrieved via keyword heuristic*
- `file_path`: str
- `line_number`: int
- `validation_status`: str (validated, unvalidated, ambiguous)
- `is_actual_defect`: bool (True if validated by expert as actual defect - *Gold Standard*)
- `repository_id`: str (FK to Repository)

### Aligned Pair
- `tool_issue_id`: str (FK to Tool Issue)
- `human_annotation_id`: str (FK to Human Annotation)
- `match_method`: str (ast, semantic) - *Line tolerance removed as match method*
- `match_confidence`: float (0–1)
- `match_status`: str (matched, unmatched) - *Ambiguous removed; low confidence = unmatched*
- `line_tolerance_used`: bool (False - *Only used for sensitivity analysis, not matching*)

### Performance Metric
- `tool_name`: str
- `defect_category`: str (bug, security, style)
- `project_id`: str
- `precision`: float
- `recall_raw`: float (Recall of Commented Defects - RCD)
- `recall_estimated`: float (Estimated Recall via Capture-Recapture)
- `f1_score`: float

### CaptureRecaptureEstimate
- `project_id`: str
- `tool_findings_count`: int
- `human_findings_count`: int
- `overlap_count`: int
- `estimated_total_defects`: float (Lincoln-Petersen estimator)
- `confidence_interval_lower`: float
- `confidence_interval_upper`: float

## Relationships

- Repository → Tool Issue (1:N)
- Repository → Human Annotation (1:N)
- Tool Issue ↔ Human Annotation (N:N via Aligned Pair)
- Tool Issue → Performance Metric (N:1)
- Human Annotation → Performance Metric (N:1)
- Repository → CaptureRecaptureEstimate (1:1)

## Constraints

- All file paths normalized to relative paths.
- Line numbers 1-indexed.
- Validation status must be one of: validated, unvalidated, ambiguous.
- Match status must be one of: matched, unmatched.
- Match method must be one of: ast, semantic.
- `is_actual_defect` must be True for Gold Standard inclusion.
- `recall_estimated` is derived from `CaptureRecaptureEstimate`.
