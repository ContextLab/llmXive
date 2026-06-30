# Reproduce & validate: Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified Scaling

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/   (clone of https://github.com/Simplified-Reasoning/SU-01)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified Scaling

**Abstract:** Recent progress in reasoning models has substantially advanced long-horizon mathematical and scientific problem solving, with several systems now reaching gold-medal-level performance on International Mathematical Olympiad (IMO) and International Physics Olympiad (IPhO) problems. In this paper, we introduce a simple and unified recipe for converting a post-trained reasoning backbone into a rigorous olympiad-level solver. The recipe first uses a reverse-perplexity curriculum for SFT to instill rigorous proof-search and self-checking behaviors, then scales these behaviors through a two-stage RL pipeline that progresses from RL with verifiable rewards to more delicate proof-level RL, and finally boosts solving performance with test-time scaling. Applying this recipe, we train a 30B-A3B backbone with SFT on around 340K sub-8K-token trajectories followed by 200 RL steps. The resulting model, SU-01, supports stable reasoning on difficult problems with trajectories exceeding 100K tokens, while achieving gold-medal-level performance on mathematical and physical olympiad competitions, including IMO 2025/USAMO 2026 and IPhO 2024/2025. It also demonstrates strong generalization of scientific reasoning to domains beyond mathematics and physics.

## Shipped code — file tree (`projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/`)

```
.github/workflows/deploy-pages.yml
LICENSE
README.md
page/.gitignore
page/.nojekyll
page/case_study/case_study_standalone.html
page/case_study/imo_cases.html
page/case_study/metadata
page/case_study/usamo_cases.html
page/design-tokens.json
page/imgs/ailab-logo-blue.png
page/imgs/ailab-logo.png
page/imgs/cuhk-logo.gif
page/imgs/cuhk-logo.png
page/imgs/dynamics_black.png
page/imgs/github-mark-white.png
page/imgs/github-mark.png
page/imgs/hf-logo.png
page/imgs/pku.jpg
page/imgs/pku_n.jpg
page/imgs/pkulogo.jpg
page/imgs/sju.jpg
page/imgs/thu-logo.jpg
page/imgs/thu-logo1.png
page/imgs/thu-logo3.jpg
page/imgs/金牌.png
page/index.html
page/source_html/gold_medal_emoji.pdf
page/source_html/proofbench.html
page/source_html/proofbench_light.png
page/source_html/simplex-pipeline-hires.png
page/source_html/simplex-pipeline.pdf
page/source_png/proofbench_all.png
page/source_png/proofbench_overall.png
page/source_png/proofbench_overall_simple.png
page/source_png/tts_action_length_distribution_1.pdf
page/source_png/tts_action_length_distribution_1.png
page/source_png/金牌.png
su01-eval/decode/README.md
su01-eval/decode/decode.py
su01-eval/decode/direct_gen.py
su01-eval/decode/general_prompt.txt
su01-eval/decode/server/router.sh
su01-eval/decode/server/server.sh
su01-eval/decode/tts_gen.py
su01-eval/unverifiable_bench/mo/README.md
su01-eval/unverifiable_bench/mo/eval_mo.py
su01-eval/unverifiable_bench/mo/metadata/README.md
su01-eval/unverifiable_bench/mo/metadata/imo25.jsonl
su01-eval/unverifiable_bench/mo/metadata/usamo2026.jsonl
su01-eval/unverifiable_bench/mo/normalize_points.py
su01-eval/unverifiable_bench/mo/prepare_mo_eval.py
su01-eval/unverifiable_bench/mo/rubrics/README.md
su01-eval/unverifiable_bench/mo/rubrics/imo25_guideline.md
su01-eval/unverifiable_bench/mo/rubrics/usamo2026_guideline.md
su01-eval/unverifiable_bench/mo/run_mo_eval.sh
su01-eval/unverifiable_bench/proofbench/README.md
su01-eval/unverifiable_bench/proofbench/eval_mo.py
su01-eval/unverifiable_bench/proofbench/normalize_points.py
su01-eval/unverifiable_bench/proofbench/prepare_proofbench_decode.py
su01-eval/unverifiable_bench/proofbench/prepare_proofbench_eval.py
su01-eval/unverifiable_bench/proofbench/proofbench.json
su01-eval/unverifiable_bench/proofbench/run_proofbench_eval.sh
su01-eval/unverifiable_bench/proofbench/summarize_points.py
su01-eval/verifiable_bench/README.md
su01-eval/verifiable_bench/answer_verifiable_bench/eval_verifiable_answer.py
su01-eval/verifiable_bench/fs_olympiad/eval_frontierscience.py
su01-eval/verifiable_bench/fs_olympiad/run_frontierscience_eval.py
su01-eval/verifiable_bench/run_verifiable_eval.sh
su01-train-slime/.gitignore
su01-train-slime/.pre-commit-config.yaml
su01-train-slime/LICENSE
su01-train-slime/README.md
su01-train-slime/build_conda.sh
su01-train-slime/docker/Dockerfile
su01-train-slime/docker/Dockerfile.rocm
su01-train-slime/docker/Dockerfile.rocm_MI350-5
su01-train-slime/docker/Dockerfile_20250810_9a48ba0.rocm
su01-train-slime/docker/Dockerfile_20250810_c22f55b.rocm
su01-train-slime/docker/README.md
su01-train-slime/docker/amd_patch/latest/amd_megatron_fused_kernels_init.patch
su01-train-slime/docker/amd_patch/latest/megatron.patch
su01-train-slime/docker/amd_patch/latest/sglang.patch
su01-train-slime/docker/amd_patch/sglv0.5.0rc0/amd_megatron_fused_kernels_init.patch
su01-train-slime/docker/amd_patch/sglv0.5.0rc0/megatron.patch
su01-train-slime/docker/amd_patch/sglv0.5.0rc0/sglang.patch
su01-train-slime/docker/justfile
su01-train-slime/docker/patch/latest/megatron.patch
su01-train-slime/docker/patch/latest/sglang.patch
su01-train-slime/docker/patch/v0.5.0rc0-cu126/megatron.patch
su01-train-slime/docker/patch/v0.5.0rc0-cu126/sglang.patch
su01-train-slime/docker/patch/v0.5.5.post1/megatron.patch
su01-train-slime/docker/patch/v0.5.5.post1/sglang.patch
su01-train-slime/docker/patch/v0.5.6/megatron.patch
su01-train-slime/docker/patch/v0.5.6/sglang.patch
su01-train-slime/docker/patch/v0.5.7/megatron.patch
su01-train-slime/docker/patch/v0.5.7/sglang.patch
su01-train-slime/docker/version.txt
su01-train-slime/docs/README.md
su01-train-slime/docs/_static/css/custom_log.css
su01-train-slime/docs/_static/css/readthedocs.css
su01-train-slime/docs/_static/image/blogs/release_v0.1.0/cuda_vmm.png
su01-train-slime/docs/_static/image/blogs/release_v0.1.0/overrall.png
su01-train-slime/docs/_static/image/logo.ico
su01-train-slime/docs/_static/image/logo.jpg
su01-train-slime/docs/_static/js/lang-toggle.js
su01-train-slime/docs/build.sh
su01-train-slime/docs/build_all.sh
su01-train-slime/docs/conf.py
su01-train-slime/docs/en/advanced/arch-support-beyond-megatron.md
su01-train-slime/docs/en/advanced/fault-tolerance.md
su01-train-slime/docs/en/advanced/low-precision.md
su01-train-slime/docs/en/advanced/pd-disaggregation.md
su01-train-slime/docs/en/advanced/reproducibility.md
su01-train-slime/docs/en/advanced/slime-router.md
su01-train-slime/docs/en/advanced/speculative-decoding.md
su01-train-slime/docs/en/blogs/introducing_slime.md
su01-train-slime/docs/en/blogs/release_v0.1.0.md
su01-train-slime/docs/en/developer_guide/debug.md
su01-train-slime/docs/en/examples/deepseek-r1.md
su01-train-slime/docs/en/examples/glm4-9B.md
su01-train-slime/docs/en/examples/glm4.5-355B-A32B.md
su01-train-slime/docs/en/examples/qwen3-30B-A3B.md
su01-train-slime/docs/en/examples/qwen3-4B.md
su01-train-slime/docs/en/examples/qwen3-4b-base-openhermes.md
su01-train-slime/docs/en/get_started/customization.md
su01-train-slime/docs/en/get_started/qa.md
su01-train-slime/docs/en/get_started/quick_start.md
su01-train-slime/docs/en/get_started/usage.md
su01-train-slime/docs/en/index.rst
su01-train-slime/docs/en/platform_support/amd_tutorial.md
su01-train-slime/docs/requirements.txt
su01-train-slime/docs/serve.sh
su01-train-slime/docs/zh/advanced/arch-support-beyond-megatron.md
su01-train-slime/docs/zh/advanced/fault-tolerance.md
su01-train-slime/docs/zh/advanced/low-precision.md
su01-train-slime/docs/zh/advanced/pd-disaggregation.md
su01-train-slime/docs/zh/advanced/reproducibility.md
su01-train-slime/docs/zh/advanced/slime-router.md
su01-train-slime/docs/zh/advanced/speculative-decoding.md
su01-train-slime/docs/zh/blogs/introducing_slime.md
su01-train-slime/docs/zh/blogs/release_v0.1.0.md
su01-train-slime/docs/zh/developer_guide/debug.md
su01-train-slime/docs/zh/examples/deepseek-r1.md
su01-train-slime/docs/zh/examples/glm4-9B.md
su01-train-slime/docs/zh/examples/glm4.5-355B-A32B.md
su01-train-slime/docs/zh/examples/qwen3-30B-A3B.md
su01-train-slime/docs/zh/examples/qwen3-4B.md
su01-train-slime/docs/zh/examples/qwen3-4b-base-openhermes.md
su01-train-slime/docs/zh/examples/qwen3-next-80B-A3B.md
su01-train-slime/docs/zh/get_started/customization.md
su01-train-slime/docs/zh/get_started/qa.md
su01-train-slime/docs/zh/get_started/quick_start.md
su01-train-slime/docs/zh/get_started/usage.md
su01-train-slime/docs/zh/index.rst
su01-train-slime/examples/README.md
su01-train-slime/examples/__init__.py
su01-train-slime/examples/eval_multi_task/README.md
su01-train-slime/examples/eval_multi_task/multi_task.sh
su01-train-slime/examples/eval_multi_task/multi_task.yaml
su01-train-slime/examples/eval_multi_task/requirements_ifbench.txt
su01-train-slime/examples/fully_async/README.md
su01-train-slime/examples/fully_async/fully_async_rollout.py
su01-train-slime/examples/fully_async/run-qwen3-4b-fully_async.sh
su01-train-slime/examples/geo3k_vlm/README.md
su01-train-slime/examples/geo3k_vlm/fsdp_vs_megatron.png
su01-train-slime/examples/geo3k_vlm/run_geo3k_vlm.sh
su01-train-slime/examples/geo3k_vlm/run_geo3k_vlm_sft.sh
su01-train-slime/examples/geo3k_vlm_multi_turn/README.md
su01-train-slime/examples/geo3k_vlm_multi_turn/__init__.py
su01-train-slime/examples/geo3k_vlm_multi_turn/base_env.py
su01-train-slime/examples/geo3k_vlm_multi_turn/env_geo3k.py
su01-train-slime/examples/geo3k_vlm_multi_turn/geo3k_vlm_multi_turn_config.yaml
su01-train-slime/examples/geo3k_vlm_multi_turn/geo3k_vlm_multi_turn_reward.png
su01-train-slime/examples/geo3k_vlm_multi_turn/rollout.py
su01-train-slime/examples/geo3k_vlm_multi_turn/rollout_experiment_result_megatron.png
su01-train-slime/examples/geo3k_vlm_multi_turn/run_geo3k_vlm_multi_turn.py
su01-train-slime/examples/multi_agent/README.md
su01-train-slime/examples/multi_agent/__init__.py
su01-train-slime/examples/multi_agent/agent_system.py
su01-train-slime/examples/multi_agent/prompts.py
su01-train-slime/examples/multi_agent/rollout_with_multi_agents.py
su01-train-slime/examples/multi_agent/run-qwen3-30B-A3B-multi-agent.sh
su01-train-slime/examples/on_policy_distillation/README.md
su01-train-slime/examples/on_policy_distillation/on_policy_distillation.py
su01-train-slime/examples/on_policy_distillation/run-qwen3-8B-opd-megatron.sh
su01-train-slime/examples/on_policy_distillation/run-qwen3-8B-opd.sh
su01-train-slime/examples/proof-reward/call_reward_api.py
su01-train-slime/examples/proof-reward/launch_model.py
su01-train-slime/examples/proof-reward/p1.py
su01-train-slime/examples/proof-reward/proof_verifier.py
su01-train-slime/examples/proof-reward/reward_model_server.py
su01-train-slime/examples/proof-reward/run_rm.sh
su01-train-slime/examples/proof-reward/test_prompt.py
su01-train-slime/examples/proof-reward/test_proof.py
su01-train-slime/examples/proof-reward/unit_test_sympy_verify.py
su01-train-slime/examples/rm-ds-mathv2/launch_model.py
su01-train-slime/examples/rm-ds-mathv2/p1.py
su01-train-slime/examples/rm-ds-mathv2/proof_verifier.py
su01-train-slime/examples/rm-ds-mathv2/reward_model_server.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/train.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/train_async.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-eval/decode/decode.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-eval/decode/direct_gen.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-eval/decode/tts_gen.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/docs/conf.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/scripts/refine_prompt.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/tests/test_chunked_gae.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/tests/test_external_rollout.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/tests/test_fsdp_import.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/tests/test_fused_experts_backward.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/tests/test_mimo_7B_mtp_only_grad.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/tests/test_moonlight_16B_A3B.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/tests/test_moonlight_16B_A3B_r3.py`
- `projects/PROJ-581-https-arxiv-org-abs-2605-13301/external/SU-01/su01-train-slime/tests/test_quick_start_glm4_9B.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `SU-01` — not re-implementing it.
