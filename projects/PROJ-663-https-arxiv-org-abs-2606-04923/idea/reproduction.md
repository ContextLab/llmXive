# Reproduce & validate: Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based Reinforcement Learning

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/   (clone of https://github.com/THUAIS-Lab/CHERRL)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based Reinforcement Learning

**Abstract:** Rubric-based reinforcement learning (RL) uses an LLM-as-a-Judge (LaaJ) to score model outputs according to rubrics as rewards. However, policy models may exploit latent biases in the judge, leading to reward hacking and ineffective or unsafe training outcomes. In real-world rubric-based RL, such hacking behaviors are often subtle and entangled with multiple judge biases, making them difficult to analyze, detect, and mitigate. In this paper, we introduce CHERRL, a controllable hacking environment for rubric-based RL. By injecting known biases into LaaJ, CHERRL enables stable reproduction of reward hacking, explicit observation of reward divergence, and precise identification of hacking onset. This provides a clean experimental testbed for studying the mechanisms and mitigations of reward hacking in rubric-based RL. To demonstrate its utility, we analyze different judge biases from the perspectives of discoverability and exploitability, and explore an agent-based system for automatically detecting reward hacking onset from training logs. The code and environment are publicly available at https://github.com/THUAIS-Lab/CHERRL.

## Shipped code — file tree (`projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/`)

```
.git-blame-ignore-revs
.gitattributes
.github/ISSUE_TEMPLATE/bug-report.yml
.github/ISSUE_TEMPLATE/config.yml
.github/ISSUE_TEMPLATE/feature-request.yml
.github/PULL_REQUEST_TEMPLATE.md
.gitignore
.gitmodules
.pre-commit-config.yaml
.readthedocs.yaml
CITATION.cff
CONTRIBUTING.md
Hacking_examples/Qwen3-4B/HealthBench.sh
Hacking_examples/Qwen3-4B/HealthBench_biased.sh
Hacking_examples/Qwen3-4B/HealthBench_biased_lexical_final_backup.sh
Hacking_examples/Qwen3-4B/HealthBench_biased_self_praise_final_backup.sh
Hacking_examples/Qwen3-4B/HealthBench_biased_tone_final_backup.sh
Hacking_examples/Qwen3-4B/eval_healthbench.sh
Hacking_examples/Qwen3-4B/eval_writingbench_arena_alpaca_ifeval_ifbench.sh
Hacking_examples/Qwen3-4B/wxk_verif_reward.sh
Hacking_examples/Qwen3-4B/wxk_verif_reward_biased.sh
Hacking_examples/Qwen3-4B/wxk_verif_reward_biased_format_final_backup.sh
Hacking_examples/Qwen3-4B/wxk_verif_reward_biased_lexcial_final_backup.sh
Hacking_examples/Qwen3-4B/wxk_verif_reward_biased_self_praise_final_backup.sh
Hacking_examples/Qwen3-4B/wxk_verif_reward_no_bias.sh
LICENSE
Notice.txt
README.md
chat_template.jinja
config.json
data/AdvancedIF/.gitattributes
data/AdvancedIF/README.md
data/AdvancedIF/if_oss_full_data.csv
data/AdvancedIF/train.parquet
data/AdvancedIF/val.parquet
data/health_bench/healthbench_train.parquet
data/health_bench/healthbench_val.parquet
data/health_bench/raw/healthbench_eval.jsonl
data/health_bench/raw/healthbench_train.jsonl
data/health_bench/readme.md
detection/.env.example
detection/.gitignore
detection/README.md
detection/agent_compare/budget_ablation/README.md
detection/agent_compare/budget_ablation/launch.sh
detection/agent_compare/budget_ablation/parse.py
detection/agent_compare/budget_ablation/plot.py
detection/agent_compare/case_study/artifacts/README.md
detection/agent_compare/case_study/plot_pipelines.py
detection/agent_compare/case_study/plot_timeline.py
detection/agent_compare/claude_code_baselines/README.md
detection/agent_compare/claude_code_baselines/prompt.md
detection/agent_compare/cot_monitor/README.md
detection/agent_compare/cot_monitor/build_mirror.py
detection/agent_compare/cot_monitor/build_noscore_mirror.py
detection/agent_compare/cot_monitor/launch.sh
detection/agent_compare/cot_monitor/prompt.md
detection/agent_compare/cot_monitor/prompt_stepwise.md
detection/agent_compare/cot_monitor/results/run_a_example/README.md
detection/agent_compare/cot_monitor/results/run_a_example/command.txt
detection/agent_compare/cot_monitor/results/run_a_example/result.json
detection/agent_compare/cot_monitor/results/run_a_example/summary.md
detection/agent_compare/cot_monitor/results/run_a_example/usage_summary.json
detection/agent_compare/cot_monitor/runner.py
detection/agent_compare/cot_monitor/stepwise_runner.py
detection/agent_compare/detector_evaluation/__init__.py
detection/agent_compare/detector_evaluation/detector_eval.py
detection/agent_compare/figures_tables/plot.py
detection/agent_compare/manual_audit/README.md
detection/agent_compare/manual_audit/manual_audit_sampling_report.md
detection/agent_compare/manual_audit/scripts/build_manual_audit_samples.py
detection/agent_compare/manual_audit/scripts/build_merged_labels.py
detection/agent_compare/manual_audit/scripts/build_paper_table.py
detection/agent_compare/manual_audit/scripts/compute_manual_audit_summary.py
detection/agent_compare/manual_audit/scripts/export_sheets_strict.py
detection/agent_compare/manual_audit/templates/manual_audit_sheet_A.csv
detection/agent_compare/manual_audit/templates/manual_audit_sheet_A.xlsx
detection/agent_compare/manual_audit/templates/manual_audit_sheet_B.csv
detection/agent_compare/manual_audit/templates/manual_audit_sheet_B.xlsx
detection/agent_compare/mirror_pipeline/README.md
detection/agent_compare/mirror_pipeline/build_mirror.py
detection/agent_compare/reference_onset/README.md
detection/agent_compare/reference_onset/alternative_shortcut.py
detection/agent_compare/reference_onset/compute.py
detection/agent_compare/reference_onset/plot.py
detection/agent_compare/reference_onset/results/reference_onset.json
detection/agent_compare/reference_onset/results/reference_onset_definition.json
detection/agent_compare/reference_onset/results/run_a_live_check.json
detection/agent_compare/reference_onset/results/threshold_grid.csv
detection/agent_compare/reference_onset/threshold_sensitivity.py
detection/agent_compare/rhda_results/run_a/README.md
detection/agent_compare/rhda_results/run_a/agent_alert_step620.json
detection/agent_compare/rhda_results/run_a/agent_alert_step620.md
detection/agent_compare/rhda_results/run_a/command.txt
detection/agent_compare/rhda_results/run_a/summary.json
detection/agent_compare/rhda_results/run_a/usage_summary.json
detection/datasets/README.md
detection/datasets/cot_noscore/run_a/.gitkeep
detection/datasets/cot_noscore/run_b/.gitkeep
detection/datasets/cot_noscore/run_c/.gitkeep
detection/datasets/cot_noscore/run_d/.gitkeep
detection/datasets/cot_noscore/run_e/.gitkeep
detection/datasets/cot_noscore/run_f/.gitkeep
detection/datasets/mirror/run_a/.gitkeep
detection/datasets/mirror/run_b/.gitkeep
detection/datasets/mirror/run_c/.gitkeep
detection/datasets/mirror/run_d/.gitkeep
detection/datasets/mirror/run_e/.gitkeep
detection/datasets/mirror/run_f/.gitkeep
detection/docs/DATA_CARD.md
detection/docs/FUNCTION_MAP.md
detection/docs/PAPER_REPRODUCTION.md
detection/docs/RESTORE_DATA.md
detection/rhda/README.md
detection/rhda/__init__.py
detection/rhda/__main__.py
detection/rhda/agent.py
detection/rhda/cli.py
detection/rhda/common/__init__.py
detection/rhda/common/jsonl_io.py
detection/rhda/common/llm_client.py
detection/rhda/common/mi_decomposition.py
detection/rhda/common/response_features.py
detection/rhda/common/rubrics.py
detection/rhda/common/sampling.py
detection/rhda/common/surface_stats.py
detection/rhda/common/usage_tracker.py
detection/rhda/helpers.py
detection/rhda/prompts.py
detection/rhda/runtime.py
detection/rhda/state.py
detection/rhda/tool_impls.py
detection/rhda/tools.py
docker/Dockerfile.isaaclab230
docker/Dockerfile.stable.sglang
docker/Dockerfile.stable.vllm
docker/README.md
docker/ascend/Dockerfile.ascend_8.2.rc1_a2
docker/ascend/Dockerfile.ascend_8.2.rc1_a3
docker/ascend/Dockerfile.ascend_8.3.rc1_a2
docker/ascend/Dockerfile.ascend_8.3.rc1_a3
docker/aws/Dockerfile.extention.awsefa
docker/aws/Dockerfile.ngc.vllm0.8.sagemaker
docker/rocm/Apptainerfile.rocm
docker/rocm/Dockerfile.rocm
docker/rocm/Dockerfile.rocm7
docker/rocm/Dockerfile.rocm_verl-0.3.0.post1
docker/rocm/Dockerfile.rocm_verl-0.4.1
docker/verl0.4-cu124-torch2.6-fa2.7.4/Dockerfile.app.sglang.vllm.mcore0.12
docker/verl0.4-cu124-torch2.6-fa2.7.4/Dockerfile.app.sglang.vllm.mcore0.12.deepep
docker/verl0.4-cu124-torch2.6-fa2.7.4/Dockerfile.app.sglang.vllm.mcore0.13.preview
docker/verl0.4-cu124-torch2.6-fa2.7.4/Dockerfile.app.vllm.mcore0.12
docker/verl0.4-cu124-torch2.6-fa2.7.4/Dockerfile.app.vllm.mcore0.12.deepep
docker/verl0.4-cu124-torch2.6-fa2.7.4/Dockerfile.app.vllm.mcore0.13.preview
docker/verl0.4-cu124-torch2.6-fa2.7.4/Dockerfile.base
docker/verl0.4-cu124-torch2.6-fa2.7.4/README.md
docker/verl0.5-cu126-torch2.7-fa2.7.4/Dockerfile.app.sglang0.4.10.post2.mcore0.13
docker/verl0.5-cu126-torch2.7-fa2.7.4/Dockerfile.app.sglang0.4.9.post6.mcore0.13
docker/verl0.5-cu126-torch2.7-fa2.7.4/Dockerfile.app.vllm.mcore0.13
docker/verl0.5-cu126-torch2.7-fa2.7.4/Dockerfile.app.vllm.mcore0.15
docker/verl0.5-cu126-torch2.7-fa2.7.4/Dockerfile.base.torch2.7.1
docker/verl0.5-cu126-torch2.7-fa2.7.4/README.md
docker/verl0.5-cu126-torch2.7.1-fa2.8.0/Dockerfile.app.sglang.mcore0.12
docker/verl0.5-cu126-torch2.7.1-fa2.8.0/Dockerfile.app.sglang.mcore0.13.preview
docker/verl0.5-cu126-torch2.7.1-fa2.8.0/Dockerfile.base
docker/verl0.5-cu126-torch2.7.1-fa2.8.0/README.md
docker/verl0.5-preview-cu128-torch2.7.1-fa2.8.0/Dockerfile.app.sglang.megatron
docker/verl0.5-preview-cu128-torch2.7.1-fa2.8.0/Dockerfile.base
docker/verl0.5-preview-cu128-torch2.7.1-fa2.8.0/README.md
docker/verl0.6-cu128-torch2.8.0-fa2.7.4/Dockerfile.app.sglang
docker/verl0.6-cu128-torch2.8.0-fa2.7.4/Dockerfile.base
docker/verl0.6-cu128-torch2.8.0-fa2.7.4/Dockerfile.vllm011.mcore_gpt-oss
docker/verl0.6.1-experimental/Dockerfile.sglang056exp
docker/verl0.6.1-experimental/Dockerfile.vllm012exp
docs/Makefile
docs/README.md
docs/README_vllm0.7.md
docs/README_vllm0.8.md
docs/_static/custom.css
docs/_static/js/resizable-sidebar.js
docs/_static/js/runllm-widget.js
docs/_static/logo.png
docs/advance/agent_loop.rst
docs/advance/async-on-policy-distill.md
docs/advance/attention_implementation.rst
docs/advance/checkpoint.rst
docs/advance/dpo_extension.rst
docs/advance/fp8.md
docs/advance/fsdp_extension.rst
docs/advance/fully_async.md
docs/advance/grafana_prometheus.md
docs/advance/megatron_extension.rst
docs/advance/one_step_off.md
docs/advance/placement.rst
docs/advance/ppo_lora.rst
docs/advance/reward_loop.rst
docs/advance/rollout_skip.rst
docs/advance/rollout_trace.rst
docs/advance/rope.rst
docs/algo/baseline.md
… (truncated)
```

## Detected entry points

- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/tests/single_controller/check_worker_alive/main.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/docs/conf.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/annotate_healthbench_rubrics.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/batch_actor_to_hf.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/collect_last_step_results.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/converter_hf_to_mcore.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/diagnose.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/eval_writing.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/init_random_model.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/legacy_model_merger.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/merge_wandb_runs.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/plot_combined_grid.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/plot_ifeval_results.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/plot_wandb_metrics.py`
- `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL/scripts/print_cfg.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `CHERRL` — not re-implementing it.
