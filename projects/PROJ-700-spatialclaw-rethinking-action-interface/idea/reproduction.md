# Reproduce & validate: SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/   (clone of https://github.com/NVlabs/SpatialClaw)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning

**Abstract:** Spatial reasoning, the ability to determine where objects are, how they relate, and how they move in 3D, remains a fundamental challenge for vision-language models (VLMs). Tool-augmented agents attempt to address this by augmenting VLMs with specialist perception modules, yet their effectiveness is bounded by the action interface through which those tools are invoked. In this work, we study how the design of this interface shapes the agent's capacity for open-ended spatial reasoning. Existing spatial agents either employ single-pass code execution, which commits to a full analysis strategy before any intermediate result is observed, or rely on a structured tool-call interface that often offers less flexibility for freely composing operations or tailoring the analysis to each task. Both designs offer limited flexibility for open-ended, complex 3D/4D spatial reasoning. We therefore propose SpatialClaw, a training-free framework for spatial reasoning that adopts code as the action interface. SpatialClaw maintains a stateful Python kernel pre-loaded with input frames and a suite of perception and geometry primitives, letting a VLM-backed agent write one executable cell per step conditioned on all prior outputs, enabling the agent to flexibly compose and manipulate perception results and adapt its analysis to both intermediate text and visual observations and the demands of each problem. Evaluated across 20 spatial reasoning benchmarks spanning a broad range of static and dynamic 3D/4D spatial reasoning tasks, SpatialClaw achieves 59.9% average accuracy, outperforming the recent spatial agent by +11.2 points, with consistent gains across six VLM backbones from two model families without any benchmark- or model-specific adaptation.

## Shipped code — file tree (`projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/`)

```
.env.example
.gitignore
.gitmodules
LICENSE
README.md
SECURITY.md
assets/radar.png
docs/architecture.md
docs/configuration.md
docs/installation.md
docs/monitoring.md
docs/running.md
docs/troubleshooting.md
spatial_agent/__init__.py
spatial_agent/config/dataset/blink.json
spatial_agent/config/dataset/cvbench.json
spatial_agent/config/dataset/dsibench.json
spatial_agent/config/dataset/erqa.json
spatial_agent/config/dataset/mindcube.json
spatial_agent/config/dataset/mmsi.json
spatial_agent/config/dataset/mmsivideo.json
spatial_agent/config/dataset/omni3d.json
spatial_agent/config/dataset/omnispatial.json
spatial_agent/config/dataset/osibench.json
spatial_agent/config/dataset/paibench.json
spatial_agent/config/dataset/perceptioncomp.json
spatial_agent/config/dataset/sparbench.json
spatial_agent/config/dataset/spatialtree.json
spatial_agent/config/dataset/spbench.json
spatial_agent/config/dataset/videomme.json
spatial_agent/config/dataset/videommev2.json
spatial_agent/config/dataset/viewspatial.json
spatial_agent/config/dataset/vsibench.json
spatial_agent/config/dataset/vsibench_unbiased.json
spatial_agent/config/dataset/vstibench.json
spatial_agent/config/model/gemma-4-26b-a4b.json
spatial_agent/config/model/gemma-4-31b.json
spatial_agent/config/model/qwen3.5-122b-a10b.json
spatial_agent/config/model/qwen3.5-397b-a17b.json
spatial_agent/config/model/qwen3.6-27b.json
spatial_agent/config/model/qwen3.6-35b-a3b.json
spatial_agent/config.py
spatial_agent/entrypoints/__init__.py
spatial_agent/entrypoints/cot_baseline.py
spatial_agent/entrypoints/debug_llm.py
spatial_agent/entrypoints/launch_gpu_server.py
spatial_agent/entrypoints/launch_vllm.py
spatial_agent/entrypoints/run.py
spatial_agent/evals/__init__.py
spatial_agent/evals/base.py
spatial_agent/evals/blink.py
spatial_agent/evals/cvbench.py
spatial_agent/evals/dsibench.py
spatial_agent/evals/erqa.py
spatial_agent/evals/factory.py
spatial_agent/evals/mindcube.py
spatial_agent/evals/mmsi.py
spatial_agent/evals/mmsivideo.py
spatial_agent/evals/omni3d.py
spatial_agent/evals/omnispatial.py
spatial_agent/evals/osibench.py
spatial_agent/evals/paibench.py
spatial_agent/evals/perceptioncomp.py
spatial_agent/evals/scoring.py
spatial_agent/evals/sparbench.py
spatial_agent/evals/spatialtree.py
spatial_agent/evals/spbench.py
spatial_agent/evals/videomme.py
spatial_agent/evals/videommev2.py
spatial_agent/evals/viewspatial.py
spatial_agent/evals/vsibench.py
spatial_agent/evals/vstibench.py
spatial_agent/gpu_dashboard/__init__.py
spatial_agent/gpu_dashboard/__main__.py
spatial_agent/gpu_dashboard/agent_counter.py
spatial_agent/gpu_dashboard/app.py
spatial_agent/gpu_dashboard/collector.py
spatial_agent/gpu_dashboard/discovery.py
spatial_agent/gpu_dashboard/sampler.py
spatial_agent/gpu_dashboard/storage.py
spatial_agent/gpu_dashboard/templates.py
spatial_agent/gpu_models/__init__.py
spatial_agent/gpu_models/base.py
spatial_agent/gpu_models/da3_model.py
spatial_agent/gpu_models/easyocr.py
spatial_agent/gpu_models/image_resize.py
spatial_agent/gpu_models/keepalive.py
spatial_agent/gpu_models/mapanything_model.py
spatial_agent/gpu_models/pi3_model.py
spatial_agent/gpu_models/sam3_model.py
spatial_agent/gpu_models/types.py
spatial_agent/kernel/__init__.py
spatial_agent/kernel/feedback_collector.py
spatial_agent/kernel/manager.py
spatial_agent/kernel/safety.py
spatial_agent/kernel/variable_tracker.py
spatial_agent/kernel_types/__init__.py
spatial_agent/kernel_types/feedback_module.py
spatial_agent/kernel_types/frame_image.py
spatial_agent/kernel_types/input_images.py
spatial_agent/kernel_types/metadata.py
spatial_agent/kernel_types/per_frame_types.py
spatial_agent/kernel_types/return_answer.py
spatial_agent/kernel_types/visual_feedback.py
spatial_agent/kernel_types/vlm_module.py
spatial_agent/launch_managers/__init__.py
spatial_agent/launch_managers/agent_manager/__init__.py
spatial_agent/launch_managers/agent_manager/__main__.py
spatial_agent/launch_managers/agent_manager/cli.py
spatial_agent/launch_managers/agent_manager/config.json
spatial_agent/launch_managers/agent_manager/config.py
spatial_agent/launch_managers/agent_manager/dashboard.py
spatial_agent/launch_managers/agent_manager/dispatcher.py
spatial_agent/launch_managers/agent_manager/experiment_chain.py
spatial_agent/launch_managers/agent_manager/state.py
spatial_agent/launch_managers/cli_utils.py
spatial_agent/launch_managers/gpu_server_manager/__init__.py
spatial_agent/launch_managers/gpu_server_manager/__main__.py
spatial_agent/launch_managers/gpu_server_manager/cli.py
spatial_agent/launch_managers/gpu_server_manager/config.json
spatial_agent/launch_managers/gpu_server_manager/config.py
spatial_agent/launch_managers/gpu_server_manager/dashboard.py
spatial_agent/launch_managers/gpu_server_manager/run_gpu_server.sh
spatial_agent/launch_managers/gpu_server_manager/server_chain.py
spatial_agent/launch_managers/gpu_server_manager/state.py
spatial_agent/launch_managers/slurm_utils.py
spatial_agent/launch_managers/vllm_manager/__init__.py
spatial_agent/launch_managers/vllm_manager/__main__.py
spatial_agent/launch_managers/vllm_manager/chat_templates/gemma4.jinja
spatial_agent/launch_managers/vllm_manager/cli.py
spatial_agent/launch_managers/vllm_manager/config.py
spatial_agent/launch_managers/vllm_manager/dashboard.py
spatial_agent/launch_managers/vllm_manager/models.json
spatial_agent/launch_managers/vllm_manager/run_vllm.sh
spatial_agent/launch_managers/vllm_manager/server_chain.py
spatial_agent/launch_managers/vllm_manager/state.py
spatial_agent/llm/__init__.py
spatial_agent/llm/client.py
spatial_agent/llm/planning_prompt.py
spatial_agent/llm/prompt_common.py
spatial_agent/llm/react_prompt.py
spatial_agent/llm/react_response_schema.py
spatial_agent/llm/react_translator.py
spatial_agent/llm/reflection_prompt.py
spatial_agent/llm/response_schema.py
spatial_agent/llm/system_prompt.py
spatial_agent/llm/vision_prompt.py
spatial_agent/logging_utils/__init__.py
spatial_agent/logging_utils/html_report.py
spatial_agent/logging_utils/logger.py
spatial_agent/nodes/__init__.py
spatial_agent/nodes/execute_node.py
spatial_agent/nodes/feedback_node.py
spatial_agent/nodes/init_node.py
spatial_agent/nodes/llm_step_node.py
spatial_agent/nodes/plan_node.py
spatial_agent/nodes/reflection_node.py
spatial_agent/nodes/router.py
spatial_agent/requirements/requirements-agent.txt
spatial_agent/requirements/requirements-vllm.txt
spatial_agent/scripts/agent/slurm/launch.sh
spatial_agent/scripts/agent/slurm/manager.py
spatial_agent/scripts/agent/slurm/run.sh
spatial_agent/scripts/cot_baseline/launch.sh
spatial_agent/scripts/cot_baseline/manager.py
spatial_agent/scripts/cot_baseline/run.sh
spatial_agent/scripts/download_datasets.sh
spatial_agent/scripts/gpu_dashboard/launch.sh
spatial_agent/scripts/gpu_dashboard/manager.py
spatial_agent/scripts/setup.sh
spatial_agent/scripts/viz_server/launch.sh
spatial_agent/scripts/viz_server/manager.py
spatial_agent/scripts/vllm/launch_qwen35_122b_a10b.sh
spatial_agent/scripts/vllm/launch_qwen35_2b.sh
spatial_agent/scripts/vllm/launch_qwen35_35b_a3b.sh
spatial_agent/scripts/vllm/launch_qwen35_397b.sh
spatial_agent/scripts/vllm/launch_qwen35_4b.sh
spatial_agent/scripts/vllm/launch_qwen35_9b.sh
spatial_agent/scripts/vllm/manager.py
spatial_agent/scripts/vllm/run_uv.sh
spatial_agent/state.py
spatial_agent/tools/__init__.py
spatial_agent/tools/base.py
spatial_agent/tools/draw_utils.py
spatial_agent/tools/easyocr_tool.py
spatial_agent/tools/geometry_utils.py
spatial_agent/tools/graph_drawer.py
spatial_agent/tools/mask_utils.py
spatial_agent/tools/reconstruct_tool.py
spatial_agent/tools/sam3_tool.py
spatial_agent/tools/time_utils.py
spatial_agent/visualization_server/__init__.py
spatial_agent/visualization_server/__main__.py
spatial_agent/visualization_server/app.py
spatial_agent/visualization_server/category_maps.py
spatial_agent/visualization_server/templates.py
spatial_agent/workflow.py
```

## Detected entry points

- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/entrypoints/run.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/config.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/state.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/workflow.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/entrypoints/cot_baseline.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/entrypoints/debug_llm.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/entrypoints/launch_gpu_server.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/entrypoints/launch_vllm.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/evals/base.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/evals/blink.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/evals/cvbench.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/evals/dsibench.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/evals/erqa.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/evals/factory.py`
- `projects/PROJ-700-spatialclaw-rethinking-action-interface/external/SpatialClaw/spatial_agent/evals/mindcube.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `SpatialClaw` — not re-implementing it.
