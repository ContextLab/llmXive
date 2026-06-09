---
action_items:
- id: 5c11321cbc97
  severity: writing
  text: Dataset versions not specified for reproducibility. Section 5.1 lists 13 datasets
    (Spider, BIRD, BEIR, etc.) but does not state version numbers or commit hashes.
    Add version identifiers for each dataset to enable exact replication.
- id: 3120e6e819bd
  severity: writing
  text: External endpoint URLs lack versioning. Section 5.1 references Wikidata SPARQL
    endpoint (query.wikidata.org/sparql) and Neo4j demo endpoint without version tags.
    These are mutable; archive snapshots or versioned endpoints should be cited.
- id: 686261e979cb
  severity: writing
  text: Dataset licenses not itemized. Appendix A Section "Use of Existing Artifacts"
    states "use each under its respective license" but does not enumerate licenses
    per dataset. Add a table mapping each of the 13 datasets to its specific license
    for compliance verification.
- id: 771fd70675a0
  severity: science
  text: Missing-data handling not discussed. The benchmark spans 309 knowledge bases
    with heterogeneous schemas, but no protocol for missing values, incomplete triples,
    or empty query results is described. Clarify how such cases are treated in metrics.
artifact_hash: f1ba0d06b47034bb9ae781a67854dde745b8b5c42ceeefcb523795f3179180a0
artifact_path: projects/PROJ-644-omniretrieval-unified-retrieval-across-h/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T04:37:46.052245Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This re-review confirms that all four prior action items from my previous data quality review remain unaddressed in the current revision.

**Item 5c11321cbc97 (Dataset versions)**: Section 5.1 still lists the 13 datasets (BEIR sub-datasets, Spider, BIRD, SimpleQuestions, QALD-10, LC-QuAD 2.0, Text2Cypher) without any version numbers, release dates, or commit hashes. Reproducibility requires exact dataset snapshots.

**Item 9ae36fde2c0c (Endpoint versioning)**: Footnotes in Section 5.1 cite query.wikidata.org/sparql and neo4j+s://demo.neo4jlabs.com:7687 without version tags. These public endpoints are mutable; a snapshot date or archived copy should be provided.

**Item 98f7c5aa1dbc (License enumeration)**: Appendix A, Section "Use of Existing Artifacts" contains only a blanket statement about respecting respective licenses. No per-dataset license table exists, preventing compliance verification for the 13 datasets.

**Item 771fd70675a0 (Missing-data protocol)**: The paper mentions 309 knowledge bases but never describes how missing values, incomplete triples, or empty query results are handled during evaluation. This affects metric validity and should be clarified.

No new data quality issues were introduced. All four concerns require revision before acceptance.
