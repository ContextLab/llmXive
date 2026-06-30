# Reproduce & validate: OmniRetrieval: Unified Retrieval across Heterogeneous Knowledge Sources

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/   (clone of https://github.com/JinheonBaek/OmniRetrieval)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** OmniRetrieval: Unified Retrieval across Heterogeneous Knowledge Sources

**Abstract:** Real-world information needs require access to structurally diverse knowledge sources, from unstructured text and relational tables to knowledge graphs and property graphs. Existing retrievers, however, operate over one source at a time under a fixed query language, leaving the broader landscape of available knowledge fragmented behind incompatible interfaces. A natural attempt at unification would collapse these sources into a shared space, but this erases the structural affordances (such as schemas, ontologies, compositional operators) that give each source its expressive power. Effective retrieval over diverse knowledge, therefore, requires not homogenization but an overarching layer that meets each source on its own terms. To achieve this, we present OmniRetrieval, a framework that takes any natural-language query, identifies appropriate knowledge sources, and dispatches source-native queries to their native execution engines. Across an extensive benchmark spanning 13 datasets and 309 distinct knowledge bases over text, relational, and graph-structured sources, OmniRetrieval exceeds single-source baselines, demonstrating that it can serve as a general-purpose interface to the heterogeneous sources while preserving the structural distinctions that make each source valuable.

## Shipped code — file tree (`projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/`)

```
.gitignore
LICENSE
README.md
assets/overview.png
evaluate.py
main.py
requirements.txt
scripts/cache_cypher_answers.py
scripts/cache_sparql_answers.py
scripts/data/download_all.sh
scripts/data/download_beir.py
scripts/data/download_bird.py
scripts/data/download_lcquad2.py
scripts/data/download_qald10.py
scripts/data/download_simplequestions.py
scripts/data/download_spider.py
scripts/data/download_text2cypher.py
scripts/data/preprocess_all.sh
scripts/data/preprocess_beir.py
scripts/data/preprocess_bird.py
scripts/data/preprocess_lcquad2.py
scripts/data/preprocess_qald10.py
scripts/data/preprocess_simplequestions.py
scripts/data/preprocess_spider.py
scripts/data/preprocess_text2cypher.py
scripts/data/wikidata_labels.py
scripts/encode_corpora.py
src/data/beir_corpora.py
src/data/cypher_corpora.py
src/data/datasets.py
src/data/schema.py
src/data/sparql_corpora.py
src/evaluation/__init__.py
src/evaluation/judge.py
src/evaluation/metrics.py
src/model/__init__.py
src/model/llm_client.py
src/model/retrieval.py
src/utils.py
```

## Detected entry points

- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/main.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/evaluate.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/cache_cypher_answers.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/cache_sparql_answers.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/encode_corpora.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/src/utils.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/data/download_beir.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/data/download_bird.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/data/download_lcquad2.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/data/download_qald10.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/data/download_simplequestions.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/data/download_spider.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/data/download_text2cypher.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/data/preprocess_beir.py`
- `projects/PROJ-644-omniretrieval-unified-retrieval-across-h/external/OmniRetrieval/scripts/data/preprocess_bird.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `OmniRetrieval` — not re-implementing it.
