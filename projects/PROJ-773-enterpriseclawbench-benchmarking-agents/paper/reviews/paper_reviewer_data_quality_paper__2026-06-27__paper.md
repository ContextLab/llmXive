---
action_items:
- id: 4a0865fe1aed
  severity: writing
  text: Add formal schema documentation for benchmark task structure (task_id, fixtures,
    rubrics, taxonomy fields) with field types and constraints.
- id: 7a8b14775505
  severity: writing
  text: Document benchmark version number and construction pipeline version; include
    changelog for any future releases.
- id: 68b248870325
  severity: writing
  text: Provide inter-annotator agreement metrics for the 120-task Lite set human
    audit (e.g., Cohen's kappa, percent agreement).
- id: edd820574ae6
  severity: writing
  text: Clarify the 2026-dated arXiv citations and provenance; ensure all external
    links are stable or archived.
artifact_hash: 436f60fbb896e41d063ceb9811d2249a06e1b5eaa235430cfaccb20cf6596607
artifact_path: projects/PROJ-773-enterpriseclawbench-benchmarking-agents/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T00:56:38.730407Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

**Data Quality Review — EnterpriseClawBench**

This review focuses exclusively on data provenance, schema, missing-data handling, version control, and external link stability.

**Provenance and Release Status**
The paper states the benchmark is constructed from "continuous internal use of an enterprise agent system at an AI startup with more than 100 employees, covering workplace sessions from March to May 2026" (Section: Enterprise setting). The benchmark data is explicitly NOT released due to proprietary concerns (Introduction, Limitations). While this is understandable for enterprise data, it prevents independent verification of data quality, redaction effectiveness, and task construction fidelity. The paper should at minimum provide a data card (following Datasheets for Datasets conventions) describing the data collection process, even if the data itself cannot be shared.

**Schema Documentation**
The appendix shows informal schema examples (task_id, business_task, user_messages, cleaning.length, cleaning.fixture, redaction recovery fields, taxonomy fields). However, there is no formal schema specification (e.g., JSON Schema, Pydantic models) documenting field types, constraints, and required vs. optional fields. This makes it difficult for readers to understand the exact data structure or reproduce the construction pipeline. I recommend adding a schema appendix or linking to a schema definition file.

**Missing-Data Handling**
The paper describes several mechanical gates that reject instances with missing or problematic data (length filtering, fixture recovery, network reachability, self-containment checks). Figure 2 shows a construction funnel, but the exact rejection counts at each stage are not quantified in the text. The paper should report: (1) total raw TaskInstances, (2) rejection counts at each gate, (3) final accepted count (852 tasks). This transparency is critical for understanding selection bias.

**Version Control**
No benchmark version number or pipeline version is mentioned. For reproducibility, the paper should specify a version identifier (e.g., "EnterpriseClawBench v1.0") and document any planned updates or versioning strategy.

**External Links and Citation Provenance**
The bibliography contains multiple arXiv citations dated 2026 (e.g., workspacebench2026, wildclawbench2026, clawbench2026). The paper's own arXiv URL (https://arxiv.org/abs/2606.23654) is also future-dated. This raises questions about the paper's actual provenance and whether these are real publications or simulated references. All external links should be verified for stability, and future-dated citations should be clarified or corrected.

**Human Annotation Quality**
The 120-task Lite set is "manually audited" (Abstract), but no inter-annotator agreement metrics are provided. For the human judge calibration audit (48 packets, Table 5), the paper reports MAE and Spearman correlation but not annotator agreement. This limits confidence in the human evaluation quality.

**Recommendations**
1. Add a data card describing collection process, even if data is not released.
2. Provide formal schema documentation for benchmark task structure.
3. Report exact rejection counts at each construction gate.
4. Add benchmark version number and pipeline version.
5. Clarify future-dated citations and verify external link stability.
6. Report inter-annotator agreement for human audits.
