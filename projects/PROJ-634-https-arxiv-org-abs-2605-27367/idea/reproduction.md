# Reproduce & validate: SpatialBench: Is Your Spatial Foundation Model an All-Round Player?

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/   (clone of https://github.com/Ropedia/SpatialBench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** SpatialBench: Is Your Spatial Foundation Model an All-Round Player?

**Abstract:** While spatial foundation models have demonstrated impressive performance on standard datasets, a critical question remains: are they truly all-round players capable of generalizing robustly across diverse downstream tasks, arbitrary viewpoints, shifting scene domains, varying input densities, and specific hardware constraints? Answering this overarching question requires a holistic assessment, yet current models are mainly evaluated on specific domains for which they were specifically designed or trained. Such evaluations are intrinsically limited by narrow paradigm coverage, limited scene domains, and arbitrary frame sampling, making it fundamentally difficult to assess their true generalization capabilities. To address this gap, we present SpatialBench, a cross-paradigm, domain-diverse benchmark for spatial foundation models with deterministic sampling. SpatialBench features unprecedented scale and rigorous deterministic design, comprising 19 datasets and 546 scenes across 5 diverse spatial domains. It comprehensively evaluates 41 models across 6 paradigms on 5 task suites under 4 different input density settings. Our extensive evaluation reveals that current models are not yet all-round players, and uncovers crucial insights for future advancement. Specifically, we demonstrate that full-context attention maximizes accuracy while bounded-memory strategies unlock long-sequence scalability. Moreover, our empirical evaluations in challenging embodied and egocentric tasks demonstrate that strict domain alignment and high data quality are far more critical to performance than simple dataset scaling. Furthermore, to address the largest data gap identified in our analysis, we go beyond evaluation by introducing a large-scale dataset, DA-Next-5M, and a strong baseline model, DA-Next, pushing the boundaries of spatial representation learning.

## Shipped code — file tree (`projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/`)

```
.gitignore
.gitmodules
README.md
assets/overview.png
assets/sb_logo.png
assets/teaser.png
benchmark/README.md
benchmark/__init__.py
benchmark/configs/chunk/da3_streaming_eval.yaml
benchmark/configs/chunk/pi_long_eval.yaml
benchmark/configs/chunk/vggt_long_eval.yaml
benchmark/configs/end2end/amb3r_eval.yaml
benchmark/configs/end2end/da3_base_eval.yaml
benchmark/configs/end2end/da3_giant_eval.yaml
benchmark/configs/end2end/da3_large_eval.yaml
benchmark/configs/end2end/da3_small_eval.yaml
benchmark/configs/end2end/da3nested_eval.yaml
benchmark/configs/end2end/fastvggt_eval.yaml
benchmark/configs/end2end/mapanything_eval.yaml
benchmark/configs/end2end/omnivggt_eval.yaml
benchmark/configs/end2end/pi3_eval.yaml
benchmark/configs/end2end/pi3x_eval.yaml
benchmark/configs/end2end/vggt_eval.yaml
benchmark/configs/end2end/vggt_omega_eval.yaml
benchmark/configs/end2end/worldmirror_eval.yaml
benchmark/configs/online/infinitevggt_eval.yaml
benchmark/configs/online/lingbot_map_stream_eval.yaml
benchmark/configs/online/lingbot_map_window_eval.yaml
benchmark/configs/online/page4d_eval.yaml
benchmark/configs/online/r3_local_eval.yaml
benchmark/configs/online/r3_long_eval.yaml
benchmark/configs/online/r3_strided_eval.yaml
benchmark/configs/online/stream3r_stream_eval.yaml
benchmark/configs/online/stream3r_window_eval.yaml
benchmark/configs/online/streamvggt_eval.yaml
benchmark/configs/optimization/dust3r_eval.yaml
benchmark/configs/optimization/mast3r_eval.yaml
benchmark/configs/prior/README.md
benchmark/configs/prior/da3_giant_prior_eval.yaml
benchmark/configs/prior/danext_prior_eval.yaml
benchmark/configs/prior/mapanything_prior_eval.yaml
benchmark/configs/prior/omnivggt_prior_eval.yaml
benchmark/configs/prior/pi3x_prior_eval.yaml
benchmark/configs/prior/worldmirror_prior_eval.yaml
benchmark/configs/ttt/loger_eval.yaml
benchmark/configs/ttt/loger_star_eval.yaml
benchmark/configs/ttt/scal3r_eval.yaml
benchmark/configs/ttt/vgg_ttt_eval.yaml
benchmark/configs/ttt/zipmap_eval.yaml
benchmark/datasets/__init__.py
benchmark/datasets/benchmark_dataset.py
benchmark/datasets/data_readers.py
benchmark/evaluation/__init__.py
benchmark/evaluation/alignment.py
benchmark/evaluation/bench_memory_curve.py
benchmark/evaluation/metrics.py
benchmark/evaluation/model_adapters/__init__.py
benchmark/evaluation/model_adapters/amb3r_adapter.py
benchmark/evaluation/model_adapters/base_adapter.py
benchmark/evaluation/model_adapters/da3_adapter.py
benchmark/evaluation/model_adapters/da3_streaming_adapter.py
benchmark/evaluation/model_adapters/da3nested_adapter.py
benchmark/evaluation/model_adapters/dust3r_adapter.py
benchmark/evaluation/model_adapters/fastvggt_adapter.py
benchmark/evaluation/model_adapters/infinitevggt_adapter.py
benchmark/evaluation/model_adapters/lingbot_map_adapter.py
benchmark/evaluation/model_adapters/lingbot_map_stream_adapter.py
benchmark/evaluation/model_adapters/loger_adapter.py
benchmark/evaluation/model_adapters/mapanything_adapter.py
benchmark/evaluation/model_adapters/mast3r_adapter.py
benchmark/evaluation/model_adapters/omnivggt_adapter.py
benchmark/evaluation/model_adapters/page4d_adapter.py
benchmark/evaluation/model_adapters/pi3_adapter.py
benchmark/evaluation/model_adapters/pi3x_adapter.py
benchmark/evaluation/model_adapters/pi_long_adapter.py
benchmark/evaluation/model_adapters/r3_adapter.py
benchmark/evaluation/model_adapters/scal3r_adapter.py
benchmark/evaluation/model_adapters/stream3r_adapter.py
benchmark/evaluation/model_adapters/streamvggt_adapter.py
benchmark/evaluation/model_adapters/vgg_ttt_adapter.py
benchmark/evaluation/model_adapters/vggt_adapter.py
benchmark/evaluation/model_adapters/vggt_long_adapter.py
benchmark/evaluation/model_adapters/vggt_omega_adapter.py
benchmark/evaluation/model_adapters/worldmirror_adapter.py
benchmark/evaluation/model_adapters/zipmap_adapter.py
benchmark/evaluation/report.py
benchmark/evaluation/run_benchmark.py
benchmark/evaluation/run_benchmark_with_prior.py
benchmark/models/amb3r_root/amb3r/backend.py
benchmark/models/amb3r_root/amb3r/blocks.py
benchmark/models/amb3r_root/amb3r/datasets/__init__.py
benchmark/models/amb3r_root/amb3r/datasets/base_many_view_dataset.py
benchmark/models/amb3r_root/amb3r/datasets/bonn.py
benchmark/models/amb3r_root/amb3r/datasets/demo.py
benchmark/models/amb3r_root/amb3r/datasets/dtu.py
benchmark/models/amb3r_root/amb3r/datasets/dtu_rmvd.json
benchmark/models/amb3r_root/amb3r/datasets/eth3d.py
benchmark/models/amb3r_root/amb3r/datasets/eth3d_rmvd.json
benchmark/models/amb3r_root/amb3r/datasets/imc.py
benchmark/models/amb3r_root/amb3r/datasets/kitti.py
benchmark/models/amb3r_root/amb3r/datasets/rel10k.py
benchmark/models/amb3r_root/amb3r/datasets/scannet.py
benchmark/models/amb3r_root/amb3r/datasets/seven_scenes.py
benchmark/models/amb3r_root/amb3r/datasets/sintel.py
benchmark/models/amb3r_root/amb3r/datasets/tnt.py
benchmark/models/amb3r_root/amb3r/frontend.py
benchmark/models/amb3r_root/amb3r/loss.py
benchmark/models/amb3r_root/amb3r/model.py
benchmark/models/amb3r_root/amb3r/model_zoo.py
benchmark/models/amb3r_root/amb3r/tools/keyframes.py
benchmark/models/amb3r_root/amb3r/tools/pose_align.py
benchmark/models/amb3r_root/amb3r/tools/pose_dist.py
benchmark/models/amb3r_root/amb3r/tools/pose_interp.py
benchmark/models/amb3r_root/amb3r/tools/pts_align.py
benchmark/models/amb3r_root/amb3r/tools/pts_vis.py
benchmark/models/amb3r_root/amb3r/tools/utils.py
benchmark/models/amb3r_root/amb3r/tools/vis.py
benchmark/models/amb3r_root/amb3r/tools/voxel_utils.py
benchmark/models/amb3r_root/amb3r/training.py
benchmark/models/amb3r_root/thirdparty/croco/LICENSE
benchmark/models/amb3r_root/thirdparty/croco/NOTICE
benchmark/models/amb3r_root/thirdparty/croco/README.MD
benchmark/models/amb3r_root/thirdparty/croco/assets/Chateau1.png
benchmark/models/amb3r_root/thirdparty/croco/assets/Chateau2.png
benchmark/models/amb3r_root/thirdparty/croco/assets/arch.jpg
benchmark/models/amb3r_root/thirdparty/croco/croco-stereo-flow-demo.ipynb
benchmark/models/amb3r_root/thirdparty/croco/datasets/__init__.py
benchmark/models/amb3r_root/thirdparty/croco/datasets/crops/README.MD
benchmark/models/amb3r_root/thirdparty/croco/datasets/crops/extract_crops_from_images.py
benchmark/models/amb3r_root/thirdparty/croco/datasets/habitat_sim/README.MD
benchmark/models/amb3r_root/thirdparty/croco/datasets/habitat_sim/__init__.py
benchmark/models/amb3r_root/thirdparty/croco/datasets/habitat_sim/generate_from_metadata.py
benchmark/models/amb3r_root/thirdparty/croco/datasets/habitat_sim/generate_from_metadata_files.py
benchmark/models/amb3r_root/thirdparty/croco/datasets/habitat_sim/generate_multiview_images.py
benchmark/models/amb3r_root/thirdparty/croco/datasets/habitat_sim/multiview_habitat_sim_generator.py
benchmark/models/amb3r_root/thirdparty/croco/datasets/habitat_sim/pack_metadata_files.py
benchmark/models/amb3r_root/thirdparty/croco/datasets/habitat_sim/paths.py
benchmark/models/amb3r_root/thirdparty/croco/datasets/pairs_dataset.py
benchmark/models/amb3r_root/thirdparty/croco/datasets/transforms.py
benchmark/models/amb3r_root/thirdparty/croco/demo.py
benchmark/models/amb3r_root/thirdparty/croco/interactive_demo.ipynb
benchmark/models/amb3r_root/thirdparty/croco/models/blocks.py
benchmark/models/amb3r_root/thirdparty/croco/models/criterion.py
benchmark/models/amb3r_root/thirdparty/croco/models/croco.py
benchmark/models/amb3r_root/thirdparty/croco/models/croco_downstream.py
benchmark/models/amb3r_root/thirdparty/croco/models/curope/__init__.py
benchmark/models/amb3r_root/thirdparty/croco/models/curope/curope.cpp
benchmark/models/amb3r_root/thirdparty/croco/models/curope/curope2d.py
benchmark/models/amb3r_root/thirdparty/croco/models/curope/kernels.cu
benchmark/models/amb3r_root/thirdparty/croco/models/curope/setup.py
benchmark/models/amb3r_root/thirdparty/croco/models/dpt_block.py
benchmark/models/amb3r_root/thirdparty/croco/models/head_downstream.py
benchmark/models/amb3r_root/thirdparty/croco/models/masking.py
benchmark/models/amb3r_root/thirdparty/croco/models/pos_embed.py
benchmark/models/amb3r_root/thirdparty/croco/pretrain.py
benchmark/models/amb3r_root/thirdparty/croco/stereoflow/README.MD
benchmark/models/amb3r_root/thirdparty/croco/stereoflow/augmentor.py
benchmark/models/amb3r_root/thirdparty/croco/stereoflow/criterion.py
benchmark/models/amb3r_root/thirdparty/croco/stereoflow/datasets_flow.py
benchmark/models/amb3r_root/thirdparty/croco/stereoflow/datasets_stereo.py
benchmark/models/amb3r_root/thirdparty/croco/stereoflow/download_model.sh
benchmark/models/amb3r_root/thirdparty/croco/stereoflow/engine.py
benchmark/models/amb3r_root/thirdparty/croco/stereoflow/test.py
benchmark/models/amb3r_root/thirdparty/croco/stereoflow/train.py
benchmark/models/amb3r_root/thirdparty/croco/utils/misc.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/api.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/app/css_and_html.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/app/gradio_app.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/app/modules/__init__.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/app/modules/event_handlers.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/app/modules/file_handlers.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/app/modules/model_inference.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/app/modules/ui_components.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/app/modules/utils.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/app/modules/visualization.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/__init__.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/configs/eval_bench.yaml
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/dataset.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/datasets/__init__.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/datasets/dtu.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/datasets/dtu64.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/datasets/eth3d.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/datasets/hiroom.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/datasets/scannetpp.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/datasets/sevenscenes.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/evaluator.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/print_metrics.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/registries.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/bench/utils.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/cfg.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/cli.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/configs/da3-base.yaml
benchmark/models/amb3r_root/thirdparty/depth_anything_3/configs/da3-giant.yaml
benchmark/models/amb3r_root/thirdparty/depth_anything_3/configs/da3-large.yaml
benchmark/models/amb3r_root/thirdparty/depth_anything_3/configs/da3-small.yaml
benchmark/models/amb3r_root/thirdparty/depth_anything_3/configs/da3metric-large.yaml
benchmark/models/amb3r_root/thirdparty/depth_anything_3/configs/da3mono-large.yaml
benchmark/models/amb3r_root/thirdparty/depth_anything_3/configs/da3nested-giant-large.yaml
benchmark/models/amb3r_root/thirdparty/depth_anything_3/model/__init__.py
benchmark/models/amb3r_root/thirdparty/depth_anything_3/model/cam_dec.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/models/scal3r/run.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/models/amb3r_root/thirdparty/robustmvd/train.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/models/amb3r_root/thirdparty/croco/stereoflow/train.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/models/amb3r_root/thirdparty/moge/moge/scripts/train.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/models/amb3r_root/thirdparty/robustmvd/eval.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/models/r3/demo.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/models/amb3r_root/amb3r/datasets/demo.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/models/amb3r_root/thirdparty/croco/demo.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/visualize_benchmark_web.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/datasets/benchmark_dataset.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/datasets/data_readers.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/evaluation/alignment.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/evaluation/bench_memory_curve.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/evaluation/metrics.py`
- `projects/PROJ-634-https-arxiv-org-abs-2605-27367/external/SpatialBench/benchmark/evaluation/report.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `SpatialBench` — not re-implementing it.
