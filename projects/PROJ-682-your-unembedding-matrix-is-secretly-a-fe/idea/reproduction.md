# Reproduce & validate: Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/   (clone of https://github.com/CentreChen/EmbFilter)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings

**Abstract:** Large language models exhibit impressive zero-shot capabilities across a wide range of downstream tasks. However, they struggle to function as off-the-shelf embedding models, leading to suboptimal performance on massive text embedding benchmarks. In this paper, we identify a potential cause underlying this deficiency. Our motivation stems from an unexpected observation: text embeddings tend to align with frequent but uninformative tokens when projected onto the vocabulary space. We argue that this excessive expression of high-frequency tokens suppresses the model's ability to capture nuanced semantics. To address this, we introduce EmbedFilter, a simple linear transformation designed to refine text embeddings derived from LLMs directly. Specifically, we uncover that the unembedding matrix within LLMs encodes a latent space that is actively writing these frequent tokens into embedding space. By filtering out this subspace, EmbedFilter suppress the influence of high-frequency tokens, thereby enhancing semantic representations. As a compelling byproduct, this enables an inherent dimensionality reduction, lowering index storage and speedup retrieval while fully preserving the refined embedding quality. Our experiments across multiple LLM backbones demonstrate that LLMs equipped with EmbedFilter achieve superior zero-shot downstream performance even with significantly reduced embedding dimensions. We hope our findings provide deeper insights into the mechanisms of LLM-based representations and inspire more principled designs to improve text embeddings training. Our code is available at https://github.com/CentreChen/EmbFilter.

## Shipped code — file tree (`projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/`)

```
.gitignore
LICENSE
README.md
eval.py
models/modeling_llama_lr.py
models/modeling_mistral_lr.py
models/modeling_qwen2_lr.py
requirements.txt
run4llama_echo.py
run4llama_prompteol.py
run4mistral_echo.py
run4mistral_prompteol.py
run4qwen_echo.py
run4qwen_prompteol.py
utils/tasks.py
utils/utils.py
```

## Detected entry points

- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/eval.py`
- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/run4llama_echo.py`
- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/run4llama_prompteol.py`
- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/run4mistral_echo.py`
- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/run4mistral_prompteol.py`
- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/run4qwen_echo.py`
- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/run4qwen_prompteol.py`
- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/models/modeling_llama_lr.py`
- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/models/modeling_mistral_lr.py`
- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/models/modeling_qwen2_lr.py`
- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/utils/tasks.py`
- `projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/external/EmbFilter/utils/utils.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `EmbFilter` — not re-implementing it.
