# Reproduce & validate: Improved Large Language Diffusion Models

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/   (clone of https://github.com/ML-GSAI/LLaDA)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Improved Large Language Diffusion Models

**Abstract:** Modern large language models are predominantly trained with autoregressive factorization and causal attention. We present \emph{iLLaDA}, an 8B masked diffusion language model trained from scratch with fully bidirectional attention. iLLaDA keeps the masked diffusion objective throughout pre-training and supervised fine-tuning (SFT), scaling pre-training to 12T tokens and fine-tuning on a 25B-token instruction corpus for 12 epochs. We further use variable-length generation for efficiency and introduce confidence-based scoring for multiple-choice evaluation. Compared with LLaDA, iLLaDA improves broadly across general, mathematical, and code benchmarks; for example, iLLaDA-Base improves by 21.6 points on BBH and 14.9 points on ARC-Challenge, while iLLaDA-Instruct improves by 14.5 points on MATH and 16.5 points on HumanEval. Despite its non-autoregressive training, iLLaDA also remains competitive with Qwen2.5 7B on several benchmarks. These results show that fully bidirectional diffusion training from scratch is a competitive path toward strong language models. Model weights and codes: https://github.com/ML-GSAI/LLaDA.

## Shipped code — file tree (`projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/`)

```
EVAL.md
GUIDELINES.md
README.md
app.py
chat.py
data/poem_data.json
eval_llada.py
eval_llada_lm_eval.sh
eval_llada_opencompass.sh
eval_reverse.py
generate.py
get_log_likelihood.py
imgs/LLaDA_vs_LLaMA.svg
imgs/LLaDA_vs_LLaMA_chat.svg
imgs/diff_remask.gif
imgs/example_gradio.gif
imgs/sample.png
imgs/transformer1.png
imgs/transformer2.png
opencompass/.codespellrc
opencompass/.gitignore
opencompass/.owners.yml
opencompass/.pre-commit-config-zh-cn.yaml
opencompass/.pre-commit-config.yaml
opencompass/LICENSE
opencompass/MANIFEST.in
opencompass/dataset-index.yml
opencompass/docs/en/.readthedocs.yaml
opencompass/docs/en/Makefile
opencompass/docs/en/_static/css/readthedocs.css
opencompass/docs/en/_static/image/logo.svg
opencompass/docs/en/_static/image/logo_icon.svg
opencompass/docs/en/_static/js/custom.js
opencompass/docs/en/_templates/404.html
opencompass/docs/en/_templates/autosummary/class.rst
opencompass/docs/en/_templates/callable.rst
opencompass/docs/en/advanced_guides/accelerator_intro.md
opencompass/docs/en/advanced_guides/circular_eval.md
opencompass/docs/en/advanced_guides/code_eval.md
opencompass/docs/en/advanced_guides/code_eval_service.md
opencompass/docs/en/advanced_guides/contamination_eval.md
opencompass/docs/en/advanced_guides/custom_dataset.md
opencompass/docs/en/advanced_guides/evaluation_lightllm.md
opencompass/docs/en/advanced_guides/evaluation_lmdeploy.md
opencompass/docs/en/advanced_guides/llm_judge.md
opencompass/docs/en/advanced_guides/longeval.md
opencompass/docs/en/advanced_guides/math_verify.md
opencompass/docs/en/advanced_guides/needleinahaystack_eval.md
opencompass/docs/en/advanced_guides/new_dataset.md
opencompass/docs/en/advanced_guides/new_model.md
opencompass/docs/en/advanced_guides/objective_judgelm_evaluation.md
opencompass/docs/en/advanced_guides/persistence.md
opencompass/docs/en/advanced_guides/prompt_attack.md
opencompass/docs/en/advanced_guides/subjective_evaluation.md
opencompass/docs/en/conf.py
opencompass/docs/en/docutils.conf
opencompass/docs/en/get_started/faq.md
opencompass/docs/en/get_started/installation.md
opencompass/docs/en/get_started/quick_start.md
opencompass/docs/en/index.rst
opencompass/docs/en/notes/academic.md
opencompass/docs/en/notes/contribution_guide.md
opencompass/docs/en/notes/news.md
opencompass/docs/en/prompt/chain_of_thought.md
opencompass/docs/en/prompt/meta_template.md
opencompass/docs/en/prompt/overview.md
opencompass/docs/en/prompt/prompt_template.md
opencompass/docs/en/statis.py
opencompass/docs/en/tools.md
opencompass/docs/en/user_guides/config.md
opencompass/docs/en/user_guides/corebench.md
opencompass/docs/en/user_guides/datasets.md
opencompass/docs/en/user_guides/deepseek_r1.md
opencompass/docs/en/user_guides/evaluation.md
opencompass/docs/en/user_guides/experimentation.md
opencompass/docs/en/user_guides/framework_overview.md
opencompass/docs/en/user_guides/metrics.md
opencompass/docs/en/user_guides/models.md
opencompass/docs/en/user_guides/summarizer.md
opencompass/docs/zh_cn/.readthedocs.yaml
opencompass/docs/zh_cn/Makefile
opencompass/docs/zh_cn/_static/css/readthedocs.css
opencompass/docs/zh_cn/_static/image/logo.svg
opencompass/docs/zh_cn/_static/image/logo_icon.svg
opencompass/docs/zh_cn/_static/js/custom.js
opencompass/docs/zh_cn/_templates/404.html
opencompass/docs/zh_cn/_templates/autosummary/class.rst
opencompass/docs/zh_cn/_templates/callable.rst
opencompass/docs/zh_cn/advanced_guides/accelerator_intro.md
opencompass/docs/zh_cn/advanced_guides/circular_eval.md
opencompass/docs/zh_cn/advanced_guides/code_eval.md
opencompass/docs/zh_cn/advanced_guides/code_eval_service.md
opencompass/docs/zh_cn/advanced_guides/compassbench_intro.md
opencompass/docs/zh_cn/advanced_guides/compassbench_v2_0.md
opencompass/docs/zh_cn/advanced_guides/contamination_eval.md
opencompass/docs/zh_cn/advanced_guides/custom_dataset.md
opencompass/docs/zh_cn/advanced_guides/evaluation_lightllm.md
opencompass/docs/zh_cn/advanced_guides/evaluation_lmdeploy.md
opencompass/docs/zh_cn/advanced_guides/llm_judge.md
opencompass/docs/zh_cn/advanced_guides/longeval.md
opencompass/docs/zh_cn/advanced_guides/math_verify.md
opencompass/docs/zh_cn/advanced_guides/needleinahaystack_eval.md
opencompass/docs/zh_cn/advanced_guides/new_dataset.md
opencompass/docs/zh_cn/advanced_guides/new_model.md
opencompass/docs/zh_cn/advanced_guides/objective_judgelm_evaluation.md
opencompass/docs/zh_cn/advanced_guides/persistence.md
opencompass/docs/zh_cn/advanced_guides/prompt_attack.md
opencompass/docs/zh_cn/advanced_guides/subjective_evaluation.md
opencompass/docs/zh_cn/conf.py
opencompass/docs/zh_cn/cp_origin_docs.sh
opencompass/docs/zh_cn/docutils.conf
opencompass/docs/zh_cn/get_started/faq.md
opencompass/docs/zh_cn/get_started/installation.md
opencompass/docs/zh_cn/get_started/quick_start.md
opencompass/docs/zh_cn/index.rst
opencompass/docs/zh_cn/notes/academic.md
opencompass/docs/zh_cn/notes/contribution_guide.md
opencompass/docs/zh_cn/notes/news.md
opencompass/docs/zh_cn/prompt/chain_of_thought.md
opencompass/docs/zh_cn/prompt/meta_template.md
opencompass/docs/zh_cn/prompt/overview.md
opencompass/docs/zh_cn/prompt/prompt_template.md
opencompass/docs/zh_cn/statis.py
opencompass/docs/zh_cn/tools.md
opencompass/docs/zh_cn/user_guides/config.md
opencompass/docs/zh_cn/user_guides/corebench.md
opencompass/docs/zh_cn/user_guides/datasets.md
opencompass/docs/zh_cn/user_guides/deepseek_r1.md
opencompass/docs/zh_cn/user_guides/evaluation.md
opencompass/docs/zh_cn/user_guides/experimentation.md
opencompass/docs/zh_cn/user_guides/framework_overview.md
opencompass/docs/zh_cn/user_guides/metrics.md
opencompass/docs/zh_cn/user_guides/models.md
opencompass/docs/zh_cn/user_guides/summarizer.md
opencompass/examples/llada_1p5_gen_gpqa_length256_block16.py
opencompass/examples/llada_1p5_gen_gsm8k_length256_block16_confidence.py
opencompass/examples/llada_1p5_gen_humaneval_length512_block32_confidence.py
opencompass/examples/llada_1p5_gen_ifeval_length256_block16_confidence.py
opencompass/examples/llada_1p5_gen_math_length1024_block128_confidence.py
opencompass/examples/llada_1p5_gen_mbpp_length512_block32_confidence.py
opencompass/examples/llada_base_gen_bbh_length256_block256.py
opencompass/examples/llada_base_gen_gsm8k_length256_block256.py
opencompass/examples/llada_base_gen_humaneval_length256_block256.py
opencompass/examples/llada_base_gen_math_length256_block256.py
opencompass/examples/llada_base_gen_mbpp_length256_block256.py
opencompass/examples/llada_instruct_gen_arcc_length512_block512.py
opencompass/examples/llada_instruct_gen_gpqa_length128_block64.py
opencompass/examples/llada_instruct_gen_gpqa_length64_block64_confidence.py
opencompass/examples/llada_instruct_gen_gsm8k_length256_block8.py
opencompass/examples/llada_instruct_gen_gsm8k_length512_block512_confidence.py
opencompass/examples/llada_instruct_gen_hellaswag_length3_block3.py
opencompass/examples/llada_instruct_gen_humaneval_length512_block32.py
opencompass/examples/llada_instruct_gen_humaneval_length512_block512_logits.py
opencompass/examples/llada_instruct_gen_ifeval_length512_block512_confidence.py
opencompass/examples/llada_instruct_gen_math_length256_block256.py
opencompass/examples/llada_instruct_gen_math_length512_block512_confidence.py
opencompass/examples/llada_instruct_gen_math_length512_block64.py
opencompass/examples/llada_instruct_gen_mbpp_length256_block256_confidence.py
opencompass/examples/llada_instruct_gen_mbpp_length512_block32.py
opencompass/examples/llada_instruct_gen_mmlu_length3_block3.py
opencompass/examples/llada_instruct_gen_mmlupro_length256_block256.py
opencompass/opencompass/__init__.py
opencompass/opencompass/cli/__init__.py
opencompass/opencompass/cli/main.py
opencompass/opencompass/configs/dataset_collections/chat_OC15.py
opencompass/opencompass/configs/datasets/ARC_c/ARC_c_clean_ppl.py
opencompass/opencompass/configs/datasets/ARC_c/ARC_c_cot_gen_926652.py
opencompass/opencompass/configs/datasets/ARC_c/ARC_c_few_shot_gen_e9b043.py
opencompass/opencompass/configs/datasets/ARC_c/ARC_c_few_shot_ppl.py
opencompass/opencompass/configs/datasets/ARC_c/ARC_c_gen.py
opencompass/opencompass/configs/datasets/ARC_c/ARC_c_gen_1e0de5.py
opencompass/opencompass/configs/datasets/ARC_c/ARC_c_ppl.py
opencompass/opencompass/configs/datasets/ARC_c/ARC_c_ppl_2ef631.py
opencompass/opencompass/configs/datasets/ARC_c/ARC_c_ppl_a450bd.py
opencompass/opencompass/configs/datasets/ARC_c/ARC_c_ppl_d52a21.py
opencompass/opencompass/configs/datasets/IFEval/IFEval.md
opencompass/opencompass/configs/datasets/IFEval/IFEval_gen.py
opencompass/opencompass/configs/datasets/IFEval/IFEval_gen_3321a3.py
opencompass/opencompass/configs/datasets/IFEval/IFEval_gen_353ae7.py
opencompass/opencompass/configs/datasets/IFEval/README.md
opencompass/opencompass/configs/datasets/bbh/README.md
opencompass/opencompass/configs/datasets/bbh/bbh_0shot_nocot_academic_gen.py
opencompass/opencompass/configs/datasets/bbh/bbh_0shot_nocot_gen_925fc4.py
opencompass/opencompass/configs/datasets/bbh/bbh_0shot_nocot_gen_9c32f6.py
opencompass/opencompass/configs/datasets/bbh/bbh_0shot_nocot_gen_ea7952.py
opencompass/opencompass/configs/datasets/bbh/bbh_3shot_gen.py
opencompass/opencompass/configs/datasets/bbh/bbh_gen.py
opencompass/opencompass/configs/datasets/bbh/bbh_gen_2879b0.py
opencompass/opencompass/configs/datasets/bbh/bbh_gen_4a31fa.py
opencompass/opencompass/configs/datasets/bbh/bbh_gen_5b92b0.py
opencompass/opencompass/configs/datasets/bbh/bbh_gen_5bf00b.py
opencompass/opencompass/configs/datasets/bbh/bbh_gen_98fba6.py
opencompass/opencompass/configs/datasets/bbh/bbh_gen_ee62e9.py
opencompass/opencompass/configs/datasets/bbh/bbh_llm_judge_gen.py
opencompass/opencompass/configs/datasets/bbh/bbh_llmjudge_gen_b5bdf1.py
opencompass/opencompass/configs/datasets/bbh/bbh_subset_settings.py
opencompass/opencompass/configs/datasets/bbh/lib_prompt/boolean_expressions.txt
opencompass/opencompass/configs/datasets/bbh/lib_prompt/causal_judgement.txt
opencompass/opencompass/configs/datasets/bbh/lib_prompt/date_understanding.txt
opencompass/opencompass/configs/datasets/bbh/lib_prompt/disambiguation_qa.txt
… (truncated)
```

## Detected entry points

- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/opencompass/opencompass/cli/main.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/opencompass/opencompass/datasets/TheoremQA/main.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/opencompass/run.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/opencompass/opencompass/utils/run.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/app.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/chat.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/eval_llada.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/eval_reverse.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/generate.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/get_log_likelihood.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/visualization/generate.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/visualization/html_to_png.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/visualization/visualization_paper.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/visualization/visualization_zhihu.py`
- `projects/PROJ-788-improved-large-language-diffusion-models/external/LLaDA/opencompass/examples/llada_1p5_gen_gpqa_length256_block16.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `LLaDA` — not re-implementing it.
