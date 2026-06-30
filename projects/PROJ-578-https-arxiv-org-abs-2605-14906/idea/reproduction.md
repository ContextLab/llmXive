# Reproduce & validate: MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/   (clone of https://github.com/xrenaf/MEMLENS)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models

**Abstract:** Memory is essential for large vision-language models (LVLMs) to handle long, multimodal interactions, with two method directions providing this capability: long-context LVLMs and memory-augmented agents. However, no existing benchmark conducts a systematic comparison of the two on questions that genuinely require multimodal evidence. To close this gap, we introduce MEMLENS, a comprehensive benchmark for memory in multimodal multi-session conversations, comprising 789 questions across five memory abilities (information extraction, multi-session reasoning, temporal reasoning, knowledge update, and answer refusal) at four standard context lengths (32K-256K tokens) under a cross-modal token-counting scheme. An image-ablation study confirms that solving MEMLENS requires visual evidence: removing evidence images drops two frontier LVLMs below 2% accuracy on the 80.4% of questions whose evidence includes images. Evaluating 27 LVLMs and 7 memory-augmented agents, we find that long-context LVLMs achieve high short-context accuracy through direct visual grounding but degrade as conversations grow, whereas memory agents are length-stable but lose visual fidelity under storage-time compression. Multi-session reasoning caps most systems below 30%, and neither approach alone solves the task. These results motivate hybrid architectures that combine long-context attention with structured multimodal retrieval. Our code is available at https://github.com/xrenaf/MEMLENS.

## Shipped code — file tree (`projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/`)

```
.gitattributes
.gitignore
CITATION.cff
LICENSE-CODE
README.md
answer_extraction.py
data.py
eval.py
eval_api.py
judge_prompts/__init__.py
judge_prompts/answer_refusal.py
judge_prompts/base.py
judge_prompts/information_extraction.py
judge_prompts/knowledge_update.py
judge_prompts/multi_session_reasoning.py
judge_prompts/temporal_reasoning.py
llm_judge.py
memory-agent/README.md
memory-agent/prompt_builders.py
parse_utils.py
requirements.txt
scripts/run_api.sh
scripts/run_benchmark.sh
scripts/run_eval.sh
utils.py
vlm_models/__init__.py
vlm_models/anthropic_api.py
vlm_models/cosmos_reason.py
vlm_models/gemini_api.py
vlm_models/gemma3.py
vlm_models/gemma3_vllm.py
vlm_models/gemma4.py
vlm_models/glm46v.py
vlm_models/glm46v_vllm.py
vlm_models/glm4v_vllm.py
vlm_models/kimi_api.py
vlm_models/model_utils.py
vlm_models/nemotron_vl.py
vlm_models/nemotron_vllm.py
vlm_models/openai_api.py
vlm_models/phi4_hf.py
vlm_models/phi4_vllm.py
vlm_models/qwen2_5_vl.py
vlm_models/qwen2_vl.py
vlm_models/qwen3_vl.py
vlm_models/qwen3_vl_moe.py
vlm_models/qwen3_vl_moe_vllm.py
```

## Detected entry points

- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/eval.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/answer_extraction.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/data.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/eval_api.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/llm_judge.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/parse_utils.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/utils.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/judge_prompts/answer_refusal.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/judge_prompts/base.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/judge_prompts/information_extraction.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/judge_prompts/knowledge_update.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/judge_prompts/multi_session_reasoning.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/judge_prompts/temporal_reasoning.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/memory-agent/prompt_builders.py`
- `projects/PROJ-578-https-arxiv-org-abs-2605-14906/external/MEMLENS/vlm_models/anthropic_api.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `MEMLENS` — not re-implementing it.
