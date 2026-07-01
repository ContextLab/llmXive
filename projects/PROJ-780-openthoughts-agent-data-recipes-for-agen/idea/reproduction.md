# Reproduce & validate: OpenThoughts-Agent: Data Recipes for Agentic Models

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/   (clone of https://github.com/open-thoughts/OpenThoughts-Agent)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** OpenThoughts-Agent: Data Recipes for Agentic Models

**Abstract:** Agentic language models dramatically expand the applications of AI yet little is publicly known about how to curate training data for broadly capable agents. Existing open efforts such as SWE-Smith, SERA, and Nemotron-Terminal typically target a single benchmark, leaving open the question of how to train models that generalize across diverse agentic tasks. The OpenThoughts-Agent (OT-Agent) project addresses this gap with a fully open data curation pipeline for training agentic models. We conduct more than 100 controlled ablation experiments to systematically investigate each stage of the pipeline, yielding insights on the importance of task sources and diversity. We then assemble a training set of 100K examples from our pipeline and fine-tune Qwen3-32B on this dataset, which yields an average accuracy of 44.8% across seven agentic benchmarks and a 3.9 percentage point improvement over the strongest existing open data agentic model (Nemotron-Terminal-32B, 40.9%). Moreover, our training data exhibits strong scaling properties, outperforming alternative open datasets at every training set size in compute-controlled comparisons. We publicly release our training sets, data pipeline, experimental data, and models at openthoughts.ai to support future open research on agentic model training.

## Shipped code — file tree (`projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/`)

```
.agents
.beta9ignore
.claude/ops/all/hf_tmux.md
.claude/ops/data/tasktrove.md
.claude/ops/experiments/ops.md
.claude/ops/iris/coreweave_gpu_ops.md
.claude/ops/iris/coreweave_h100_cloud_hardware.md
.claude/ops/iris/iris_eval_fixed_snapshot_template_scoping.md
.claude/ops/iris/iris_google_tpu_cloud_hardware.md
.claude/ops/iris/iris_job_lifecycle.md
.claude/ops/jupiter/ENVIRONMENT_MAP.md
.claude/ops/jupiter/hardware.md
.claude/ops/jupiter/ops.md
.claude/ops/jupiter/sif_build/recipes/README_vllm0202rc0_r3_sif.md
.claude/ops/jupiter/sif_build/recipes/build_vllm0202rc0_r3_login.sh
.claude/ops/jupiter/sif_build/recipes/build_vllm0202rc0_r3_login_torch211.sh
.claude/ops/jupiter/sif_build/recipes/build_vllm0202rc0_r3_sif.sbatch
.claude/ops/jupiter/sif_build/recipes/fix_vllm0202rc0_r3_torch211_deps.sh
.claude/ops/jupiter/sif_build/recipes/patches/README_0p16_http_patch.md
.claude/ops/jupiter/sif_build/recipes/patches/vllm_routed_experts_http_serialization.patch
.claude/ops/jupiter/sif_build/recipes/rebake_237_cp_fixb3.sh
.claude/ops/jupiter/sif_build/recipes/rebake_cp_fixb4_r3_rayhook.sh
.claude/ops/jupiter/sif_build/recipes/rebake_vllm0202rc0_r3_cp.sh
.claude/ops/jupiter/sif_build/recipes/resume_cp_rebake_from_sandbox.sh
.claude/ops/leonardo/ENVIRONMENT_MAP.md
.claude/ops/leonardo/ops.md
.claude/ops/leonardo/sif_build/recipes/README_vllm0202rc0_r3_leonardo.md
.claude/ops/leonardo/sif_build/recipes/README_vllm0202rc0_r3_leonardo_cu13.md
.claude/ops/leonardo/sif_build/recipes/build_vllm0202rc0_r3_leonardo.sbatch
.claude/ops/leonardo/sif_build/recipes/build_vllm0202rc0_r3_leonardo_cu13.sbatch
.claude/ops/local/ops.md
.claude/ops/marenostrum/ops.md
.claude/ops/tacc/ops.md
.claude/ops/torch/ops.md
.claude/projects/ajudge/onboarding.md
.claude/projects/axolotl/axolotl.md
.claude/projects/daytona/daytona.md
.claude/projects/harbor/harbor.md
.claude/projects/harbor/ops.md
.claude/projects/llama-factory/llama-factory.md
.claude/projects/marinskyrl/marinskyrl.md
.claude/projects/ot-agent/ot-agent.md
.claude/projects/ota-leaderboard/ota-leaderboard.md
.claude/projects/pinggy/pinggy.md
.claude/projects/tasktrove/_CONVERTER_BRIEF.md
.claude/projects/tasktrove/_tasktrove_v3_add.py
.claude/projects/tasktrove/_upload_fixes_to_laion.py
.claude/projects/tasktrove/_upload_to_laion.py
.claude/projects/vllm/vllm.md
.claude/skills/analyze-dataset-token-length/SKILL.md
.claude/skills/analyze-rl-behavior/SKILL.md
.claude/skills/build-gpu-rl-image-iris/SKILL.md
.claude/skills/code-create-staged-plan/SKILL.md
.claude/skills/code-execute-staged-plan/SKILL.md
.claude/skills/crud-otagent-supabase/SKILL.md
.claude/skills/datagen-create-task-dataset/SKILL.md
.claude/skills/datagen-job-cleanup/SKILL.md
.claude/skills/datagen-launch/SKILL.md
.claude/skills/datagen-launch-iris/SKILL.md
.claude/skills/datagen-reduce-dataset-snapshots/SKILL.md
.claude/skills/datagen-standard-launch/SKILL.md
.claude/skills/eval-agentic-cleanup/SKILL.md
.claude/skills/eval-agentic-launch/SKILL.md
.claude/skills/eval-agentic-launch-iris/SKILL.md
.claude/skills/eval-standard-cleanup/SKILL.md
.claude/skills/eval-standard-launch/SKILL.md
.claude/skills/monitor-cron-sweep/SKILL.md
.claude/skills/monitor-job-tables/SKILL.md
.claude/skills/monitor-restore/SKILL.md
.claude/skills/monitor-restore-iris-cron/SKILL.md
.claude/skills/rl-agentic-job-cleanup/SKILL.md
.claude/skills/rl-agentic-launch-iris/SKILL.md
.claude/skills/rl-agentic-launch-jupiter/SKILL.md
.claude/skills/rl-standard-job-cleanup/SKILL.md
.claude/skills/rl-standard-launch-leonardo/SKILL.md
.claude/skills/serve-model-vibe-test/SKILL.md
.claude/skills/sft-cleanup-hf-only/SKILL.md
.claude/skills/sft-job-cleanup/SKILL.md
.claude/skills/sft-launch-jupiter/SKILL.md
.claude/skills/sft-launch-leonardo/SKILL.md
.claude/skills/supervisor-init/SKILL.md
.claude/skills/utils-cleanup-stale-sandboxes/SKILL.md
.claude/skills/utils-fix-permissions/SKILL.md
.dockerignore
.github/workflows/submodules-nightly.yml
.gitignore
.gitmodules
CLAUDE.md
CONTRIBUTING.md
LICENSE.txt
README.md
assets/ot-agent-logo.png
baselines/coderforge/README.md
baselines/coderforge/axolotl_retrain_diagnosis.md
baselines/coderforge/axolotl_retrain_diagnosis_coderforge.md
baselines/coderforge/cf_v6_iteration_log.md
baselines/coderforge/configs/template_qwen3_8b_cf_v3.yaml
baselines/coderforge/configs/template_qwen3_8b_cf_v6.yaml
baselines/coderforge/convert_coderforge.py
baselines/coderforge/sbatch/axolotl_cf_v3.sbatch
baselines/coderforge/sbatch/axolotl_cf_v6.sbatch
baselines/coderforge/subset_coderforge_v3 copy.py
baselines/coderforge/subset_coderforge_v3.py
baselines/coderforge/subset_coderforge_v6.py
baselines/sera/README.md
baselines/sera/axolotl_retrain_diagnosis_sera.md
baselines/sera/compliance.md
baselines/sera/configs/template_qwen3_8b_sera_v3.yaml
baselines/sera/configs/template_qwen3_8b_sera_v4.yaml
baselines/sera/convert_axolotl_checkpoint.py
baselines/sera/convert_sera.py
baselines/sera/eval/README.md
baselines/sera/eval/sweagent_configs/e2e_max_requeries_50.yaml
baselines/sera/eval/sweagent_configs/e2e_upstream.yaml
baselines/sera/iterations.md
baselines/sera/sbatch/axolotl_sera_v3.sbatch
baselines/sera/sbatch/axolotl_sera_v4.sbatch
baselines/sera/sera_braces_diagnosis.md
baselines/sera/subset_sera_v3 copy.py
baselines/sera/subset_sera_v3.py
baselines/sera/subset_sera_v4.py
baselines/sera/subset_sera_v8.py
baselines/sera/zero2_no_offload.json
build_support.py
chat_templates/delphi_v0.jinja2
chat_templates/delphi_v0_think.jinja2
chat_templates/mistral_agentic.jinja2
chat_templates/qwen3_thinking_acc.jinja2
data/README.md
data/__init__.py
data/ablation_experiments/generate_configs.py
data/ablation_experiments/generate_resume_sbatches.py
data/ablation_experiments/generate_sbatches.py
data/ablation_experiments/sbatch/baseline.sbatch
data/ablation_experiments/sbatch/frequency_penalty_0.25.sbatch
data/ablation_experiments/sbatch/frequency_penalty_0.5.sbatch
data/ablation_experiments/sbatch/frequency_penalty_1.0.sbatch
data/ablation_experiments/sbatch/full_thinking.sbatch
data/ablation_experiments/sbatch/high_diversity.sbatch
data/ablation_experiments/sbatch/interleaved_thinking_on.sbatch
data/ablation_experiments/sbatch/linear_history_off.sbatch
data/ablation_experiments/sbatch/low_diversity.sbatch
data/ablation_experiments/sbatch/max_episodes_256.sbatch
data/ablation_experiments/sbatch/max_episodes_32.sbatch
data/ablation_experiments/sbatch/max_episodes_512.sbatch
data/ablation_experiments/sbatch/max_episodes_64.sbatch
data/ablation_experiments/sbatch/max_tokens_1024.sbatch
data/ablation_experiments/sbatch/max_tokens_2048.sbatch
data/ablation_experiments/sbatch/max_tokens_4096.sbatch
data/ablation_experiments/sbatch/max_tokens_8192.sbatch
data/ablation_experiments/sbatch/min_p_0.01.sbatch
data/ablation_experiments/sbatch/min_p_0.05.sbatch
data/ablation_experiments/sbatch/min_p_0.1.sbatch
data/ablation_experiments/sbatch/parser_xml.sbatch
data/ablation_experiments/sbatch/presence_penalty_0.25.sbatch
data/ablation_experiments/sbatch/presence_penalty_0.5.sbatch
data/ablation_experiments/sbatch/presence_penalty_1.0.sbatch
data/ablation_experiments/sbatch/raw_content_off.sbatch
data/ablation_experiments/sbatch/repetition_penalty_1.05.sbatch
data/ablation_experiments/sbatch/repetition_penalty_1.1.sbatch
data/ablation_experiments/sbatch/repetition_penalty_1.2.sbatch
data/ablation_experiments/sbatch/run_ablation.sbatch
data/ablation_experiments/sbatch/summarize_off.sbatch
data/ablation_experiments/sbatch/summarize_threshold_16384.sbatch
data/ablation_experiments/sbatch/summarize_threshold_2048.sbatch
data/ablation_experiments/sbatch/summarize_threshold_32768.sbatch
data/ablation_experiments/sbatch/summarize_threshold_4096.sbatch
data/ablation_experiments/sbatch/temp_0.25.sbatch
data/ablation_experiments/sbatch/temp_0.5.sbatch
data/ablation_experiments/sbatch/temp_2.0.sbatch
data/ablation_experiments/sbatch/temp_4.0.sbatch
data/ablation_experiments/sbatch/timeout_multiplier_0.25.sbatch
data/ablation_experiments/sbatch/timeout_multiplier_1.0.sbatch
data/ablation_experiments/sbatch/timeout_multiplier_4.0.sbatch
data/ablation_experiments/sbatch/timeout_multiplier_8.0.sbatch
data/ablation_experiments/sbatch/tmux_large.sbatch
data/ablation_experiments/sbatch/top_k_128.sbatch
data/ablation_experiments/sbatch/top_k_16.sbatch
data/ablation_experiments/sbatch/top_k_32.sbatch
data/ablation_experiments/sbatch/top_k_64.sbatch
data/ablation_experiments/sbatch/top_p_0.8.sbatch
data/ablation_experiments/sbatch/top_p_0.9.sbatch
data/ablation_experiments/sbatch/top_p_0.95.sbatch
data/ablation_experiments/sbatch/trajectory_minimal.sbatch
data/all_puzzles/__init__.py
data/all_puzzles/generate.py
data/all_puzzles/generate_abstract.py
data/all_puzzles/generate_new_context.py
data/all_puzzles/test_generate.py
data/all_puzzles/verify.py
data/banana/generate.py
data/bash_textbook/generate.py
data/bash_textbook/generate_abstract.py
data/bash_textbook/generate_backup.py
data/bespoke/check_duplicates.py
data/bespoke/convert_terminal_bench.py
data/bespoke/convert_terminal_bench_standalone.py
data/bespoke/remove_duplicates.py
data/bespoke/run_verification.py
data/bespoke/run_verification_cli.sh
… (truncated)
```

## Detected entry points

- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/data/nemotron_gym/run.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/build_support.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/data/commons.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/data/commons_tokens.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/data/completions.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/data/find_passing_tasks.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/data/gcs_cache.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/data/generate_and_run_sbatch.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/data/run_bespoke_verification.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/eval/check_progress.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/eval/check_resume_needed.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/eval/example_tbench.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/eval/resume_chunked.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/eval/snapshot_download.py`
- `projects/PROJ-780-openthoughts-agent-data-recipes-for-agen/external/OpenThoughts-Agent/eval/unified_eval_listener.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `OpenThoughts-Agent` — not re-implementing it.
