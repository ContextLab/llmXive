# Reproduce & validate: SciAtlas: A Large-Scale Knowledge Graph for Automated Scientific Research

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/   (clone of https://github.com/zjunlp/SciAtlas)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** SciAtlas: A Large-Scale Knowledge Graph for Automated Scientific Research

**Abstract:** The exponential growth of global academic output has confronted researchers and AI agents with an unprecedented ``information explosion,'' where fragmented and unstructured knowledge organization impedes deep interdisciplinary integration. Current academic retrieval tools predominantly rely on superficial keyword matching or vector-space semantic retrieval, which lack the topological reasoning capabilities required to navigate complex logical connections. Agentic deep-research-based frameworks are often prone to logical hallucinations and consuming high inference costs. To bridge this gap, in this report, we introduce SciAtlas, a large-scale, multi-disciplinary, heterogeneous academic resource knowledge graph designed as a panoramic scientific evolution network. By integrating over 43M papers from 26 disciplines, and a total of 157M entities and 3B triplets, SciAtlas provides a structured topological cognitive substrate that dismantles disciplinary barriers and furnishes AI agents with a global perspective. Furthermore, we develop a neuro-symbolic retrieval algorithm featuring tri-path collaborative recall and graph reranking, achieving a seamless transition from simple semantic matching to deterministic association discovery. We also present key application directions of SciAtlas, including literature review, automated research trend synthesis, idea positioning, and academic trajectory exploration, to demonstrate that SciAtlas can serve as an effective ``cognitive map'' to empower the full loop of automated scientific research while significantly reducing reasoning costs. We have released the interfaces for KG retrieval and various downstream tasks in our GitHub repo.

## Shipped code — file tree (`projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/`)

```
.env.example
.gitignore
LICENSE
README.md
README_zh.md
agent-skill/README.md
agent-skill/sciatlas-idea-evaluate/SKILL.md
agent-skill/sciatlas-idea-evaluate/agents/openai.yaml
agent-skill/sciatlas-idea-generate/SKILL.md
agent-skill/sciatlas-idea-generate/agents/openai.yaml
agent-skill/sciatlas-idea-grounding/SKILL.md
agent-skill/sciatlas-idea-grounding/agents/openai.yaml
agent-skill/sciatlas-literature-review/SKILL.md
agent-skill/sciatlas-literature-review/agents/openai.yaml
agent-skill/sciatlas-quick-paper-search/SKILL.md
agent-skill/sciatlas-quick-paper-search/agents/openai.yaml
agent-skill/sciatlas-researcher-review/SKILL.md
agent-skill/sciatlas-researcher-review/agents/openai.yaml
agent-skill/sciatlas-trend-report/SKILL.md
agent-skill/sciatlas-trend-report/agents/openai.yaml
docs/api/index.html
imgs/.DS_Store
imgs/agent-skill-demo.gif
imgs/field_distribution_pie.png
imgs/schema.png
references/README.md
references/search/.env.example
references/search/.gitignore
references/search/README.md
references/search/run_search.py
references/search/src/innoeval_search/__init__.py
references/search/src/innoeval_search/__main__.py
references/search/src/innoeval_search/cli.py
references/search/src/innoeval_search/combined/__init__.py
references/search/src/innoeval_search/combined/merge_search.py
references/search/src/innoeval_search/kg/__init__.py
references/search/src/innoeval_search/kg/candidate_fusion.py
references/search/src/innoeval_search/kg/config.py
references/search/src/innoeval_search/kg/encoder.py
references/search/src/innoeval_search/kg/graph_rerank.py
references/search/src/innoeval_search/kg/interface.py
references/search/src/innoeval_search/kg/models.py
references/search/src/innoeval_search/kg/neo4j_repository.py
references/search/src/innoeval_search/kg/pdf_reference_selector.py
references/search/src/innoeval_search/kg/pipeline.py
references/search/src/innoeval_search/kg/query_understanding.py
references/search/src/innoeval_search/kg/recall_embedding_path.py
references/search/src/innoeval_search/kg/recall_keyword_path.py
references/search/src/innoeval_search/kg/recall_title_path.py
references/search/src/innoeval_search/kg/reranker.py
references/search/src/innoeval_search/s2/__init__.py
references/search/src/innoeval_search/s2/keyword_extractor.py
references/search/src/innoeval_search/s2/pipeline.py
references/search/src/innoeval_search/shared/__init__.py
references/search/src/innoeval_search/shared/llm_client.py
references/search/src/innoeval_search/shared/pdf_extraction/__init__.py
references/search/src/innoeval_search/shared/pdf_extraction/__main__.py
references/search/src/innoeval_search/shared/pdf_extraction/cli.py
references/search/src/innoeval_search/shared/pdf_extraction/extractor.py
references/search/src/innoeval_search/shared/pdf_extraction/grobid_client.py
references/search/src/innoeval_search/shared/pdf_extraction/models.py
references/search/src/innoeval_search/shared/pdf_extraction/parser.py
references/search/src/innoeval_search/shared/text_utils.py
requirements.txt
run_sciatlas.py
sciatlas/.env.example
sciatlas/.gitignore
sciatlas/MANIFEST.in
sciatlas/README.md
sciatlas/README_skills.md
sciatlas/__init__.py
sciatlas/cli.py
sciatlas/core/__init__.py
sciatlas/core/api_client.py
sciatlas/core/common.py
sciatlas/core/schemas.py
sciatlas/evidence/__init__.py
sciatlas/evidence/grounding.py
sciatlas/evidence/pdf_manifest.py
sciatlas/evidence/utils.py
sciatlas/evidence/vendor/pdf_extraction/__init__.py
sciatlas/evidence/vendor/pdf_extraction/__main__.py
sciatlas/evidence/vendor/pdf_extraction/cli.py
sciatlas/evidence/vendor/pdf_extraction/extractor.py
sciatlas/evidence/vendor/pdf_extraction/grobid_client.py
sciatlas/evidence/vendor/pdf_extraction/models.py
sciatlas/evidence/vendor/pdf_extraction/parser.py
sciatlas/examples/idea_evaluate.sh
sciatlas/examples/literature_review.sh
sciatlas/examples/search_papers.sh
sciatlas/llm/__init__.py
sciatlas/llm/base.py
sciatlas/llm/client.py
sciatlas/llm/openai_compatible.py
sciatlas/llm/prompts.py
sciatlas/pyproject.toml
sciatlas/renderers/__init__.py
sciatlas/renderers/markdown.py
sciatlas/search/__init__.py
sciatlas/search/planner.py
sciatlas/search/reranker.py
sciatlas/src/sciatlas/__init__.py
sciatlas/src/sciatlas/builtin_skills.json
sciatlas/src/sciatlas/cli.py
sciatlas/src/sciatlas/client.py
sciatlas/src/sciatlas/config.py
sciatlas/src/sciatlas/skills.py
sciatlas/tasks/__init__.py
sciatlas/tasks/_shared.py
sciatlas/tasks/author_profile.py
sciatlas/tasks/dispatcher.py
sciatlas/tasks/grounded_review.py
sciatlas/tasks/idea_generation.py
sciatlas/tasks/related_authors.py
sciatlas/tasks/topic_trend_review.py
sciatlas/tests/test_cli_artifacts.py
sciatlas/tests/test_import.py
sciatlas.cmd
scripts/install-sciatlas-uv.ps1
scripts/install-sciatlas-uv.sh
```

## Detected entry points

- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/run_sciatlas.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/cli.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/references/search/run_search.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/core/api_client.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/core/common.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/core/schemas.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/evidence/grounding.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/evidence/pdf_manifest.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/evidence/utils.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/llm/base.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/llm/client.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/llm/openai_compatible.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/llm/prompts.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/renderers/markdown.py`
- `projects/PROJ-623-sciatlas-a-large-scale-knowledge-graph-f/external/SciAtlas/sciatlas/search/planner.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `SciAtlas` — not re-implementing it.
