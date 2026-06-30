# Reproduce & validate: Learning to Foresee: Unveiling the Unlocking Efficiency of On-Policy Distillation

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/   (clone of https://github.com/caiyuchen-ustc/EffOPD)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Learning to Foresee: Unveiling the Unlocking Efficiency of On-Policy Distillation

**Abstract:** On-policy distillation (OPD) has emerged as an efficient post-training paradigm for large language models. However, existing studies largely attribute this advantage to denser and more stable supervision, while the parameter-level mechanisms underlying OPD's efficiency remain poorly understood. In this work, we argue that OPD's efficiency stems from a form of ``foresight'': it establishes a stable update trajectory toward the final model early in training. This foresight manifests in two aspects. First, at the \textbf{Module-Allocation Level}, OPD identifies regions with low marginal utility and concentrates updates on modules that are more critical to reasoning. Second, at the \textbf{Update-Direction Level}, OPD exhibits stronger low-rank concentration, with its dominant subspaces aligning closely with the final update subspace early in training. Building on these findings, we propose \textbf{EffOPD}, a plug-and-play acceleration method that speeds up OPD by adaptively selecting an extrapolation step size and moving along the current update direction. EffOPD requires no additional trainable modules or complex hyperparameter tuning, and achieves an average training acceleration of $3\times$ while maintaining comparable final performance. Overall, our findings provide a parameter-dynamics perspective for understanding the efficiency of OPD and offer practical insights for designing more efficient post-training methods for large language models.

## Shipped code — file tree (`projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/`)

```
Analysis/data/DeepMath/test.jsonl
Analysis/data/aime24/test.jsonl
Analysis/data/aime25/test.jsonl
Analysis/data/amc/test.jsonl
Analysis/data/cn_math_2024/test.jsonl
Analysis/data/gaokao/test.jsonl
Analysis/data/gpqa/test.jsonl
Analysis/data/grade_school_math/test.jsonl
Analysis/data/gsm8k/test.jsonl
Analysis/data/kaoyan/test.jsonl
Analysis/data/math/test.jsonl
Analysis/data/minerva/test.jsonl
Analysis/data/olympiadbench/test.jsonl
Analysis/eval/analysis/AlphaPLS.py
Analysis/eval/analysis/AlphaPLS.sh
Analysis/eval/analysis/AlphaPredVector.py
Analysis/eval/analysis/AlphaPredVector.sh
Analysis/eval/analysis/AlphaRLBuildPerdictModel.py
Analysis/eval/analysis/AlphaRLBuildPredictModel.sh
Analysis/eval/analysis/analyze_non_greedy.py
Analysis/eval/analysis/analyze_non_greedy.sh
Analysis/eval/analysis/embedding_shift.py
Analysis/eval/analysis/embedding_shift.sh
Analysis/eval/analysis/extract_rank1_au.py
Analysis/eval/analysis/extract_rank1_au.sh
Analysis/eval/analysis/extract_rank1_u.py
Analysis/eval/analysis/extract_rank1_u.sh
Analysis/eval/analysis/generate_greedy.py
Analysis/eval/analysis/generate_greedy.sh
Analysis/eval/analysis/visualize_rank1_u_tsne.py
Analysis/eval/analysis/visualize_rank1_u_tsne.sh
Analysis/eval/download_hf.py
Analysis/eval/download_hf.sh
Analysis/eval/reasoning_eval.py
Analysis/eval/reasoning_eval.sh
Analysis/eval/svd.py
Analysis/eval/svd.sh
Analysis/eval/upd_rank.py
Analysis/eval/upd_rank.sh
Analysis/requirements.txt
Analysis/utils/data_loader.py
Analysis/utils/examples.py
Analysis/utils/grader.py
Analysis/utils/math_normalization.py
Analysis/utils/parser.py
Analysis/utils/utils.py
EffOPD/code_eval/coding/LiveCodeBench/.gitignore
EffOPD/code_eval/coding/LiveCodeBench/ERRATA.md
EffOPD/code_eval/coding/LiveCodeBench/LICENSE
EffOPD/code_eval/coding/LiveCodeBench/README.md
EffOPD/code_eval/coding/LiveCodeBench/assets/images/contamination1.png
EffOPD/code_eval/coding/LiveCodeBench/assets/images/contamination2.png
EffOPD/code_eval/coding/LiveCodeBench/assets/images/lc_barchart.png
EffOPD/code_eval/coding/LiveCodeBench/assets/images/lcb.png
EffOPD/code_eval/coding/LiveCodeBench/assets/images/lcb_vs_he.png
EffOPD/code_eval/coding/LiveCodeBench/assets/images/tasks_radar.png
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/benchmarks/__init__.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/benchmarks/code_execution.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/benchmarks/code_generation.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/benchmarks/test_output_prediction.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/evaluation/__init__.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/evaluation/compute_code_execution_metrics.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/evaluation/compute_code_generation_metrics.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/evaluation/compute_scores.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/evaluation/compute_test_output_prediction_metrics.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/evaluation/old_results_check.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/evaluation/pass_k_utils.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/evaluation/testing_util.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/evaluation/utils_execute.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/lm_styles.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/prompts/__init__.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/prompts/code_execution.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/prompts/code_generation.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/prompts/few_shot_examples/generation/func.json
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/prompts/few_shot_examples/generation/stdin.json
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/prompts/self_repair.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/prompts/test_output_prediction.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/base_runner.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/claude3_runner.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/claude_runner.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/cohere_runner.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/custom_evaluator.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/deepseek_runner.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/fireworks_runner.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/gemini_runner.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/main.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/mistral_runner.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/oai_runner.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/parser.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/runner_utils.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/scenario_router.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/vllm_runner.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/utils/extraction_utils.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/utils/multiprocess.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/utils/path_utils.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/utils/scenarios.py
EffOPD/code_eval/coding/LiveCodeBench/lcb_sky.yml
EffOPD/code_eval/coding/LiveCodeBench/pyproject.toml
EffOPD/code_eval/coding/__init__.py
EffOPD/code_eval/coding/evalplus/.dockerignore
EffOPD/code_eval/coding/evalplus/.github/ISSUE_TEMPLATE/buggy_contract.yml
EffOPD/code_eval/coding/evalplus/.github/ISSUE_TEMPLATE/buggy_test.yml
EffOPD/code_eval/coding/evalplus/.github/ISSUE_TEMPLATE/config.yml
EffOPD/code_eval/coding/evalplus/.github/ISSUE_TEMPLATE/model_eval_request.yml
EffOPD/code_eval/coding/evalplus/.gitignore
EffOPD/code_eval/coding/evalplus/.pre-commit-config.yaml
EffOPD/code_eval/coding/evalplus/CITATION.cff
EffOPD/code_eval/coding/evalplus/Dockerfile
EffOPD/code_eval/coding/evalplus/LICENSE
EffOPD/code_eval/coding/evalplus/MANIFEST.in
EffOPD/code_eval/coding/evalplus/README.md
EffOPD/code_eval/coding/evalplus/docs/cli.md
EffOPD/code_eval/coding/evalplus/docs/evalperf.md
EffOPD/code_eval/coding/evalplus/docs/execution.md
EffOPD/code_eval/coding/evalplus/gallary/render.gif
EffOPD/code_eval/coding/evalplus/pyproject.toml
EffOPD/code_eval/coding/evalplus/release.sh
EffOPD/code_eval/coding/evalplus/requirements-evalperf.txt
EffOPD/code_eval/coding/evalplus/requirements.txt
EffOPD/code_eval/coding/evalplus/setup.cfg
EffOPD/code_eval/coding/evalplus/tests/requirements.txt
EffOPD/code_eval/coding/evalplus/tests/test_legacy_sanitizer.py
EffOPD/code_eval/coding/evalplus/tests/test_treesitter_sanitizer.py
EffOPD/code_eval/coding/evalplus/tools/_experimental/README.md
EffOPD/code_eval/coding/evalplus/tools/_experimental/evaluate_coverage.py
EffOPD/code_eval/coding/evalplus/tools/_experimental/evaluate_runtime.py
EffOPD/code_eval/coding/evalplus/tools/_experimental/generate_big_input.py
EffOPD/code_eval/coding/evalplus/tools/_experimental/set_cover.py
EffOPD/code_eval/coding/evalplus/tools/_experimental/topset_distill.py
EffOPD/code_eval/coding/evalplus/tools/_experimental/type_mut_for_eff.py
EffOPD/code_eval/coding/evalplus/tools/checker.py
EffOPD/code_eval/coding/evalplus/tools/collect_valid_solutions.py
EffOPD/code_eval/coding/evalplus/tools/directory_to_jsonl.py
EffOPD/code_eval/coding/evalplus/tools/evalperf/hf_upload.py
EffOPD/code_eval/coding/evalplus/tools/evalperf/intra_model_viz.py
EffOPD/code_eval/coding/evalplus/tools/evalperf/pairwise_heatmap.py
EffOPD/code_eval/coding/evalplus/tools/evalperf/viz_by_params.py
EffOPD/code_eval/coding/evalplus/tools/filter_inputs.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/check_ground_truth.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/filter_extreme.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/fix_utils.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/fix_v011.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/fix_v012.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/fix_v013.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/fix_v014.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/fix_v015.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/fix_v016.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/fix_v017.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/fix_v018.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/fix_v019.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/init_ground_truth.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/init_plus.py
EffOPD/code_eval/coding/evalplus/tools/humaneval/to_original_fmt.py
EffOPD/code_eval/coding/evalplus/tools/mbpp/check_ground_truth.py
EffOPD/code_eval/coding/evalplus/tools/mbpp/filter_extreme.py
EffOPD/code_eval/coding/evalplus/tools/mbpp/fix_v010.py
EffOPD/code_eval/coding/evalplus/tools/mbpp/fix_v020.py
EffOPD/code_eval/coding/evalplus/tools/mbpp/init_ground_truth.py
EffOPD/code_eval/coding/evalplus/tools/mbpp/init_plus.py
EffOPD/code_eval/coding/evalplus/tools/mbpp/to_original_fmt.py
EffOPD/code_eval/coding/evalplus/tools/merge_dataset.py
EffOPD/code_eval/coding/evalplus/tools/render.py
EffOPD/code_eval/coding/evalplus/tools/requirements.txt
EffOPD/code_eval/coding/evalplus/tools/sanitize.py
EffOPD/code_eval/coding/evalplus/tools/stat_plus.py
EffOPD/code_eval/coding/evalplus/tools/tsr/.gitignore
EffOPD/code_eval/coding/evalplus/tools/tsr/README.md
EffOPD/code_eval/coding/evalplus/tools/tsr/__init__.py
EffOPD/code_eval/coding/evalplus/tools/tsr/coverage_init.py
EffOPD/code_eval/coding/evalplus/tools/tsr/minimization.py
EffOPD/code_eval/coding/evalplus/tools/tsr/mutation_init.py
EffOPD/code_eval/coding/evalplus/tools/tsr/requirements.txt
EffOPD/code_eval/coding/evalplus/tools/tsr/run.py
EffOPD/code_eval/coding/evalplus/tools/tsr/sample_init.py
EffOPD/code_eval/coding/evalplus/tools/tsr/utils.py
EffOPD/code_eval/coding/evalplus/tools/viz_passrate.py
EffOPD/code_eval/coding/evalplus/tools/zip_solutions.py
EffOPD/code_eval/data/HumanEvalPlus.jsonl
EffOPD/code_eval/data/MbppPlus.jsonl
EffOPD/code_eval/scripts/run_evalplus.sh
EffOPD/code_eval/scripts/run_lcb_gen.sh
EffOPD/data/aime24/test.jsonl
EffOPD/data/aime25/test.jsonl
EffOPD/data/hmmt25_feb/test.jsonl
EffOPD/data/hmmt25_nov/test.jsonl
EffOPD/math_eval/eval_math.py
EffOPD/math_eval/run_eval_math.sh
EffOPD/verl/.gemini/config.yaml
EffOPD/verl/.github/CODEOWNERS
EffOPD/verl/.github/ISSUE_TEMPLATE/bug-report.yml
EffOPD/verl/.github/ISSUE_TEMPLATE/config.yml
EffOPD/verl/.github/ISSUE_TEMPLATE/feature-request.yml
EffOPD/verl/.github/PULL_REQUEST_TEMPLATE.md
EffOPD/verl/.github/dependabot.yml
EffOPD/verl/.github/workflows/.deprecate/e2e_eval_aime24.yml
EffOPD/verl/.github/workflows/.deprecate/e2e_ppo_trainer.yml
EffOPD/verl/.github/workflows/.deprecate/e2e_ppo_trainer_megatron_sglang.yml
EffOPD/verl/.github/workflows/.deprecate/e2e_prime.yml
EffOPD/verl/.github/workflows/.deprecate/e2e_spin.yml
EffOPD/verl/.github/workflows/.deprecate/e2e_sppo.yml
… (truncated)
```

## Detected entry points

- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/EffOPD/verl/tests/single_controller/check_worker_alive/main.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/EffOPD/code_eval/coding/LiveCodeBench/lcb_runner/runner/main.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/EffOPD/code_eval/coding/evalplus/tools/tsr/run.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/Analysis/eval/download_hf.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/Analysis/eval/reasoning_eval.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/Analysis/eval/svd.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/Analysis/eval/upd_rank.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/Analysis/utils/data_loader.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/Analysis/utils/examples.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/Analysis/utils/grader.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/Analysis/utils/math_normalization.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/Analysis/utils/parser.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/Analysis/utils/utils.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/EffOPD/math_eval/eval_math.py`
- `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/Analysis/eval/analysis/AlphaPLS.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `EffOPD` — not re-implementing it.
