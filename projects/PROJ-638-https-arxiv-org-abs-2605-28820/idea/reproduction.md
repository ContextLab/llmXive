# Reproduce & validate: From Pixels to Words -- Towards Native One-Vision Models at Scale

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/   (clone of https://github.com/EvolvingLMMs-Lab/NEO)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** From Pixels to Words -- Towards Native One-Vision Models at Scale

**Abstract:** Current vision-language models (VLMs) typically stitch together separate image encoders and language decoders via multi-stage alignment, a modular framework that inevitably fragments pixel-level signals across frames and scatters early pixel-word interactions. In parallel, native VLMs, despite impressive performance on single images, remain largely unexplored in multi-image, video understanding, and spatial intelligence. Hence, we introduce NEO-ov, a native foundation model that learns cross-frame and pixel-word correspondence end-to-end, without any external encoders, auxiliary adapters, or post-hoc fusion. By eliminating module boundaries entirely, NEO-ov enables fine-grained and unified spatiotemporal modeling to emerge natively inside the model. Notably, NEO-ov largely narrows the gap to modular counterparts while excelling at fine-grained visual perception, validating that native "one-vision" architectures are not only feasible but competitive at scale. Beyond empirical performance, we unveil systematic architectural analyses and detailed training recipes to facilitate subsequent native multimodal modeling. Our code and models are publicly available at: https://github.com/EvolvingLMMs-Lab/NEO.

## Shipped code — file tree (`projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/`)

```
LICENSE
README.md
VLMEvalKit/.gitignore
VLMEvalKit/.pre-commit-config.yaml
VLMEvalKit/LICENSE
VLMEvalKit/README.md
VLMEvalKit/assets/LOGO.svg
VLMEvalKit/docs/en/.readthedocs.yaml
VLMEvalKit/docs/en/ConfigSystem.md
VLMEvalKit/docs/en/Contributors.md
VLMEvalKit/docs/en/Development.md
VLMEvalKit/docs/en/EvalByLMDeploy.md
VLMEvalKit/docs/en/Makefile
VLMEvalKit/docs/en/Quickstart.md
VLMEvalKit/docs/en/_static/css/readthedocs.css
VLMEvalKit/docs/en/_static/image/logo.svg
VLMEvalKit/docs/en/_static/image/logo_icon.svg
VLMEvalKit/docs/en/_static/js/custom.js
VLMEvalKit/docs/en/_templates/404.html
VLMEvalKit/docs/en/_templates/autosummary/class.rst
VLMEvalKit/docs/en/_templates/callable.rst
VLMEvalKit/docs/en/conf.py
VLMEvalKit/docs/en/docutils.conf
VLMEvalKit/docs/en/index.rst
VLMEvalKit/docs/zh-CN/.readthedocs.yaml
VLMEvalKit/docs/zh-CN/ConfigSystem.md
VLMEvalKit/docs/zh-CN/Development.md
VLMEvalKit/docs/zh-CN/EvalByLMDeploy.md
VLMEvalKit/docs/zh-CN/Makefile
VLMEvalKit/docs/zh-CN/Quickstart.md
VLMEvalKit/docs/zh-CN/README_zh-CN.md
VLMEvalKit/docs/zh-CN/_static/css/readthedocs.css
VLMEvalKit/docs/zh-CN/_static/image/logo.svg
VLMEvalKit/docs/zh-CN/_static/image/logo_icon.svg
VLMEvalKit/docs/zh-CN/_static/js/custom.js
VLMEvalKit/docs/zh-CN/_templates/404.html
VLMEvalKit/docs/zh-CN/_templates/autosummary/class.rst
VLMEvalKit/docs/zh-CN/_templates/callable.rst
VLMEvalKit/docs/zh-CN/conf.py
VLMEvalKit/docs/zh-CN/cp_origin_docs.sh
VLMEvalKit/docs/zh-CN/docutils.conf
VLMEvalKit/docs/zh-CN/index.rst
VLMEvalKit/requirements/docs.txt
VLMEvalKit/requirements.txt
VLMEvalKit/run.py
VLMEvalKit/scripts/AI2D_preproc.ipynb
VLMEvalKit/scripts/apires_scan.py
VLMEvalKit/scripts/auto_run.py
VLMEvalKit/scripts/cover.sh
VLMEvalKit/scripts/data_browser.py
VLMEvalKit/scripts/srun.sh
VLMEvalKit/scripts/summarize.py
VLMEvalKit/scripts/visualize.ipynb
VLMEvalKit/setup.py
VLMEvalKit/tests/__init__.py
VLMEvalKit/tests/test_minimax_provider.py
VLMEvalKit/vlmeval/__init__.py
VLMEvalKit/vlmeval/api/__init__.py
VLMEvalKit/vlmeval/api/base.py
VLMEvalKit/vlmeval/api/claude.py
VLMEvalKit/vlmeval/api/cloudwalk.py
VLMEvalKit/vlmeval/api/doubao_vl_api.py
VLMEvalKit/vlmeval/api/glm_vision.py
VLMEvalKit/vlmeval/api/gpt.py
VLMEvalKit/vlmeval/api/hf_chat_model.py
VLMEvalKit/vlmeval/api/hunyuan.py
VLMEvalKit/vlmeval/api/jt_vl_chat.py
VLMEvalKit/vlmeval/api/kimivl_api.py
VLMEvalKit/vlmeval/api/lmdeploy.py
VLMEvalKit/vlmeval/api/mug_u.py
VLMEvalKit/vlmeval/api/siliconflow.py
VLMEvalKit/vlmeval/api/taichu.py
VLMEvalKit/vlmeval/api/taiyi.py
VLMEvalKit/vlmeval/config.py
VLMEvalKit/vlmeval/dataset/CGAVCounting/__init__.py
VLMEvalKit/vlmeval/dataset/CGAVCounting/cg_av_counting.py
VLMEvalKit/vlmeval/dataset/CGAVCounting/requirements.txt
VLMEvalKit/vlmeval/dataset/CGAVCounting/utils.py
VLMEvalKit/vlmeval/dataset/EgoExoBench/README.md
VLMEvalKit/vlmeval/dataset/EgoExoBench/__init__.py
VLMEvalKit/vlmeval/dataset/EgoExoBench/cvmhat_preprocess.py
VLMEvalKit/vlmeval/dataset/EgoExoBench/egoexobench.py
VLMEvalKit/vlmeval/dataset/EgoExoBench/tf2023_preprocess.py
VLMEvalKit/vlmeval/dataset/EgoExoBench/utils.py
VLMEvalKit/vlmeval/dataset/GUI/__init__.py
VLMEvalKit/vlmeval/dataset/GUI/screenspot.py
VLMEvalKit/vlmeval/dataset/GUI/screenspot_pro.py
VLMEvalKit/vlmeval/dataset/GUI/screenspot_v2.py
VLMEvalKit/vlmeval/dataset/OmniDocBench/__init__.py
VLMEvalKit/vlmeval/dataset/OmniDocBench/data_preprocess.py
VLMEvalKit/vlmeval/dataset/OmniDocBench/metrics.py
VLMEvalKit/vlmeval/dataset/OmniDocBench/omnidocbench.py
VLMEvalKit/vlmeval/dataset/OmniDocBench/requirements.txt
VLMEvalKit/vlmeval/dataset/OmniDocBench/utils.py
VLMEvalKit/vlmeval/dataset/__init__.py
VLMEvalKit/vlmeval/dataset/cgbench.py
VLMEvalKit/vlmeval/dataset/chartmimic.py
VLMEvalKit/vlmeval/dataset/charxiv.py
VLMEvalKit/vlmeval/dataset/cmmmu.py
VLMEvalKit/vlmeval/dataset/creation.py
VLMEvalKit/vlmeval/dataset/dude.py
VLMEvalKit/vlmeval/dataset/dynamath.py
VLMEvalKit/vlmeval/dataset/emma.py
VLMEvalKit/vlmeval/dataset/gobench.py
VLMEvalKit/vlmeval/dataset/image_base.py
VLMEvalKit/vlmeval/dataset/image_caption.py
VLMEvalKit/vlmeval/dataset/image_ccocr.py
VLMEvalKit/vlmeval/dataset/image_mcq.py
VLMEvalKit/vlmeval/dataset/image_mt.py
VLMEvalKit/vlmeval/dataset/image_shortqa.py
VLMEvalKit/vlmeval/dataset/image_vqa.py
VLMEvalKit/vlmeval/dataset/image_yorn.py
VLMEvalKit/vlmeval/dataset/longvideobench.py
VLMEvalKit/vlmeval/dataset/m4bench.py
VLMEvalKit/vlmeval/dataset/megabench.py
VLMEvalKit/vlmeval/dataset/miabench.py
VLMEvalKit/vlmeval/dataset/mlvu.py
VLMEvalKit/vlmeval/dataset/mmalignbench.py
VLMEvalKit/vlmeval/dataset/mmbench_video.py
VLMEvalKit/vlmeval/dataset/mmgenbench.py
VLMEvalKit/vlmeval/dataset/mmifeval.py
VLMEvalKit/vlmeval/dataset/mmlongbench.py
VLMEvalKit/vlmeval/dataset/mmmath.py
VLMEvalKit/vlmeval/dataset/moat.py
VLMEvalKit/vlmeval/dataset/moviechat1k.py
VLMEvalKit/vlmeval/dataset/mvbench.py
VLMEvalKit/vlmeval/dataset/ost_bench.py
VLMEvalKit/vlmeval/dataset/qbench_video.py
VLMEvalKit/vlmeval/dataset/sfebench.py
VLMEvalKit/vlmeval/dataset/slidevqa.py
VLMEvalKit/vlmeval/dataset/spatial457.py
VLMEvalKit/vlmeval/dataset/tamperbench.py
VLMEvalKit/vlmeval/dataset/tempcompass.py
VLMEvalKit/vlmeval/dataset/text_base.py
VLMEvalKit/vlmeval/dataset/text_mcq.py
VLMEvalKit/vlmeval/dataset/utils/Ocrbench_v2/IoUscore_metric.py
VLMEvalKit/vlmeval/dataset/utils/Ocrbench_v2/TEDS_metric.py
VLMEvalKit/vlmeval/dataset/utils/Ocrbench_v2/page_ocr_metric.py
VLMEvalKit/vlmeval/dataset/utils/Ocrbench_v2/parallel.py
VLMEvalKit/vlmeval/dataset/utils/Ocrbench_v2/requirements.txt
VLMEvalKit/vlmeval/dataset/utils/Ocrbench_v2/spotting_eval/rrc_evaluation_funcs_1_1.py
VLMEvalKit/vlmeval/dataset/utils/Ocrbench_v2/spotting_metric.py
VLMEvalKit/vlmeval/dataset/utils/Ocrbench_v2/vqa_metric.py
VLMEvalKit/vlmeval/dataset/utils/__init__.py
VLMEvalKit/vlmeval/dataset/utils/ayavision.py
VLMEvalKit/vlmeval/dataset/utils/bmmr.py
VLMEvalKit/vlmeval/dataset/utils/bmmr_grade.py
VLMEvalKit/vlmeval/dataset/utils/ccocr_evaluator/README.md
VLMEvalKit/vlmeval/dataset/utils/ccocr_evaluator/__init__.py
VLMEvalKit/vlmeval/dataset/utils/ccocr_evaluator/common.py
VLMEvalKit/vlmeval/dataset/utils/ccocr_evaluator/doc_parsing_evaluator.py
VLMEvalKit/vlmeval/dataset/utils/ccocr_evaluator/kie_evaluator.py
VLMEvalKit/vlmeval/dataset/utils/ccocr_evaluator/ocr_evaluator.py
VLMEvalKit/vlmeval/dataset/utils/cgbench.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/__init__.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/eval_configs/__init__.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/eval_configs/global_config.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/eval_req.txt
VLMEvalKit/vlmeval/dataset/utils/chartmimic/evaluator/__init__.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/evaluator/chart_type_and_color.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/evaluator/chart_type_evaluator.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/evaluator/chart_type_evaluator_prefix.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/evaluator/color_evaluator.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/evaluator/color_evaluator_prefix.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/evaluator/color_utils.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/evaluator/grid_evaluator.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/evaluator/layout_evaluator.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/evaluator/legend_evaluator.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/evaluator/text_evaluator.py
VLMEvalKit/vlmeval/dataset/utils/chartmimic/mp_util.py
VLMEvalKit/vlmeval/dataset/utils/crpe.py
VLMEvalKit/vlmeval/dataset/utils/hrbench.py
VLMEvalKit/vlmeval/dataset/utils/judge_util.py
VLMEvalKit/vlmeval/dataset/utils/llavabench.py
VLMEvalKit/vlmeval/dataset/utils/logicvista.py
VLMEvalKit/vlmeval/dataset/utils/longvideobench.py
VLMEvalKit/vlmeval/dataset/utils/mathv.py
VLMEvalKit/vlmeval/dataset/utils/mathverse.py
VLMEvalKit/vlmeval/dataset/utils/mathvista.py
VLMEvalKit/vlmeval/dataset/utils/megabench/README.md
VLMEvalKit/vlmeval/dataset/utils/megabench/__init__.py
VLMEvalKit/vlmeval/dataset/utils/megabench/aggregation/mean_agg.py
VLMEvalKit/vlmeval/dataset/utils/megabench/aggregation/min_agg.py
VLMEvalKit/vlmeval/dataset/utils/megabench/aggregation/unsupported_agg.py
VLMEvalKit/vlmeval/dataset/utils/megabench/aggregation_type.py
VLMEvalKit/vlmeval/dataset/utils/megabench/evaluator.py
VLMEvalKit/vlmeval/dataset/utils/megabench/metric_type.py
VLMEvalKit/vlmeval/dataset/utils/megabench/parsing/answer_str_parse.py
VLMEvalKit/vlmeval/dataset/utils/megabench/parsing/common/parsers.py
VLMEvalKit/vlmeval/dataset/utils/megabench/parsing/common/utils.py
VLMEvalKit/vlmeval/dataset/utils/megabench/parsing/dummy_parse.py
VLMEvalKit/vlmeval/dataset/utils/megabench/parsing/json_parse.py
VLMEvalKit/vlmeval/dataset/utils/megabench/requirements.txt
VLMEvalKit/vlmeval/dataset/utils/megabench/response_parse_type.py
VLMEvalKit/vlmeval/dataset/utils/megabench/scoring/ascii_art_gpt4o_judge.py
VLMEvalKit/vlmeval/dataset/utils/megabench/scoring/chess_jaccard.py
VLMEvalKit/vlmeval/dataset/utils/megabench/scoring/common/conversions.py
VLMEvalKit/vlmeval/dataset/utils/megabench/scoring/common/metrics.py
VLMEvalKit/vlmeval/dataset/utils/megabench/scoring/common/transformations.py
VLMEvalKit/vlmeval/dataset/utils/megabench/scoring/constrained_generation.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit/run.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit_ov/run.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMTrainKit/neo/train/train.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit/vlmeval/dataset/utils/vcrbench/eval.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit_ov/vlmeval/dataset/utils/vcrbench/eval.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit_ov/smoke_test_neo_si.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit_ov/utils.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit/scripts/apires_scan.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit/scripts/auto_run.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit/scripts/data_browser.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit/scripts/summarize.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit/tests/test_minimax_provider.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit/vlmeval/config.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit/vlmeval/inference.py`
- `projects/PROJ-638-https-arxiv-org-abs-2605-28820/external/NEO/VLMEvalKit/vlmeval/inference_mt.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `NEO` — not re-implementing it.
