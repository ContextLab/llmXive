---
action_items:
- id: 9f9f8b484368
  severity: writing
  text: No code artifacts (implementation files, test suites, dependency manifests)
    are provided in this submission. The paper mentions a GitHub repo (github.com/zjunlp/SciAtlas)
    but the actual code cannot be evaluated for modularity, test coverage, or reproducibility.
- id: 3f55179c17d2
  severity: writing
  text: The paper describes a Neo4j-based KG system with Python-based keyword extraction
    (Qwen3-30B-A3B), embedding generation (bge-large-en-v1.5), and retrieval algorithms.
    A code quality review requires access to the actual implementation to assess dependency
    hygiene, test coverage, and reproducibility from scratch.
- id: 031b4126e439
  severity: writing
  text: Section 5.2 (Construction) describes data pipelines but provides no code snippets,
    configuration files, or deployment scripts. For reproducibility assessment, include
    Dockerfile, requirements.txt, or conda environment specification in the artifact
    package.
artifact_hash: 2d03fe1e69a43f0e46e7519d0318b0a18b1fbc7fdac764f3d055c5b8406f650f
artifact_path: projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T00:52:13.045079Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

**Code Quality Assessment: Artifacts Not Available**

This review focuses exclusively on code quality of artifacts that produced the paper. However, the submission contains only the LaTeX paper source (`main.tex`, `sections/*.tex`, `references.bib`) with no accompanying implementation artifacts.

**What Cannot Be Evaluated:**

1. **Modularity**: The paper describes a tri-path retrieval algorithm (Section 4) with keyword matching, semantic matching, and graph propagation components. Without access to `retrieval.py` or equivalent modules, I cannot assess whether these are properly separated into cohesive units or if the 600+ line algorithm description translates to a single monolithic file.

2. **Tests**: No test files are provided. The retrieval scoring formulas (Eq. 1-12 in Section 4) should have corresponding unit tests for edge weight calculations, RWR convergence, and score normalization. A 157M node, 3B edge system requires integration tests for memory handling.

3. **Dependency Hygiene**: The paper references Qwen3-30B-A3B-Instruct-2507, bge-large-en-v1.5, GROBID, and Neo4j. No `requirements.txt`, `environment.yml`, or `pyproject.toml` is included to verify dependency versions and compatibility.

4. **Reproducibility from Scratch**: Section 5.2 describes OpenAlex data ingestion and keyword extraction pipelines. Without the actual ETL scripts, I cannot verify if the 43M paper graph can be reconstructed from scratch within reasonable compute resources.

5. **Truncation Risk**: The paper references CLI and skills for downstream tasks (Section 6). If implementation code exists, it should be split into smaller modules (<200 lines each) to avoid 32K token output limits during future revisions.

**Recommendation**: For a complete code quality review, the artifact package should include:
- `src/` directory with retrieval, construction, and API modules
- `tests/` directory with unit and integration tests
- `config/` for hyperparameters (λ values, thresholds from Section 4)
- `docker/` for reproducible deployment
- `docs/api.md` for Neo4j schema and Cypher query examples

Without these artifacts, the code quality lens cannot be properly applied.
