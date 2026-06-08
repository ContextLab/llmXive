---
action_items:
- id: 5c11321cbc97
  severity: writing
  text: Dataset versions not specified for reproducibility. Section 5.1 lists 13 datasets
    (Spider, BIRD, BEIR, etc.) but does not state version numbers or commit hashes.
    Add version identifiers for each dataset to enable exact replication.
- id: 9ae36fde2c0c
  severity: writing
  text: External endpoint URLs lack versioning. Appendix A references Wikidata SPARQL
    endpoint (query.wikidata.org/sparql) and Neo4j demo endpoint without version tags.
    These are mutable; archive snapshots or versioned endpoints should be cited.
- id: 98f7c5aa1dbc
  severity: writing
  text: Dataset licenses not itemized. Appendix A states "use each under its respective
    license" but does not enumerate licenses per dataset. Add a table mapping each
    of the 13 datasets to its specific license for compliance verification.
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
reviewed_at: '2026-06-08T07:51:03.441811Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper demonstrates strong attention to data provenance by compiling 13 existing public datasets into a unified benchmark spanning 309 knowledge bases (Section 5.1, lines 1-15). However, several data quality concerns require attention before publication.

**Dataset Versioning (Section 5.1):** The manuscript references Spider, BIRD, BEIR, SimpleQuestions, QALD-10, LC-QuAD 2.0, and Text2Cypher without specifying version numbers. For example, Spider has multiple releases (v1.0, v1.1, etc.), and BEIR has evolved since 2021. Without version identifiers, exact replication is impossible. Please add version tags or commit hashes for all 13 datasets in a dedicated reproducibility table.

**External Endpoint Stability (Appendix A):** The Wikidata SPARQL endpoint (query.wikidata.org/sparql) and Neo4j demo endpoint (neo4j+s://demo.neo4jlabs.com:7687) are cited without versioning or archival snapshots. These services change over time; queries that execute today may fail in six months. Recommend citing snapshot dates, using Wayback Machine archives, or providing Dockerized local copies where feasible.

**License Transparency (Appendix A, Section A.2):** While the paper states artifacts are used "under their respective license and terms," it does not enumerate licenses per dataset. For example, Spider uses CC BY-SA 4.0, BIRD may have different terms, and BEIR datasets vary. Add a table mapping each dataset to its specific license for compliance verification.

**Missing-Data Handling:** The benchmark spans heterogeneous knowledge sources with varying completeness levels. No protocol is described for handling empty query results, missing triples in Wikidata, or incomplete rows in relational databases. Since metrics like Execution Match depend on gold query outputs, clarify how incomplete data affects evaluation.

These are primarily writing-level fixes that strengthen reproducibility without requiring new experiments.
