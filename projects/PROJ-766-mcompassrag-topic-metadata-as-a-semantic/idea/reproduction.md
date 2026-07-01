# Reproduce & validate: MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level Retrieval

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/   (clone of https://github.com/AmirAbaskohi/MCompassRAG)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level Retrieval

**Abstract:** Retrieval-augmented generation (RAG) systems depend critically on how documents are chunked and searched. Fine-grained chunks can improve retrieval precision but expand the search space, increasing latency and cost; larger chunks reduce the number of candidates but make dense similarity less reliable, as the representation for each chunk mixes multiple topics and introduces more semantic noise. This trade-off becomes especially limiting in deep research tasks, where retrieval must be both fast and precise across large, heterogeneous corpora. We introduce MCompassRAG, a metadata-guided retrieval framework that uses topic-level signals as a semantic compass for selecting relevant evidence. Instead of relying only on cosine similarity between queries and noisy chunk embeddings, MCompassRAG enriches chunk representations with topic metadata in the same embedding space and trains a lightweight retriever through LLM-teacher distillation. At inference time, MCompassRAG performs topic-aware retrieval without additional LLM calls, improving both efficiency and evidence quality. Across six complex retrieval benchmarks, MCompassRAG improves information efficiency (IE) by 8.24% on average with over 5 times lower latency than the strongest efficient RAG baselines. Code is available on https://github.com/AmirAbaskohi/MCompassRAG.

## Shipped code — file tree (`projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/`)

```
.gitignore
LICENSE
README.md
configs/gen_train_data.yaml
configs/rag/cemtm.yaml
configs/rag/cwtm.yaml
configs/rag/etm.yaml
configs/rag/softltm.yaml
configs/train_retriever.yaml
configs/train_topic_model.yaml
data_gen/__init__.py
data_gen/build_training_data.py
data_gen/negatives.py
data_gen/openrouter_client.py
data_gen/query_gen.py
data_gen/teacher.py
misc/logo.png
misc/method.png
requirements.txt
scripts/build_index.sh
scripts/gen_train_data.sh
scripts/run_rag.sh
scripts/setup.sh
scripts/train_retriever.sh
scripts/train_topic_model.sh
src/__init__.py
src/config.py
src/encoders/__init__.py
src/encoders/backbone.py
src/encoders/retriever_encoder.py
src/index/__init__.py
src/index/chunking.py
src/index/metadata_bank.py
src/inference/__init__.py
src/inference/retrieve.py
src/models/__init__.py
src/models/abstraction.py
src/models/compass_retriever.py
src/models/scorer.py
src/models/selector.py
src/pipeline.py
src/run.py
src/training/__init__.py
src/training/dataset.py
src/training/losses.py
src/training/train.py
src/training/trainer.py
topic_models/__init__.py
topic_models/base.py
topic_models/cemtm_adapter.py
topic_models/cwtm_adapter.py
topic_models/etm_adapter.py
topic_models/registry.py
topic_models/softltm_adapter.py
topic_models/train_topic_model.py
topic_models/wikiweb2m.py
```

## Detected entry points

- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/src/run.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/src/training/train.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/data_gen/build_training_data.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/data_gen/negatives.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/data_gen/openrouter_client.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/data_gen/query_gen.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/data_gen/teacher.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/src/config.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/src/pipeline.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/topic_models/base.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/topic_models/cemtm_adapter.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/topic_models/cwtm_adapter.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/topic_models/etm_adapter.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/topic_models/registry.py`
- `projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/external/MCompassRAG/topic_models/softltm_adapter.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `MCompassRAG` — not re-implementing it.
