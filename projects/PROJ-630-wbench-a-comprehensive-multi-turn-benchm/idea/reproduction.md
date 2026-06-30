# Reproduce & validate: WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/   (clone of https://github.com/meituan-longcat/WBench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation

**Abstract:** Interactive world models are advancing rapidly, yet existing benchmarks cover only part of the required competencies, leaving no unified standard for systematic evaluation. To fill this gap, we introduce WBench, a comprehensive multi-turn benchmark for interactive world model evaluation along five dimensions, namely video quality, setting adherence, interaction adherence, consistency, and physics compliance. WBench contains 289 test cases and 1,058 interaction turns, where each case specifies a world setting and a multi-turn interaction sequence, covering diverse scenes, styles, subjects, and both first- and third-person perspectives, together with four interaction types, including navigation, subject action, event editing, and perspective switching. For navigation, WBench unifies text, 6-DoF pose, and discrete-action control, enabling evaluation of models with different native input interfaces. Evaluation uses 22 automatic sub-metrics that combine specialist vision models with large multimodal models, and all metrics are validated against human judgments. Across 20 state-of-the-art models, we find that no single model performs strongly across all dimensions. We provide detailed diagnostic insights into the characteristic strengths, weaknesses, and open challenges of each model. Code and data are available at https://github.com/meituan-longcat/WBench.

## Shipped code — file tree (`projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/`)

```
.claude/skills/wbench-evaluate/SKILL.md
.claude/skills/wbench-generate/SKILL.md
.claude/skills/wbench-submit/SKILL.md
.gitignore
.gitmodules
LICENSE
README.md
WBench_Longcat_early_access.pdf
assets/distribution.png
assets/icon/alibaba.png
assets/icon/amap.png
assets/icon/bytedance.png
assets/icon/cosmos.png
assets/icon/fudan.svg
assets/icon/google.png
assets/icon/hunyuan.png
assets/icon/inspatio.jpeg
assets/icon/kairos.png
assets/icon/kling.jpeg
assets/icon/lightrix.jpeg
assets/icon/lingbot.png
assets/icon/longcat-color.png
assets/icon/longcat.png
assets/icon/meituan.png
assets/icon/modelscope.svg
assets/icon/nankai.png
assets/icon/nvidia.svg
assets/icon/shlab.png
assets/icon/skywork.jpeg
assets/icon/thu.png
assets/icon/wan.png
assets/icon/yume.png
assets/leaderboard_20models_navi.csv
assets/leaderboard_9models_full.csv
assets/longcat-logo-full.png
assets/qr_code.png
assets/teaser.png
assets/wx_qr.png
docs/SUBMISSION.md
examples/hy_worldplay/README.md
examples/hy_worldplay/convert_cases_to_jsonl.py
examples/hy_worldplay/generate_navigation.py
examples/hy_worldplay/navigation_to_poses.py
generate.py
main.py
src/__init__.py
src/compat.py
src/config.yaml
src/evaluate.py
src/metrics/__init__.py
src/metrics/base.py
src/metrics/consistency/__init__.py
src/metrics/consistency/background_consistency.py
src/metrics/consistency/perspective_consistency.py
src/metrics/consistency/reconstruction_consistency.py
src/metrics/consistency/segment_continuity.py
src/metrics/consistency/spatial_consistency.py
src/metrics/consistency/subject_consistency.py
src/metrics/interaction/__init__.py
src/metrics/interaction/navigation_trajectory.py
src/metrics/interaction/vlm_interaction.py
src/metrics/physical/__init__.py
src/metrics/physical/causal_fidelity.py
src/metrics/physical/visual_plausibility.py
src/metrics/setting_adherence/__init__.py
src/metrics/setting_adherence/scene_adherence.py
src/metrics/setting_adherence/subject_adherence.py
src/metrics/video_quality/__init__.py
src/metrics/video_quality/aesthetic_quality.py
src/metrics/video_quality/dynamic_degree.py
src/metrics/video_quality/evaluator.py
src/metrics/video_quality/hpsv3_quality.py
src/metrics/video_quality/imaging_quality.py
src/metrics/video_quality/motion_smoothness.py
src/metrics/video_quality/temporal_flickering.py
src/metrics/vlm/__init__.py
src/metrics/vlm/vlm_evaluator.py
src/metrics/weight_utils.py
src/models/__init__.py
src/models/action/__init__.py
src/models/action/actions.py
src/models/action/demo.py
src/models/action/example_model.py
src/models/action/web/.claude/skills/genie3/SKILL.md
src/models/action/web/.claude/skills/happy/SKILL.md
src/models/action/web/README.md
src/models/action/web/auto_interact.py
src/models/action/web/genie3/t.png
src/models/action/web/genie3/upload_image_full.py
src/models/action/web/happy_oyster/batch_happy_oyster.py
src/models/action/web/happy_oyster/t2.png
src/models/action/web/requirements.txt
src/models/action/web/serve.py
src/models/base.py
src/models/camera/__init__.py
src/models/camera/demo.py
src/models/camera/example_model.py
src/models/camera/poses.py
src/models/conditioning.py
src/models/navigation.py
src/models/text/__init__.py
src/models/text/api_client.py
src/models/text/kling.py
src/models/text/prompt_builder.py
src/models/text/seedance.py
src/models/text/wan.py
src/utils/__init__.py
src/utils/case_loader.py
src/utils/turn_splitter.py
src/utils/video_utils.py
tools/download_weights.py
tools/install.sh
tools/install_vp.sh
tools/requirements.txt
tools/run_da3_depth.py
tools/run_megasam.py
tools/run_sam2_track.py
tools/run_visual_plausibility.py
tools/verify_install.py
```

## Detected entry points

- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/main.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/src/evaluate.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/src/models/action/demo.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/src/models/camera/demo.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/generate.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/src/compat.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/tools/download_weights.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/tools/run_da3_depth.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/tools/run_megasam.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/tools/run_sam2_track.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/tools/run_visual_plausibility.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/tools/verify_install.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/examples/hy_worldplay/convert_cases_to_jsonl.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/examples/hy_worldplay/generate_navigation.py`
- `projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/external/WBench/examples/hy_worldplay/navigation_to_poses.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `WBench` — not re-implementing it.
