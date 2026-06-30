# Reproduce & validate: ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Research

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/   (clone of https://github.com/InternScience/ResearchClawBench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Research

**Abstract:** AI coding agents are increasingly used for scientific work, but their end-to-end autonomous research capability remains difficult to verify. We present ResearchClawBench, a benchmark for evaluating autonomous scientific research across 40 tasks from 10 scientific domains. Each task is grounded in a real published paper, provides related literature and raw data, and hides the target paper during evaluation. Expert-curated multimodal rubrics decompose the target scientific artifacts into weighted criteria, enabling evaluation of target-paper-level re-discovery while leaving room for new discovery. We evaluate seven autonomous research (auto-research) agents under a unified protocol and seventeen native LLMs through the lightweight ResearchHarness. Current systems remain far from reliable re-discovery: the strongest autonomous agent, Claude Code, averages 21.5, and the strongest ResearchHarness LLM, Claude-Opus-4.7, averages 20.7, with an LLM frontier mean of only 26.5. Error analysis shows that failures concentrate in experimental protocol mismatch, evidence mismatch, and missing scientific core. ResearchClawBench provides a reproducible evaluation frontier for measuring progress toward autonomous scientific research.

## Shipped code — file tree (`projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/`)

```
.github/workflows/tests.yml
.gitignore
CONTRIBUTING.md
LICENSE
README.md
assets/auto-research.png
assets/evaluation.png
assets/leaderboard.png
assets/teaser.png
assets/wechat.jpg
assets/whatsapp.jpg
eval_configs/researchharness_example_1_single_task.yaml
eval_configs/researchharness_example_2_mixed_repeats.yaml
eval_configs/researchharness_example_3_all_tasks.yaml
eval_configs/researchharness_example_4_qwen_thinking.yaml
evaluation/.env.example
evaluation/__init__.py
evaluation/__main__.py
evaluation/agents.json
evaluation/cli_clear.py
evaluation/cli_eval.py
evaluation/config.py
evaluation/instructions_tmpl.py
evaluation/requirements.txt
evaluation/run_task.py
evaluation/score.py
evaluation/server.py
evaluation/static/app.js
evaluation/static/favicon.svg
evaluation/static/logos/anthropic.svg
evaluation/static/logos/arxiv.svg
evaluation/static/logos/asx.svg
evaluation/static/logos/deepseek.png
evaluation/static/logos/evo.svg
evaluation/static/logos/gemini.png
evaluation/static/logos/github.svg
evaluation/static/logos/glm.webp
evaluation/static/logos/grok.png
evaluation/static/logos/huggingface.svg
evaluation/static/logos/kimi.png
evaluation/static/logos/lingtai.png
evaluation/static/logos/mimo.png
evaluation/static/logos/minimax.png
evaluation/static/logos/nanobot.svg
evaluation/static/logos/openai.svg
evaluation/static/logos/openclaw.svg
evaluation/static/logos/qwen.png
evaluation/static/logos/researchclaw.svg
evaluation/static/logos/rh.svg
evaluation/static/style.css
evaluation/templates/index.html
evaluation/utils.py
rcb-clear
rcb-eval
tasks/Astronomy_000/data/IRAS_09149-6206_samples.dat
tasks/Astronomy_000/data/M33_X-7_samples.dat
tasks/Astronomy_000/related_work/paper_000.pdf
tasks/Astronomy_000/related_work/paper_001.pdf
tasks/Astronomy_000/related_work/paper_002.pdf
tasks/Astronomy_000/related_work/paper_003.pdf
tasks/Astronomy_000/target_study/checklist.json
tasks/Astronomy_000/target_study/images/exclusion_plot.png
tasks/Astronomy_000/target_study/images/m33x7_exclusion.png
tasks/Astronomy_000/target_study/images/m33x7_regge.png
tasks/Astronomy_000/target_study/images/superrad_rates.png
tasks/Astronomy_000/target_study/paper.pdf
tasks/Astronomy_000/task_info.json
tasks/Astronomy_001/data/DESI_EDE_Repro_Data.txt
tasks/Astronomy_001/related_work/paper_000.pdf
tasks/Astronomy_001/related_work/paper_001.pdf
tasks/Astronomy_001/related_work/paper_002.pdf
tasks/Astronomy_001/related_work/paper_003.pdf
tasks/Astronomy_001/target_study/checklist.json
tasks/Astronomy_001/target_study/images/figure3_triangle.png
tasks/Astronomy_001/target_study/images/figure6_distance.png
tasks/Astronomy_001/target_study/paper.pdf
tasks/Astronomy_001/task_info.json
tasks/Astronomy_002/data/H0DN_MinimalDataset.txt
tasks/Astronomy_002/related_work/paper_000.pdf
tasks/Astronomy_002/related_work/paper_001.pdf
tasks/Astronomy_002/related_work/paper_002.pdf
tasks/Astronomy_002/related_work/paper_003.pdf
tasks/Astronomy_002/target_study/checklist.json
tasks/Astronomy_002/target_study/images/host_residuals.png
tasks/Astronomy_002/target_study/paper.pdf
tasks/Astronomy_002/task_info.json
tasks/Astronomy_003/data/fig6_data.csv
tasks/Astronomy_003/data/fig7_data.csv
tasks/Astronomy_003/data/fig8_data.csv
tasks/Astronomy_003/related_work/paper_000.pdf
tasks/Astronomy_003/related_work/paper_001.pdf
tasks/Astronomy_003/related_work/paper_002.pdf
tasks/Astronomy_003/related_work/paper_003.pdf
tasks/Astronomy_003/target_study/checklist.json
tasks/Astronomy_003/target_study/images/figure6.png
tasks/Astronomy_003/target_study/images/figure7.png
tasks/Astronomy_003/target_study/images/figure8.png
tasks/Astronomy_003/target_study/paper.pdf
tasks/Astronomy_003/task_info.json
tasks/Chemistry_000/data/bace.csv
tasks/Chemistry_000/data/bbbp.csv
tasks/Chemistry_000/data/clintox.csv
tasks/Chemistry_000/data/hiv.csv
tasks/Chemistry_000/data/muv.csv
tasks/Chemistry_000/related_work/paper_000.pdf
tasks/Chemistry_000/related_work/paper_001.pdf
tasks/Chemistry_000/related_work/paper_002.pdf
tasks/Chemistry_000/related_work/paper_003.pdf
tasks/Chemistry_000/target_study/checklist.json
tasks/Chemistry_000/target_study/images/cc4d517e-d400-4714-a343-617b7e657b51.png
tasks/Chemistry_000/target_study/paper.pdf
tasks/Chemistry_000/task_info.json
tasks/Chemistry_001/data/sample/2l3r/2l3r_ligand.sdf
tasks/Chemistry_001/data/sample/2l3r/2l3r_protein.pdb
tasks/Chemistry_001/related_work/paper_000.pdf
tasks/Chemistry_001/related_work/paper_001.pdf
tasks/Chemistry_001/related_work/paper_002.pdf
tasks/Chemistry_001/related_work/paper_003.pdf
tasks/Chemistry_001/target_study/checklist.json
tasks/Chemistry_001/target_study/images/comparison.png
tasks/Chemistry_001/target_study/images/diffusion_schedule.csv
tasks/Chemistry_001/target_study/images/diffusion_schedule.png
tasks/Chemistry_001/target_study/paper.pdf
tasks/Chemistry_001/task_info.json
tasks/Chemistry_002/data/1brs_AD.pdb
tasks/Chemistry_002/data/skempi_v2.csv
tasks/Chemistry_002/related_work/paper_000.pdf
tasks/Chemistry_002/related_work/paper_001.pdf
tasks/Chemistry_002/related_work/paper_002.pdf
tasks/Chemistry_002/related_work/paper_003.pdf
tasks/Chemistry_002/target_study/checklist.json
tasks/Chemistry_002/target_study/images/haddock3-alascan_VS_SKEMPI.png
tasks/Chemistry_002/target_study/paper.pdf
tasks/Chemistry_002/task_info.json
tasks/Chemistry_003/data/ag3_chargestates.xyz
tasks/Chemistry_003/data/charged_dimer.xyz
tasks/Chemistry_003/data/random_charges.xyz
tasks/Chemistry_003/related_work/paper_000.pdf
tasks/Chemistry_003/related_work/paper_001.pdf
tasks/Chemistry_003/related_work/paper_002.pdf
tasks/Chemistry_003/related_work/paper_003.pdf
tasks/Chemistry_003/target_study/checklist.json
tasks/Chemistry_003/target_study/images/fig1_random_charges.png
tasks/Chemistry_003/target_study/images/fig3_dimer_binding.png
tasks/Chemistry_003/target_study/images/fig5_ag3_energy.png
tasks/Chemistry_003/target_study/paper.pdf
tasks/Chemistry_003/task_info.json
tasks/Earth_000/data/glambie/GlaMBIE_DATASETS_INFO.md
tasks/Earth_000/data/glambie/README.md
tasks/Earth_000/data/glambie/input/10_north_asia/north_asia_combined_DUS-combined_Dussaillant_et_al.csv
tasks/Earth_000/data/glambie/input/10_north_asia/north_asia_combined_Huss_Huss_et_al.csv
tasks/Earth_000/data/glambie/input/10_north_asia/north_asia_demdiff_ETH_Hugonnet_et_al.csv
tasks/Earth_000/data/glambie/input/10_north_asia/north_asia_glaciological_UZH_GlaciolSineWave_Zemp_et_al.csv
tasks/Earth_000/data/glambie/input/10_north_asia/north_asia_glaciological_WGMS-beta_WGMS.csv
tasks/Earth_000/data/glambie/input/10_north_asia/north_asia_gravimetry_Jacob_2012_dmdt_Jacob_et_al.csv
tasks/Earth_000/data/glambie/input/10_north_asia/north_asia_gravimetry_Sasgen_AWIarc_RL01_2_Sasgen_et_al.csv
tasks/Earth_000/data/glambie/input/10_north_asia/north_asia_gravimetry_Wouters_Wouters_et_al.csv
tasks/Earth_000/data/glambie/input/11_central_europe/central_europe_combined_DUS-combined_Dussaillant_et_al.csv
tasks/Earth_000/data/glambie/input/11_central_europe/central_europe_combined_Huss_Huss_et_al.csv
tasks/Earth_000/data/glambie/input/11_central_europe/central_europe_demdiff_ETH_Hugonnet_et_al.csv
tasks/Earth_000/data/glambie/input/11_central_europe/central_europe_demdiff_FAU-GLACIER_Braun_et_al.csv
tasks/Earth_000/data/glambie/input/11_central_europe/central_europe_glaciological_UZH_GlaciolSineWave_Zemp_et_al.csv
tasks/Earth_000/data/glambie/input/11_central_europe/central_europe_glaciological_WGMS-beta_WGMS.csv
tasks/Earth_000/data/glambie/input/11_central_europe/central_europe_gravimetry_Jacob_2012_dmdt_Jacob_et_al.csv
tasks/Earth_000/data/glambie/input/11_central_europe/central_europe_gravimetry_Sasgen_AWIarc_RL01_2_Sasgen_et_al.csv
tasks/Earth_000/data/glambie/input/11_central_europe/central_europe_gravimetry_Wouters_Wouters_et_al.csv
tasks/Earth_000/data/glambie/input/12_caucasus_middle_east/caucasus_middle_east_combined_DUS-combined_Dussaillant_et_al.csv
tasks/Earth_000/data/glambie/input/12_caucasus_middle_east/caucasus_middle_east_combined_Huss_Huss_et_al.csv
tasks/Earth_000/data/glambie/input/12_caucasus_middle_east/caucasus_middle_east_demdiff_ETH_Hugonnet_et_al.csv
tasks/Earth_000/data/glambie/input/12_caucasus_middle_east/caucasus_middle_east_glaciological_UZH_GlaciolSineWave_Zemp_et_al.csv
tasks/Earth_000/data/glambie/input/12_caucasus_middle_east/caucasus_middle_east_glaciological_WGMS-beta_WGMS.csv
tasks/Earth_000/data/glambie/input/12_caucasus_middle_east/caucasus_middle_east_gravimetry_Jacob_2012_dmdt_Jacob_et_al.csv
tasks/Earth_000/data/glambie/input/12_caucasus_middle_east/caucasus_middle_east_gravimetry_Wouters_Wouters_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_altimetry_Jakob_Gourmelen_Jakob_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_altimetry_Ke_Ke_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_altimetry_Treichler_ICESat_Treichler_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_altimetry_Treichler_snowfall_Treichler_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_combined_DUS-combined_Dussaillant_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_combined_Huss_Huss_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_combined_Miles2021_Miles_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_demdiff_Brun_et_al_2017_Brun_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_demdiff_ETH_Hugonnet_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_glaciological_UZH_GlaciolSineWave_Zemp_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_glaciological_WGMS-beta_WGMS.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_gravimetry_Harig_Group_Harig_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_gravimetry_Jacob_2012_dmdt_Jacob_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_gravimetry_Sasgen_AWIarc_RL01_2_Sasgen_et_al.csv
tasks/Earth_000/data/glambie/input/13_central_asia/central_asia_gravimetry_Wouters_Wouters_et_al.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_altimetry_Jakob_Gourmelen_Jakob_et_al.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_altimetry_Ke_Ke_et_al.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_altimetry_Treichler_ICESat_Treichler_et_al.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_altimetry_Treichler_snowfall_Treichler_et_al.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_combined_DUS-combined_Dussaillant_et_al.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_combined_Huss_Huss_et_al.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_combined_Miles2021_Miles_et_al.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_demdiff_Brun_et_al_2017_Brun_et_al.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_demdiff_ETH_Hugonnet_et_al.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_glaciological_UZH_GlaciolSineWave_Zemp_et_al.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_glaciological_WGMS-beta_WGMS.csv
tasks/Earth_000/data/glambie/input/14_south_asia_west/south_asia_west_gravimetry_Jacob_2012_dmdt_Jacob_et_al.csv
… (truncated)
```

## Detected entry points

- `projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/evaluation/cli_clear.py`
- `projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/evaluation/cli_eval.py`
- `projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/evaluation/config.py`
- `projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/evaluation/instructions_tmpl.py`
- `projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/evaluation/run_task.py`
- `projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/evaluation/score.py`
- `projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/evaluation/server.py`
- `projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/evaluation/utils.py`
- `projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/tests/test_cli_clear.py`
- `projects/PROJ-683-researchclawbench-a-benchmark-for-end-to/external/ResearchClawBench/tests/test_cli_eval.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `ResearchClawBench` — not re-implementing it.
