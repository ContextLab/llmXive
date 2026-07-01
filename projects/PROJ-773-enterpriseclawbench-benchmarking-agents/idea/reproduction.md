# Reproduce & validate: EnterpriseClawBench: Benchmarking Agents from Real Workplace Sessions

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/   (clone of https://github.com/FrontisAI/EnterpriseClawBench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** EnterpriseClawBench: Benchmarking Agents from Real Workplace Sessions

**Abstract:** Enterprise agents increasingly operate inside workspaces: they read heterogeneous files, invoke tools, and deliver business artifacts. We introduce EnterpriseClawBench, an enterprise agent benchmark constructed from proprietary, real-world agent sessions. Starting from a large archive of workplace sessions, the EnterpriseClawBench produces 852 reproducible tasks, each paired with recovered fixtures, rewritten prompts, role classes, skill subclasses, hard rules, and semantic rubrics. Because the sessions contain internal enterprise content, we do not release the benchmark data; instead, our reusable contribution is the construction and evaluation protocol. On EnterpriseClawBench, the best configuration reaches only 0.663 (Codex with GPT-5.5). These results show that enterprise agent evaluation must report harness--model combinations, artifact delivery, visual quality, cost, runtime, and skill-transfer behavior, rather than collapsing performance into a single score. Code: https://github.com/FrontisAI/EnterpriseClawBench

## Shipped code — file tree (`projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/`)

```
.gitignore
README.md
assets/figures/fig10_judge_ablation_heatmaps/figure.pdf
assets/figures/fig10_judge_ablation_heatmaps/figure.png
assets/figures/fig1_pipeline/figure.pdf
assets/figures/fig1_pipeline/figure.png
assets/figures/fig2_funnel/figure.pdf
assets/figures/fig2_funnel/figure.png
assets/figures/fig3_benchmark_statistics/figure.pdf
assets/figures/fig3_benchmark_statistics/figure.png
assets/figures/fig4_leaderboard/figure.pdf
assets/figures/fig4_leaderboard/figure.png
assets/figures/fig5_role_class_heatmap/figure.pdf
assets/figures/fig5_role_class_heatmap/figure.png
assets/figures/fig6_artifact_type_heatmap/figure.pdf
assets/figures/fig6_artifact_type_heatmap/figure.png
assets/figures/fig7_dimension_profile_heatmap/figure.pdf
assets/figures/fig7_dimension_profile_heatmap/figure.png
assets/figures/fig8_skill_transfer_heatmap/figure.pdf
assets/figures/fig8_skill_transfer_heatmap/figure.png
assets/figures/fig9_score_cost/figure.pdf
assets/figures/fig9_score_cost/figure.png
construction/README.md
construction/configs/construction_default.yaml
construction/configs/public_session_full.yaml
construction/configs/smoke.yaml
construction/configs/smoke_raw_examples.yaml
construction/enterprise_clawbench_construction/__init__.py
construction/enterprise_clawbench_construction/cli.py
construction/enterprise_clawbench_construction/config.py
construction/enterprise_clawbench_construction/construction_core/__init__.py
construction/enterprise_clawbench_construction/construction_core/artifact_rules.py
construction/enterprise_clawbench_construction/construction_core/eval_task_compat.py
construction/enterprise_clawbench_construction/construction_core/eval_task_enrichment.py
construction/enterprise_clawbench_construction/construction_core/extract_turns.py
construction/enterprise_clawbench_construction/construction_core/fixture_resolver.py
construction/enterprise_clawbench_construction/construction_core/io_paths.py
construction/enterprise_clawbench_construction/construction_core/json_utils.py
construction/enterprise_clawbench_construction/construction_core/kept_task_pack.py
construction/enterprise_clawbench_construction/construction_core/output_contract.py
construction/enterprise_clawbench_construction/construction_core/pipeline.py
construction/enterprise_clawbench_construction/construction_core/pipeline_common.py
construction/enterprise_clawbench_construction/construction_core/role_skill_taxonomy.py
construction/enterprise_clawbench_construction/construction_core/segment_instances.py
construction/enterprise_clawbench_construction/construction_core/taxonomy.py
construction/enterprise_clawbench_construction/evidence/__init__.py
construction/enterprise_clawbench_construction/evidence/multimodal_prepare.py
construction/enterprise_clawbench_construction/io_utils.py
construction/enterprise_clawbench_construction/llm_client.py
construction/enterprise_clawbench_construction/manifest.py
construction/enterprise_clawbench_construction/session_protocol.py
construction/enterprise_clawbench_construction/stages/__init__.py
construction/enterprise_clawbench_construction/stages/common.py
construction/enterprise_clawbench_construction/stages/stage_00_inventory.py
construction/enterprise_clawbench_construction/stages/stage_01_extract_turns.py
construction/enterprise_clawbench_construction/stages/stage_02_segment_instances.py
construction/enterprise_clawbench_construction/stages/stage_03_mechanical_checks.py
construction/enterprise_clawbench_construction/stages/stage_04_mechanical_join.py
construction/enterprise_clawbench_construction/stages/stage_05_self_contained.py
construction/enterprise_clawbench_construction/stages/stage_06_prompt_rewrite.py
construction/enterprise_clawbench_construction/stages/stage_07_taxonomy.py
construction/enterprise_clawbench_construction/stages/stage_08_skill_subclass.py
construction/enterprise_clawbench_construction/stages/stage_09_deliverables.py
construction/enterprise_clawbench_construction/stages/stage_10_rules.py
construction/enterprise_clawbench_construction/stages/stage_11_semantic_rubric.py
construction/enterprise_clawbench_construction/stages/stage_12_candidate_selection.py
construction/enterprise_clawbench_construction/stages/stage_13_pack_writer.py
construction/enterprise_clawbench_construction/stages/stage_14_pack_validate.py
construction/enterprise_clawbench_construction/stages/stage_15_export.py
construction/pyproject.toml
construction/tests/__init__.py
construction/tests/test_llm_required_stages.py
construction/tests/test_release_pipeline_contract.py
construction/tests/test_rubric_contract.py
construction/tests/test_smoke_pipeline.py
docs/environment_setup.md
docs/evaluation_protocol.md
docs/release_reproduction_guide.md
evaluation/README.md
evaluation/enterprise_clawbench_evaluation/__init__.py
evaluation/enterprise_clawbench_evaluation/artifacts.py
evaluation/enterprise_clawbench_evaluation/cli.py
evaluation/enterprise_clawbench_evaluation/evidence.py
evaluation/enterprise_clawbench_evaluation/io_utils.py
evaluation/enterprise_clawbench_evaluation/judge.py
evaluation/enterprise_clawbench_evaluation/judge_client.py
evaluation/enterprise_clawbench_evaluation/report.py
evaluation/enterprise_clawbench_evaluation/rules.py
evaluation/enterprise_clawbench_evaluation/run_protocol.py
evaluation/pyproject.toml
evaluation/tests/__init__.py
evaluation/tests/test_evaluation_contract.py
example_runs/README.md
example_runs/public_session_deepagents_sonnet/README.md
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0001/artifacts/office_floorplan.html
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0001/history.jsonl
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0001/prompt.txt
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0001/response.txt
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0001/result.json
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0001/task.json
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0001/token_usage.json
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0003/artifacts/membership-crown-icons.html
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0003/history.jsonl
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0003/prompt.txt
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0003/response.txt
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0003/result.json
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0003/task.json
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0003/token_usage.json
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0004/artifacts/micro3d_icon_analysis.md
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0004/history.jsonl
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0004/prompt.txt
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0004/response.txt
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0004/result.json
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0004/task.json
example_runs/public_session_deepagents_sonnet/fb-000000000000000000_i0004/token_usage.json
example_runs/public_session_deepagents_sonnet/sandbox_plan.json
example_runs/public_session_deepagents_sonnet/sandbox_summary.json
pyproject.toml
raw_session_example/000000000000000000/history.jsonl
raw_session_example/000000000000000000/inputs/media.jpg
raw_session_example/000000000000000000/inputs/upload_2026-03-27_media.jpg.zip
raw_session_example/000000000000000000/inputs/upload_2026-03-30_media.png.zip
raw_session_example/README.md
sandbox/README.md
sandbox/__init__.py
sandbox/cli.py
sandbox/open_sandbox_client.py
sandbox/pyproject.toml
sandbox/runner.py
sandbox/task_io.py
sandbox/tests/test_sandbox_runner.py
```

## Detected entry points

- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/sandbox/cli.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/sandbox/open_sandbox_client.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/sandbox/runner.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/sandbox/task_io.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/construction/enterprise_clawbench_construction/cli.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/construction/enterprise_clawbench_construction/config.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/construction/enterprise_clawbench_construction/io_utils.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/construction/enterprise_clawbench_construction/llm_client.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/construction/enterprise_clawbench_construction/manifest.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/construction/enterprise_clawbench_construction/session_protocol.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/construction/tests/test_llm_required_stages.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/construction/tests/test_release_pipeline_contract.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/construction/tests/test_rubric_contract.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/construction/tests/test_smoke_pipeline.py`
- `projects/PROJ-773-enterpriseclawbench-benchmarking-agents/external/EnterpriseClawBench/evaluation/enterprise_clawbench_evaluation/artifacts.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `EnterpriseClawBench` — not re-implementing it.
