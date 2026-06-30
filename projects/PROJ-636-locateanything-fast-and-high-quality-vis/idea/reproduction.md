# Reproduce & validate: LocateAnything: Fast and High-Quality Vision-Language Grounding with Parallel Box Decoding

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/   (clone of https://github.com/NVlabs/Eagle)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** LocateAnything: Fast and High-Quality Vision-Language Grounding with Parallel Box Decoding

**Abstract:** Vision-language models (VLMs) commonly formulate visual grounding and detection as a coordinate-token generation problem, serializing each 2D box into multiple 1D tokens that are learned and decoded largely independently. This token-by-token decoding mismatches the coupled structure of box geometry and creates a practical inference bottleneck due to strictly sequential generation. We introduce LocateAnything, a unified generative grounding and detection framework based on Parallel Box Decoding (PBD). By decoding geometric elements such as bounding boxes and points as atomic units in a single step, LocateAnything preserves intra-box geometric coherence and unlocks substantial parallelism. We show that PBD improves both decoding throughput and localization accuracy. We further develop a scalable data engine and curate LocateAnything-Data, a large-scale dataset with more than 138 million training samples, substantially increasing data diversity for high-precision localization. Extensive evaluations show that LocateAnything advances the speed-accuracy frontier, achieving significantly higher decoding throughput while improving high-IoU localization quality across diverse benchmarks. The results highlight the complementary benefits of Parallel Box Decoding and large-scale training data in enabling efficient and precise unified visual grounding and detection.

## Shipped code — file tree (`projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/`)

```
.gitattributes
.gitignore
CONTRIBUTING.md
Eagle/Eagle.pdf
Eagle/README.md
Eagle/assets/Eagle.png
Eagle/assets/Logo.png
Eagle/assets/animal-compare.png
Eagle/assets/eagle-logo.png
Eagle/assets/fig-teaser.jpg
Eagle/assets/georgia-tech.jpeg
Eagle/assets/health-insurance.png
Eagle/assets/leasing-apartment.png
Eagle/assets/nvidia.jpeg
Eagle/assets/visual/AV1.png
Eagle/assets/visual/AV2.png
Eagle/assets/visual/Doc1.png
Eagle/assets/visual/Doc2.png
Eagle/assets/visual/Doc3.png
Eagle/assets/visual/VQA1.png
Eagle/assets/visual/VQA2.png
Eagle/assets/visual/VQA3.png
Eagle/eagle/__init__.py
Eagle/eagle/constants.py
Eagle/eagle/conversation.py
Eagle/eagle/eval/eval_gpt_review.py
Eagle/eagle/eval/eval_gpt_review_bench.py
Eagle/eagle/eval/eval_gpt_review_visual.py
Eagle/eagle/eval/eval_pope.py
Eagle/eagle/eval/eval_science_qa.py
Eagle/eagle/eval/eval_science_qa_gpt4.py
Eagle/eagle/eval/eval_science_qa_gpt4_requery.py
Eagle/eagle/eval/eval_textvqa.py
Eagle/eagle/eval/generate_webpage_data_from_table.py
Eagle/eagle/eval/m4c_evaluator.py
Eagle/eagle/eval/model_qa.py
Eagle/eagle/eval/model_vqa.py
Eagle/eagle/eval/model_vqa_loader.py
Eagle/eagle/eval/model_vqa_mmbench.py
Eagle/eagle/eval/model_vqa_mmmu.py
Eagle/eagle/eval/model_vqa_science.py
Eagle/eagle/eval/qa_baseline_gpt35.py
Eagle/eagle/eval/run_eagle.py
Eagle/eagle/eval/summarize_gpt_review.py
Eagle/eagle/mm_utils.py
Eagle/eagle/model/__init__.py
Eagle/eagle/model/builder.py
Eagle/eagle/model/consolidate.py
Eagle/eagle/model/eagle_arch.py
Eagle/eagle/model/language_model/__init__.py
Eagle/eagle/model/language_model/eagle_llama.py
Eagle/eagle/model/multimodal_encoder/__init__.py
Eagle/eagle/model/multimodal_encoder/builder.py
Eagle/eagle/model/multimodal_encoder/clip_encoder.py
Eagle/eagle/model/multimodal_encoder/convnext_encoder.py
Eagle/eagle/model/multimodal_encoder/hr_clip_encoder.py
Eagle/eagle/model/multimodal_encoder/multi_backbone_channel_concatenation_encoder.py
Eagle/eagle/model/multimodal_encoder/pix2struct_encoder.py
Eagle/eagle/model/multimodal_encoder/sam_encoder.py
Eagle/eagle/model/multimodal_encoder/vision_models/__init__.py
Eagle/eagle/model/multimodal_encoder/vision_models/convnext.py
Eagle/eagle/model/multimodal_encoder/vision_models/eva_vit.py
Eagle/eagle/model/multimodal_projector/__init__.py
Eagle/eagle/model/multimodal_projector/builder.py
Eagle/eagle/train/eagle_trainer.py
Eagle/eagle/train/llama_flash_attn_monkey_patch.py
Eagle/eagle/train/llama_xformers_attn_monkey_patch.py
Eagle/eagle/utils.py
Eagle/evaluate_lmms_eval.py
Eagle/gradio_demo.py
Eagle/lmms_eval/__init__.py
Eagle/lmms_eval/__main__.py
Eagle/lmms_eval/api/__init__.py
Eagle/lmms_eval/api/filter.py
Eagle/lmms_eval/api/instance.py
Eagle/lmms_eval/api/metrics.py
Eagle/lmms_eval/api/model.py
Eagle/lmms_eval/api/registry.py
Eagle/lmms_eval/api/samplers.py
Eagle/lmms_eval/api/task.py
Eagle/lmms_eval/evaluator.py
Eagle/lmms_eval/filters/__init__.py
Eagle/lmms_eval/filters/decontamination.py
Eagle/lmms_eval/filters/extraction.py
Eagle/lmms_eval/filters/selection.py
Eagle/lmms_eval/filters/transformation.py
Eagle/lmms_eval/logging_utils.py
Eagle/lmms_eval/models/__init__.py
Eagle/lmms_eval/models/eagle.py
Eagle/lmms_eval/models/gpt4v.py
Eagle/lmms_eval/tasks/__init__.py
Eagle/lmms_eval/tasks/_task_utils/file_utils.py
Eagle/lmms_eval/tasks/_task_utils/gpt_eval_utils.py
Eagle/lmms_eval/tasks/_task_utils/vqa_eval_metric.py
Eagle/lmms_eval/tasks/ai2d/ai2d.yaml
Eagle/lmms_eval/tasks/ai2d/upload_ai2d.py
Eagle/lmms_eval/tasks/ai2d/utils.py
Eagle/lmms_eval/tasks/chartqa/chartqa.yaml
Eagle/lmms_eval/tasks/chartqa/upload_chartqa.py
Eagle/lmms_eval/tasks/chartqa/utils.py
Eagle/lmms_eval/tasks/cmmmu/_cmmmu.yaml
Eagle/lmms_eval/tasks/cmmmu/_default_template_cmmmu_yaml
Eagle/lmms_eval/tasks/cmmmu/cmmmu_test.yaml
Eagle/lmms_eval/tasks/cmmmu/cmmmu_val.yaml
Eagle/lmms_eval/tasks/cmmmu/utils.py
Eagle/lmms_eval/tasks/coco_cap/coco2014_cap.yaml
Eagle/lmms_eval/tasks/coco_cap/coco2014_cap_test.yaml
Eagle/lmms_eval/tasks/coco_cap/coco2014_cap_val.yaml
Eagle/lmms_eval/tasks/coco_cap/coco2017_cap.yaml
Eagle/lmms_eval/tasks/coco_cap/coco2017_cap_test.yaml
Eagle/lmms_eval/tasks/coco_cap/coco2017_cap_val.yaml
Eagle/lmms_eval/tasks/coco_cap/coco_cap.yaml
Eagle/lmms_eval/tasks/coco_cap/utils.py
Eagle/lmms_eval/tasks/docvqa/_default_template_docvqa_yaml
Eagle/lmms_eval/tasks/docvqa/docvqa.yaml
Eagle/lmms_eval/tasks/docvqa/docvqa_test.yaml
Eagle/lmms_eval/tasks/docvqa/docvqa_val.yaml
Eagle/lmms_eval/tasks/docvqa/utils.py
Eagle/lmms_eval/tasks/ferret/ferret.yaml
Eagle/lmms_eval/tasks/ferret/rule.json
Eagle/lmms_eval/tasks/ferret/utils.py
Eagle/lmms_eval/tasks/flickr30k/flickr30k.yaml
Eagle/lmms_eval/tasks/flickr30k/flickr30k_test.yaml
Eagle/lmms_eval/tasks/flickr30k/utils.py
Eagle/lmms_eval/tasks/gqa/gqa.yaml
Eagle/lmms_eval/tasks/gqa/utils.py
Eagle/lmms_eval/tasks/hallusion_bench/evaluate_hb.py
Eagle/lmms_eval/tasks/hallusion_bench/hallusion_bench_image.yaml
Eagle/lmms_eval/tasks/hallusion_bench/utils.py
Eagle/lmms_eval/tasks/iconqa/_default_template_docvqa_yaml
Eagle/lmms_eval/tasks/iconqa/iconqa.yaml
Eagle/lmms_eval/tasks/iconqa/iconqa_test.yaml
Eagle/lmms_eval/tasks/iconqa/iconqa_val.yaml
Eagle/lmms_eval/tasks/iconqa/utils.py
Eagle/lmms_eval/tasks/infovqa/_default_template_infovqa_yaml
Eagle/lmms_eval/tasks/infovqa/infovqa.yaml
Eagle/lmms_eval/tasks/infovqa/infovqa_test.yaml
Eagle/lmms_eval/tasks/infovqa/infovqa_val.yaml
Eagle/lmms_eval/tasks/infovqa/utils.py
Eagle/lmms_eval/tasks/llava-bench-coco/llava-bench-coco.yaml
Eagle/lmms_eval/tasks/llava-bench-coco/rule.json
Eagle/lmms_eval/tasks/llava-bench-coco/utils.py
Eagle/lmms_eval/tasks/llava-in-the-wild/llava-in-the-wild.yaml
Eagle/lmms_eval/tasks/llava-in-the-wild/rule.json
Eagle/lmms_eval/tasks/llava-in-the-wild/utils.py
Eagle/lmms_eval/tasks/mathvista/mathvista.yaml
Eagle/lmms_eval/tasks/mathvista/mathvista_evals.py
Eagle/lmms_eval/tasks/mathvista/mathvista_test.yaml
Eagle/lmms_eval/tasks/mathvista/mathvista_testmini.yaml
Eagle/lmms_eval/tasks/mathvista/utils.py
Eagle/lmms_eval/tasks/mmbench/_default_template_mmbench_cn_yaml
Eagle/lmms_eval/tasks/mmbench/_default_template_mmbench_en_yaml
Eagle/lmms_eval/tasks/mmbench/cc_utils.py
Eagle/lmms_eval/tasks/mmbench/cn_utils.py
Eagle/lmms_eval/tasks/mmbench/en_utils.py
Eagle/lmms_eval/tasks/mmbench/mmbench.yaml
Eagle/lmms_eval/tasks/mmbench/mmbench_cc.yaml
Eagle/lmms_eval/tasks/mmbench/mmbench_cn.yaml
Eagle/lmms_eval/tasks/mmbench/mmbench_cn_dev.yaml
Eagle/lmms_eval/tasks/mmbench/mmbench_cn_test.yaml
Eagle/lmms_eval/tasks/mmbench/mmbench_en.yaml
Eagle/lmms_eval/tasks/mmbench/mmbench_en_dev.yaml
Eagle/lmms_eval/tasks/mmbench/mmbench_en_test.yaml
Eagle/lmms_eval/tasks/mmbench/mmbench_evals.py
Eagle/lmms_eval/tasks/mme/mme.yaml
Eagle/lmms_eval/tasks/mme/utils.py
Eagle/lmms_eval/tasks/mmmu/mmmu.yaml
Eagle/lmms_eval/tasks/mmmu/mmmu_test.yaml
Eagle/lmms_eval/tasks/mmmu/mmmu_val.yaml
Eagle/lmms_eval/tasks/mmmu/utils.py
Eagle/lmms_eval/tasks/mmvet/mmvet.yaml
Eagle/lmms_eval/tasks/mmvet/utils.py
Eagle/lmms_eval/tasks/multidocvqa/multidocvqa.yaml
Eagle/lmms_eval/tasks/multidocvqa/multidocvqa_test.yaml
Eagle/lmms_eval/tasks/multidocvqa/multidocvqa_val.yaml
Eagle/lmms_eval/tasks/multidocvqa/utils.py
Eagle/lmms_eval/tasks/nocaps/_default_template_nocaps_yaml
Eagle/lmms_eval/tasks/nocaps/nocaps.yaml
Eagle/lmms_eval/tasks/nocaps/nocaps_test.yaml
Eagle/lmms_eval/tasks/nocaps/nocaps_val.yaml
Eagle/lmms_eval/tasks/nocaps/utils.py
Eagle/lmms_eval/tasks/ocrbench/ocrbench.yaml
Eagle/lmms_eval/tasks/ocrbench/upload_ocrbench.py
Eagle/lmms_eval/tasks/ocrbench/utils.py
Eagle/lmms_eval/tasks/ok_vqa/_default_template_vqa_yaml
Eagle/lmms_eval/tasks/ok_vqa/_generate_config.py
Eagle/lmms_eval/tasks/ok_vqa/_ok_vqa.yaml
Eagle/lmms_eval/tasks/ok_vqa/ok_vqa_val2014.yaml
Eagle/lmms_eval/tasks/ok_vqa/utils.py
Eagle/lmms_eval/tasks/olympiadbench/cn_utils.py
Eagle/lmms_eval/tasks/olympiadbench/en_utils.py
Eagle/lmms_eval/tasks/olympiadbench/olympiadbench.yaml
Eagle/lmms_eval/tasks/olympiadbench/olympiadbench_evals.py
Eagle/lmms_eval/tasks/olympiadbench/olympiadbench_test_cn.yaml
Eagle/lmms_eval/tasks/olympiadbench/olympiadbench_test_en.yaml
Eagle/lmms_eval/tasks/pope/pope.yaml
Eagle/lmms_eval/tasks/pope/utils.py
Eagle/lmms_eval/tasks/refcoco/_default_template_bbox_yaml
Eagle/lmms_eval/tasks/refcoco/_default_template_seg_yaml
Eagle/lmms_eval/tasks/refcoco/_generate_config.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/train.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/evaluate_lmms_eval.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/gradio_demo.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/predict_demo.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/train_mem.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Embodied/locateanything_worker.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/eagle/constants.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/eagle/conversation.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/eagle/mm_utils.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/eagle/utils.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/lmms_eval/evaluator.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/lmms_eval/logging_utils.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/lmms_eval/utils.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/scripts/convert_gqa_for_eval.py`
- `projects/PROJ-636-locateanything-fast-and-high-quality-vis/external/Eagle/Eagle/scripts/convert_mmbench_for_submission.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `Eagle` — not re-implementing it.
