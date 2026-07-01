# Reproduce & validate: PlanBench-XL: Evaluating Long-Horizon Planning of LLM Tool-Use Agents in Large-Scale Tool Ecosystems

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/   (clone of https://github.com/JiayuJeff/PlanBench-XL)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** PlanBench-XL: Evaluating Long-Horizon Planning of LLM Tool-Use Agents in Large-Scale Tool Ecosystems

**Abstract:** LLM agents increasingly operate in large tool ecosystems, where real-world tasks require discovering relevant tools, inferring implicit sub-goals, and adapting to dynamic environments over long horizons. However, existing benchmarks rarely evaluate planning under retrieval-limited tool visibility. To address this gap, we introduce PlanBench-XL, an interactive benchmark of 327 retail tasks over 1,665 tools that tests whether agents can iteratively retrieve usable tools, invoke them to uncover intermediate evidence for subsequent calls toward the final goal. PlanBench-XL further features an optional blocking mechanism that simulates real-world unpredictability through missing, failing, or distracting tool functions, forcing agents to detect disrupted paths and adapt at runtime. Experiments on ten leading LLMs show that massive-tool planning remains challenging: while GPT-5.4 achieves 51.90% accuracy in block-free settings, it collapses to 11.36% under the most severe blocking condition. Further analysis shows that agents are especially vulnerable when failures lack explicit error signals or when recovery requires longer alternative tool-use paths. These results establish PlanBench-XL as a testbed for diagnosing agentic planning failures and highlight the need for robust adaptive planning in long-horizon tasks with large, imperfect tool environments.

## Shipped code — file tree (`projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/`)

```
.gitignore
README.md
figures/Main_Table.png
figures/PlanBench_XL.png
scripts/run_retail_batch.py
src/data/retail/baseline_tools.json
src/data/retail/blocker_tools.json
src/data/retail/database.json
src/data/retail/datatypes.json
src/data/retail/noisy_tools.json
src/data/retail/paths_set_catalog.json
src/data/retail/queries.json
src/data/retail/tasks.json
src/env/__init__.py
src/env/config/.env.example
src/env/config/base/env.yaml
src/env/config/model_registry.yaml
src/env/config/models/openai/deepseek-v4-flash.yaml
src/env/config/models/openai/gemini-3.1-pro.yaml
src/env/config/models/openai/gemini-3.5-flash.yaml
src/env/config/models/openai/gpt-5.4-mini.yaml
src/env/config/models/openai/gpt-5.4.yaml
src/env/config/models/openai/llama3.1-8b-local.yaml
src/env/config/models/openai/llama3.3-70b-local.yaml
src/env/config/models/openai/qwen3-14b-local.yaml
src/env/config/models/openai/qwen3-32b-local.yaml
src/env/config/models/openai/qwen3-8b-local.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_blocker.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_default.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_feedback.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_finegrain_long.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_finegrain_short.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_noise_ratio_0p2.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_noise_ratio_0p4.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_noise_ratio_0p6.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_noise_ratio_0p8.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_noise_type_explicit.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_noise_type_implicit.yaml
src/env/config/runs/retail/deepseek-v4-flash/retail_deepseek_v4_flash_noise_type_misleading.yaml
src/env/config/runs/retail/gemini-3.1-pro/retail_gemini3_1_pro_default.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_blocker.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_default.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_feedback.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_finegrain_long.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_finegrain_short.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_noise_ratio_0p2.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_noise_ratio_0p4.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_noise_ratio_0p6.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_noise_ratio_0p8.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_noise_type_explicit.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_noise_type_implicit.yaml
src/env/config/runs/retail/gemini-3.5-flash/retail_gemini3_5_flash_noise_type_misleading.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_blocker.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_default.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_feedback.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_finegrain_long.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_finegrain_short.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_noise_ratio_0p2.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_noise_ratio_0p4.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_noise_ratio_0p6.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_noise_ratio_0p8.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_noise_type_explicit.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_noise_type_implicit.yaml
src/env/config/runs/retail/gpt-5.4/retail_gpt5.4_noise_type_misleading.yaml
src/env/config/runs/retail/gpt-5.4-mini/retail_gpt5.4_mini_default.yaml
src/env/config/runs/retail/llama3.1-8b-local/retail_llama3_1_8b_local_default.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_blocker.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_default.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_feedback.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_finegrain_long.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_finegrain_short.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_noise_ratio_0p2.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_noise_ratio_0p4.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_noise_ratio_0p6.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_noise_ratio_0p8.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_noise_type_explicit.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_noise_type_implicit.yaml
src/env/config/runs/retail/llama3.3-70b-local/retail_llama3_3_70b_local_noise_type_misleading.yaml
src/env/config/runs/retail/qwen3-14b-local/retail_qwen3_14b_local_default.yaml
src/env/config/runs/retail/qwen3-32b-local/retail_qwen3_32b_local_default.yaml
src/env/config/runs/retail/qwen3-8b-local/retail_qwen3_8b_local_default.yaml
src/env/core/__init__.py
src/env/core/answer_judges.py
src/env/core/config.py
src/env/core/sampling.py
src/env/core/types.py
src/env/core/utils.py
src/env/domains/__init__.py
src/env/domains/executor.py
src/env/evaluate.py
src/env/events/__init__.py
src/env/events/blocker.py
src/env/events/controller.py
src/env/events/noisy.py
src/env/prompt/domain_context_retail.txt
src/env/prompt/error_call_blocked.txt
src/env/prompt/error_call_json_format.txt
src/env/prompt/error_call_missing_inputs.txt
src/env/prompt/error_call_tool_not_available.txt
src/env/prompt/error_call_wrong_inputs.txt
src/env/prompt/error_label_format.txt
src/env/prompt/error_retrieve_json_format.txt
src/env/prompt/error_retrieve_semantic.txt
src/env/prompt/system_runtime_prompt.txt
src/env/retriever/__init__.py
src/env/retriever/hierarchical.py
src/env/retriever/schema.py
src/env/retriever/semantic.py
src/env/run.py
src/env/runtime/__init__.py
src/env/runtime/llm.py
src/env/runtime/parsing.py
src/env/runtime/prompts.py
src/env/runtime/runner.py
```

## Detected entry points

- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/run.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/evaluate.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/scripts/run_retail_batch.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/core/answer_judges.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/core/config.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/core/sampling.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/core/types.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/core/utils.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/domains/executor.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/events/blocker.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/events/controller.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/events/noisy.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/retriever/hierarchical.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/retriever/schema.py`
- `projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/external/PlanBench-XL/src/env/retriever/semantic.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `PlanBench-XL` — not re-implementing it.
