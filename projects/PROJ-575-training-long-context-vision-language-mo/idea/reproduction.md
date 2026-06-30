# Reproduce & validate: Training Long-Context Vision-Language Models Effectively with Generalization Beyond 128K Context

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/   (clone of https://github.com/EdinburghNLP/MMLongBench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Training Long-Context Vision-Language Models Effectively with Generalization Beyond 128K Context

**Abstract:** Long-context modeling is becoming a core capability of modern large vision-language models (LVLMs), enabling sustained context management across long-document understanding, video analysis, and multi-turn tool use in agentic workflows. Yet practical training recipes remain insufficiently explored, particularly for designing and balancing long-context data mixtures. In this work, we present a systematic study of long-context continued pre-training for LVLMs, extending a 7B model from 32K to 128K context with extensive ablations on long-document data. We first show that long-document VQA is substantially more effective than OCR transcription. Building on this observation, our ablations further yield three key findings: i) for sequence-length distribution, balanced data outperforms target-length-focused data (e.g., 128K), suggesting that long-context ability requires generalizable key-information retrieval across various lengths and positions; ii) retrieval remains the primary bottleneck, favoring retrieval-heavy mixtures with modest reasoning data for task diversity; and iii) pure long-document VQA largely preserves short-context capabilities, suggesting that instruction-formatted long data reduces the need for short-data mixing. Based on these findings, we introduce MMProLong, obtained by long-context continued pre-training from Qwen2.5-VL-7B with only a 5B-token budget. MMProLong improves long-document VQA scores by 7.1% and maintains strong performance at 256K and 512K contexts beyond its 128K training window, without additional training. It further generalizes to webpage-based multimodal needle retrieval, long-context vision-text compression, and long-video understanding without task-specific supervision. Overall, our study establishes a practical LongPT recipe and an empirical foundation for advancing long-context vision-language models.

## Shipped code — file tree (`projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/`)

```
.gitignore
LICENSE.txt
README.md
arguments.py
assets/comparison_page.jpg
assets/overview_page.jpg
configs/docqa_all.yaml
configs/icl_all.yaml
configs/mm_niah_image_all.yaml
configs/mm_niah_text_all.yaml
configs/summ_all.yaml
configs/text_docqa_all.yaml
configs/text_rag_all.yaml
configs/vh_all.yaml
configs/vrag_all.yaml
data.py
eval.py
eval_api.py
eval_api_batch.py
figure_scripts/10_plot_NIAH_distribution.py
figure_scripts/11_task_diffculty.py
figure_scripts/12_metrics_for_summ.py
figure_scripts/13_vh_difficulty.py
figure_scripts/13_vh_multi_difficulty.py
figure_scripts/14_needle_modal_difficulty.py
figure_scripts/15_docqa_modal_difficulty.py
figure_scripts/15_rag_modal_difficulty.py
figure_scripts/16_docqa_pie_figure.py
figure_scripts/18_internvl2_V2PE.py
figure_scripts/18_qwen2_5_yarn.py
figure_scripts/1_main_most_models.py
figure_scripts/2_main_full_models.py
figure_scripts/3_main_full_models_by_category.py
figure_scripts/4_main_full_models_split.py
figure_scripts/5_correlation_NIAH_most.py
figure_scripts/6_correlation_NIAH_all.py
figure_scripts/7_correlation_all_categories.py
figure_scripts/8_correlation_all_datasets.py
figure_scripts/9_heatmap_by_depth.py
figure_scripts/t1_check_image_number.py
figure_scripts/utils.py
requirements.txt
scripts/check_missing.py
scripts/download_image_data.sh
scripts/download_text_data.sh
scripts/eval_gpt4_summ.py
scripts/eval_gpt4_summ.sh
scripts/eval_task_manager.py
scripts/generate_configs.py
scripts/run_analysis.sh
scripts/run_api.sh
scripts/run_eval.sh
utils.py
utils_prompt.py
uv.lock
vlm_model/__init__.py
vlm_model/deepseek_vl2.py
vlm_model/gemini.py
vlm_model/gemma3.py
vlm_model/idefics.py
vlm_model/internv2pe.py
vlm_model/internvl.py
vlm_model/internvl_v2pe/__init__.py
vlm_model/internvl_v2pe/internvl/__init__.py
vlm_model/internvl_v2pe/internvl/conversation.py
vlm_model/internvl_v2pe/internvl/dist_utils.py
vlm_model/internvl_v2pe/internvl/model/__init__.py
vlm_model/internvl_v2pe/internvl/model/internlm2/configuration_internlm2.py
vlm_model/internvl_v2pe/internvl/model/internlm2/modeling_internlm2.py
vlm_model/internvl_v2pe/internvl/model/internlm2/tokenization_internlm2.py
vlm_model/internvl_v2pe/internvl/model/internlm2/tokenization_internlm2_fast.py
vlm_model/internvl_v2pe/internvl/model/internvl_chat/__init__.py
vlm_model/internvl_v2pe/internvl/model/internvl_chat/configuration_intern_vit.py
vlm_model/internvl_v2pe/internvl/model/internvl_chat/configuration_internvl_chat.py
vlm_model/internvl_v2pe/internvl/model/internvl_chat/flash_attention.py
vlm_model/internvl_v2pe/internvl/model/internvl_chat/modeling_intern_vit.py
vlm_model/internvl_v2pe/internvl/model/internvl_chat/modeling_internvl_chat.py
vlm_model/internvl_v2pe/internvl/patch/__init__.py
vlm_model/internvl_v2pe/internvl/patch/internlm2_packed_training_patch.py
vlm_model/internvl_v2pe/internvl/patch/llama2_flash_attn_monkey_patch.py
vlm_model/internvl_v2pe/internvl/patch/llama_flash_attn_monkey_patch.py
vlm_model/internvl_v2pe/internvl/patch/llama_packed_training_patch.py
vlm_model/internvl_v2pe/internvl/patch/llama_rmsnorm_monkey_patch.py
vlm_model/internvl_v2pe/internvl/patch/pad_data_collator.py
vlm_model/internvl_v2pe/internvl/patch/qwen2_packed_training_patch.py
vlm_model/internvl_v2pe/internvl/patch/train_dataloader_patch.py
vlm_model/internvl_v2pe/internvl/patch/train_sampler_patch.py
vlm_model/internvl_v2pe/internvl/serve/__init__.py
vlm_model/internvl_v2pe/internvl/serve/constants.py
vlm_model/internvl_v2pe/internvl/serve/mm_utils.py
vlm_model/internvl_v2pe/internvl/serve/model_worker.py
vlm_model/internvl_v2pe/internvl/serve/utils.py
vlm_model/internvl_v2pe/internvl/train/__init__.py
vlm_model/internvl_v2pe/internvl/train/compress_seq_trainer.py
vlm_model/internvl_v2pe/internvl/train/constants.py
vlm_model/internvl_v2pe/internvl/train/dataset.py
vlm_model/internvl_v2pe/internvl/train/dataset_packed.py
vlm_model/internvl_v2pe/internvl/train/internvl_chat_finetune.py
vlm_model/internvl_v2pe/internvl/train/trainer_monkey_patch.py
vlm_model/llava_onevision.py
vlm_model/minicpm.py
vlm_model/mllama.py
vlm_model/model_utils.py
vlm_model/mplug_owl3.py
vlm_model/nvila.py
vlm_model/nvila_2b_ef8fa9c8/__init__.py
vlm_model/nvila_2b_ef8fa9c8/auto_processor.py
vlm_model/nvila_2b_ef8fa9c8/base_projector.py
vlm_model/nvila_2b_ef8fa9c8/builder.py
vlm_model/nvila_2b_ef8fa9c8/configuration_vila.py
vlm_model/nvila_2b_ef8fa9c8/constants.py
vlm_model/nvila_2b_ef8fa9c8/conversation.py
vlm_model/nvila_2b_ef8fa9c8/distributed.py
vlm_model/nvila_2b_ef8fa9c8/loss.py
vlm_model/nvila_2b_ef8fa9c8/media.py
vlm_model/nvila_2b_ef8fa9c8/media_encoder.py
vlm_model/nvila_2b_ef8fa9c8/mm_utils.py
vlm_model/nvila_2b_ef8fa9c8/model_utils_packing.py
vlm_model/nvila_2b_ef8fa9c8/modeling_vila.py
vlm_model/nvila_2b_ef8fa9c8/siglip_encoder.py
vlm_model/nvila_2b_ef8fa9c8/tokenizer_utils.py
vlm_model/nvila_2b_ef8fa9c8/utils.py
vlm_model/nvila_8b_e2481b0c/__init__.py
vlm_model/nvila_8b_e2481b0c/auto_processor.py
vlm_model/nvila_8b_e2481b0c/base_projector.py
vlm_model/nvila_8b_e2481b0c/builder.py
vlm_model/nvila_8b_e2481b0c/configuration_vila.py
vlm_model/nvila_8b_e2481b0c/constants.py
vlm_model/nvila_8b_e2481b0c/conversation.py
vlm_model/nvila_8b_e2481b0c/distributed.py
vlm_model/nvila_8b_e2481b0c/loss.py
vlm_model/nvila_8b_e2481b0c/media.py
vlm_model/nvila_8b_e2481b0c/media_encoder.py
vlm_model/nvila_8b_e2481b0c/mm_utils.py
vlm_model/nvila_8b_e2481b0c/model_utils_packing.py
vlm_model/nvila_8b_e2481b0c/modeling_vila.py
vlm_model/nvila_8b_e2481b0c/siglip_encoder.py
vlm_model/nvila_8b_e2481b0c/tokenizer_utils.py
vlm_model/nvila_8b_e2481b0c/utils.py
vlm_model/openai_model.py
vlm_model/ovis2.py
vlm_model/phi3.py
vlm_model/phi4.py
vlm_model/pixtral.py
vlm_model/qwen2_vl.py
vlm_model/qwen2_with_prefill/__init__.py
vlm_model/qwen2_with_prefill/qwen2_5vl.py
vlm_model/qwen2_with_prefill/qwen2vl.py
vlm_model/qwen_vl.py
vlm_model/text_only_model.py
vlm_model/vllm_models.py
```

## Detected entry points

- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/eval.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/arguments.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/data.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/eval_api.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/eval_api_batch.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/utils.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/utils_prompt.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/figure_scripts/10_plot_NIAH_distribution.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/figure_scripts/11_task_diffculty.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/figure_scripts/12_metrics_for_summ.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/figure_scripts/13_vh_difficulty.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/figure_scripts/13_vh_multi_difficulty.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/figure_scripts/14_needle_modal_difficulty.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/figure_scripts/15_docqa_modal_difficulty.py`
- `projects/PROJ-575-training-long-context-vision-language-mo/external/MMLongBench/figure_scripts/15_rag_modal_difficulty.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `MMLongBench` — not re-implementing it.
