# Reproduce & validate: Active Learners as Efficient PRP Rerankers

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/   (clone of https://github.com/jerecoder/IReranker)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Active Learners as Efficient PRP Rerankers

**Abstract:** Pairwise Ranking Prompting (PRP) elicits pairwise preference judgments from an LLM, which are then aggregated into a ranking, usually via classical sorting algorithms. However, judgments are noisy, order-sensitive, and sometimes intransitive, so sorting assumptions do not match the setting. Because sorting aims to recover a full permutation, truncating it to meet a call budget does not produce a dependable top-K. We thus reframe PRP reranking as active learning from noisy pairwise comparisons and show that active rankers are drop-in replacements that improve NDCG@10 per call in the call-constrained regime. Our noise-robust framework also introduces a randomized-direction oracle that uses a single LLM call per pair. This approach converts systematic position bias into zero-mean noise, enabling unbiased aggregate ranking without the cost of bidirectional calls.

## Shipped code — file tree (`projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/`)

```
.github/workflows/ci.yml
.gitignore
LICENSE
Makefile
README.md
config/beir_eval.json
config/beir_loader.json
data/external/beir/bm25-runs/run.beir.bm25-flat.dbpedia-entity.txt
data/external/beir/bm25-runs/run.beir.bm25-flat.dl-2019.txt
data/external/beir/bm25-runs/run.beir.bm25-flat.dl-2020.txt
data/external/beir/bm25-runs/run.beir.bm25-flat.fiqa.txt
data/external/beir/bm25-runs/run.beir.bm25-flat.nfcorpus.txt
data/external/beir/bm25-runs/run.beir.bm25-flat.robust04.txt
data/external/beir/bm25-runs/run.beir.bm25-flat.scifact.txt
data/external/beir/bm25-runs/run.beir.bm25-flat.trec-covid.txt
data/external/beir/bm25-runs/run.beir.bm25-flat.trec-news.txt
data/external/beir/bm25-runs/run.beir.bm25-flat.webis-touche2020.txt
experiments/analyze_prompt_tokens.py
experiments/inference_time.py
experiments/k_budget_sweep.py
experiments/limit_comparisons.py
experiments/limit_comparisons_sampling_seed_ci.py
experiments/order_effects_fliprate.py
experiments/qwen_evaluation.py
experiments/table1_queries_pairs_ci.py
experiments/table2_queries_pairs_ci.py
experiments/table_queries_pairs_ci.py
experiments/unique_pairs_diagnostic.py
experiments/visualize_results.py
ireranker/__init__.py
ireranker/config.py
ireranker/data/loaders.py
ireranker/evaluation/beir.py
ireranker/oracles/__init__.py
ireranker/oracles/bidirectional_matrix_oracle.py
ireranker/oracles/oracle.py
ireranker/oracles/sampling_matrix_oracles.py
ireranker/oracles/tracking_oracle.py
ireranker/plots.py
ireranker/rankers/__init__.py
ireranker/rankers/bubble_ranker.py
ireranker/rankers/mohajer_bubble_ranker.py
ireranker/rankers/mohajer_ranker.py
ireranker/rankers/nothing_ranker.py
ireranker/rankers/pac.py
ireranker/rankers/pac_bubble_ranker.py
ireranker/rankers/pac_optimized.py
ireranker/rankers/prp_allpairs_ranker.py
ireranker/rankers/prp_sorting_ranker.py
ireranker/rankers/quicksort_ranker.py
ireranker/rankers/ranker.py
ireranker/rankers/registry.py
ireranker/rankers/sliding_window.py
ireranker/rankers/spectral_mle_ranker.py
ireranker/run_beir_eval.py
ireranker/types.py
notebooks/.gitkeep
notebooks/beir_results.ipynb
notebooks/limit_comparisons_visualization.ipynb
notebooks/missing_matrix_entries.ipynb
notebooks/qwen_evaluation_visualization.ipynb
notebooks/rerank_matrix_explorer.ipynb
notebooks/tradeoff_analysis.ipynb
notebooks/variance_analysis.ipynb
pyproject.toml
references/.gitkeep
references/IR/mohajer17a.pdf
reports/beir-metrics/flan-t5-large/dbpedia-entity/summary.csv
reports/beir-metrics/flan-t5-large/dl-2019/summary.csv
reports/beir-metrics/flan-t5-large/dl-2020/summary.csv
reports/beir-metrics/flan-t5-large/fiqa/summary.csv
reports/beir-metrics/flan-t5-large/nfcorpus/summary.csv
reports/beir-metrics/flan-t5-large/robust04/summary.csv
reports/beir-metrics/flan-t5-large/scifact/summary.csv
reports/beir-metrics/flan-t5-large/trec-covid/summary.csv
reports/beir-metrics/flan-t5-large/webis-touche2020/summary.csv
reports/beir-metrics/flan-t5-xl/dbpedia-entity/SKIPPED.txt
reports/beir-metrics/flan-t5-xl/dl-2019/summary.csv
reports/beir-metrics/flan-t5-xl/dl-2020/summary.csv
reports/beir-metrics/flan-t5-xl/fiqa/SKIPPED.txt
reports/beir-metrics/flan-t5-xl/nfcorpus/summary.csv
reports/beir-metrics/flan-t5-xl/robust04/SKIPPED.txt
reports/beir-metrics/flan-t5-xl/scifact/summary.csv
reports/beir-metrics/flan-t5-xl/trec-covid/summary.csv
reports/beir-metrics/flan-t5-xl/webis-touche2020/summary.csv
reports/beir-metrics/flan-t5-xxl/dbpedia-entity/SKIPPED.txt
reports/beir-metrics/flan-t5-xxl/dl-2019/summary.csv
reports/beir-metrics/flan-t5-xxl/dl-2020/summary.csv
reports/beir-metrics/flan-t5-xxl/fiqa/SKIPPED.txt
reports/beir-metrics/flan-t5-xxl/robust04/SKIPPED.txt
reports/beir-metrics/flan-t5-xxl/scifact/SKIPPED.txt
reports/beir-metrics/flan-t5-xxl/trec-covid/SKIPPED.txt
reports/beir-metrics/flan-t5-xxl/webis-touche2020/SKIPPED.txt
reports/beir-metrics-trec/flan-t5-large/dl-2019/summary.csv
reports/beir-metrics-trec/flan-t5-large/dl-2020/summary.csv
reports/beir-metrics-trec/flan-t5-xl/dl-2019/summary.csv
reports/beir-metrics-trec/flan-t5-xl/dl-2020/summary.csv
reports/beir-metrics-trec/flan-t5-xxl/dl-2019/summary.csv
reports/beir-metrics-trec/flan-t5-xxl/dl-2020/summary.csv
reports/figures/aggregated/limit_comparisons_main_all.png
reports/figures/aggregated/limit_comparisons_oracles_all_al.png
reports/figures/aggregated/limit_comparisons_oracles_all_classic.png
reports/figures/limit_comparisons_time/limit_comparisons_time_all_flan_a100_both.png
reports/figures/limit_comparisons_time/limit_comparisons_time_all_flan_a100_randomized.png
reports/figures/limit_comparisons_time/limit_comparisons_time_all_flan_h100_both.png
reports/figures/limit_comparisons_time/limit_comparisons_time_all_flan_h200_both.png
reports/figures/limit_comparisons_time/limit_comparisons_time_all_qwen_a100_both.png
reports/figures/limit_comparisons_time/limit_comparisons_time_all_qwen_h100_both.png
reports/figures/limit_comparisons_time/limit_comparisons_time_all_qwen_h200_both.png
reports/figures/main/limit_comparisons_main_dbpedia-entity.png
reports/figures/main/limit_comparisons_main_dl-2019.png
reports/figures/main/limit_comparisons_main_dl-2020.png
reports/figures/main/limit_comparisons_main_fiqa.png
reports/figures/main/limit_comparisons_main_robust04.png
reports/figures/main/limit_comparisons_main_scifact.png
reports/figures/main/limit_comparisons_main_trec-covid.png
reports/figures/main/limit_comparisons_main_webis-touche2020.png
reports/figures/oracles_al/limit_comparisons_oracles_al_dbpedia-entity.png
reports/figures/oracles_al/limit_comparisons_oracles_al_dl-2019.png
reports/figures/oracles_al/limit_comparisons_oracles_al_dl-2020.png
reports/figures/oracles_al/limit_comparisons_oracles_al_fiqa.png
reports/figures/oracles_al/limit_comparisons_oracles_al_robust04.png
reports/figures/oracles_al/limit_comparisons_oracles_al_scifact.png
reports/figures/oracles_al/limit_comparisons_oracles_al_trec-covid.png
reports/figures/oracles_al/limit_comparisons_oracles_al_webis-touche2020.png
reports/figures/oracles_classic/limit_comparisons_oracles_classic_dbpedia-entity.png
reports/figures/oracles_classic/limit_comparisons_oracles_classic_dl-2019.png
reports/figures/oracles_classic/limit_comparisons_oracles_classic_dl-2020.png
reports/figures/oracles_classic/limit_comparisons_oracles_classic_fiqa.png
reports/figures/oracles_classic/limit_comparisons_oracles_classic_robust04.png
reports/figures/oracles_classic/limit_comparisons_oracles_classic_scifact.png
reports/figures/oracles_classic/limit_comparisons_oracles_classic_trec-covid.png
reports/figures/oracles_classic/limit_comparisons_oracles_classic_webis-touche2020.png
reports/k_budget_sweep.csv
reports/limit_comparisons_experiment.csv
reports/limit_comparisons_experiment_backup.csv
reports/order_effects_fliprate_summary.csv
reports/qwen_evaluation.csv
reports/qwen_evaluation_plots/qwen3-0.6b_dl-2019.png
reports/qwen_evaluation_plots/qwen3-0.6b_dl-2020.png
reports/qwen_evaluation_plots/qwen3-4b-instruct_dl-2019.png
reports/qwen_evaluation_plots/qwen3-4b-instruct_dl-2020.png
reports/qwen_evaluation_summary.csv
reports/results_table_large.csv
reports/results_table_xl.csv
reports/significance_testing/limit_comparisons_raw_by_seed.csv
reports/significance_testing/limit_comparisons_seed_ci_by_dataset.csv
reports/significance_testing/limit_comparisons_seed_ci_macro_dl19_dl20.csv
reports/unique_pairs_diagnostic.csv
scripts/download_tasks_beir.py
scripts/generate_results_table.py
scripts/limit_comparisons_time_plot.py
scripts/refine_limit_comparisons.py
tests/conftest.py
tests/rankers/conftest.py
tests/rankers/expected_webis_results.csv
tests/rankers/test_webis_benchmark.py
tests/run_budget_test.py
tests/test_beir_eval_module.py
tests/test_budgeted_ranker.py
tests/test_matrix_cache.py
tests/test_metrics.py
tests/test_oracle.py
tests/test_rankers_behavior.py
tests/test_registry.py
tests/test_runner.py
tests/test_sampling_oracle_cache.py
```

## Detected entry points

- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/analyze_prompt_tokens.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/inference_time.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/k_budget_sweep.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/limit_comparisons.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/limit_comparisons_sampling_seed_ci.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/order_effects_fliprate.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/qwen_evaluation.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/table1_queries_pairs_ci.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/table2_queries_pairs_ci.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/table_queries_pairs_ci.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/unique_pairs_diagnostic.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/experiments/visualize_results.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/ireranker/config.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/ireranker/plots.py`
- `projects/PROJ-609-https-arxiv-org-abs-2605-14236/external/IReranker/ireranker/run_beir_eval.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `IReranker` — not re-implementing it.
