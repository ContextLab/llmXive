# Reproduce & validate: Scaling the Horizon, Not the Parameters: Reaching Trillion-Parameter Performance with a 35B Agent

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/   (clone of https://github.com/InternScience/Agents-A1)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Scaling the Horizon, Not the Parameters: Reaching Trillion-Parameter Performance with a 35B Agent

**Abstract:** We introduce Agents-A1, a 35B Mixture-of-Experts Agentic Model that reaches trillion-parameter-level performance by scaling the agent horizon. We investigate agent-horizon scaling from two perspectives: scaling long-horizon trajectories and scaling heterogeneous agent abilities. To support this goal, we build a long-horizon knowledge-action infrastructure that connects external knowledge, actions, observations, and verifier outcomes, producing agentic trajectories with an average length of 45K tokens. Based on this, we train Agents-A1 with a three-stage recipe. First, we perform full-domain supervised fine-tuning to align the base model with broad agentic behaviors. Second, we train domain-level teacher models to capture specialized expertise in each domain. Third, we propose a multi-teacher domain-routed on-policy distillation with salient vocabulary alignment to improve knowledge transfer efficiency across different domains, unifying six heterogeneous domains into one deployable student model. Agents-A1 achieves strong and broad performance for long-horizon agent benchmarks. Compared with 1T-parameter model such as Kimi-K2.6 and DeepSeek-V4-pro, Agents-A1 achieves leading results on SEAL-0 (56.4), IFBench (80.6), HiPhO (46.4), FrontierScience-Olympiad (79.0), and MolBench-Bind (56.8), and remains highly competitive on SciCode (44.3), HLE (47.6) and BrowseComp (75.5). We hope this work provides the community with a practical path for scaling the horizon using a 35B agent that can reach or match the performance of 1T models on long-horizon tasks.

## Shipped code — file tree (`projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/`)

```
LICENSE
README.md
assets/a1_benchmarks_altair_grid.svg
docs/.nojekyll
docs/assets/InternScience_logo.png
docs/assets/a1_benchmarks_altair_grid.svg
docs/assets/model_logos/deepseek.svg
docs/assets/model_logos/kimi.png
docs/assets/model_logos/openai.svg
docs/assets/model_logos/ours.svg
docs/assets/model_logos/qwen.svg
docs/assets/model_logos/stepfun.svg
docs/index.html
evaluation/IF/.gitkeep
evaluation/IF/README.md
evaluation/MLE/.gitkeep
evaluation/MLE/README.md
evaluation/Science/.gitkeep
evaluation/Science/README.md
evaluation/Search/.env.example
evaluation/Search/.gitkeep
evaluation/Search/README.md
evaluation/Search/datasets/README.md
evaluation/Search/datasets/data/browsecomp/.gitkeep
evaluation/Search/datasets/data/browsecomp_zh/.gitkeep
evaluation/Search/datasets/data/example/images/logo.png
evaluation/Search/datasets/data/example/standardized_data.jsonl
evaluation/Search/datasets/data/example/standardized_data_with_file.jsonl
evaluation/Search/datasets/data/gaia/.gitkeep
evaluation/Search/datasets/data/seal-0/.gitkeep
evaluation/Search/datasets/data/xbench-deepsearch/.gitkeep
evaluation/Search/inference/agent.py
evaluation/Search/inference/multimodal.py
evaluation/Search/inference/prompt.py
evaluation/Search/inference/run_inference.py
evaluation/Search/inference/run_inference.sh
evaluation/Search/inference/tool_python.py
evaluation/Search/inference/tool_search.py
evaluation/Search/inference/tool_visit.py
evaluation/Search/judger/README.md
evaluation/Search/judger/aggregation.py
evaluation/Search/judger/constants.py
evaluation/Search/judger/data_loading.py
evaluation/Search/judger/evaluate.py
evaluation/Search/judger/judge.py
evaluation/Search/judger/metric_utils.py
evaluation/Search/judger/prompt.py
evaluation/Search/judger/run_stats.py
evaluation/Search/judger/schemas.py
evaluation/Search/requirements.txt
evaluation/Search/run.sh
evaluation/Search/sample_dataset/standardized_data.jsonl
evaluation/Tools/.gitkeep
evaluation/Tools/README.md
evaluation/Tools/mattools/.dockerignore
evaluation/Tools/mattools/.gitattributes
evaluation/Tools/mattools/.gitignore
evaluation/Tools/mattools/.python-version
evaluation/Tools/mattools/Dockerfile
evaluation/Tools/mattools/LICENSE
evaluation/Tools/mattools/README.md
evaluation/Tools/mattools/poetry.lock
evaluation/Tools/mattools/pyproject.toml
evaluation/Tools/mattools/requirements.txt
evaluation/Tools/mattools/src/RAG_agent_test/build_agent.py
evaluation/Tools/mattools/src/RAG_agent_test/mtb_logger.py
evaluation/Tools/mattools/src/agentic_RAG_test/main.py
evaluation/Tools/mattools/src/agentic_RAG_test/mtb_logger.py
evaluation/Tools/mattools/src/agentic_RAG_test/prompt.py
evaluation/Tools/mattools/src/agentic_RAG_test/rag.py
evaluation/Tools/mattools/src/agentic_RAG_test/text_analysis_tool.py
evaluation/Tools/mattools/src/call_llms.py
evaluation/Tools/mattools/src/claude_cli_test/build_agent.py
evaluation/Tools/mattools/src/claude_cli_test/launch_claude.sh
evaluation/Tools/mattools/src/code_segments/pymatgen_analysis_defects/conftest.json
evaluation/Tools/mattools/src/code_segments/pymatgen_analysis_defects/plotting/test_thermo.json
evaluation/Tools/mattools/src/code_segments/pymatgen_analysis_defects/test_ccd.json
evaluation/Tools/mattools/src/code_segments/pymatgen_analysis_defects/test_core.json
evaluation/Tools/mattools/src/code_segments/pymatgen_analysis_defects/test_corrections.json
evaluation/Tools/mattools/src/code_segments/pymatgen_analysis_defects/test_finder.json
evaluation/Tools/mattools/src/code_segments/pymatgen_analysis_defects/test_generators.json
evaluation/Tools/mattools/src/code_segments/pymatgen_analysis_defects/test_recombination.json
evaluation/Tools/mattools/src/code_segments/pymatgen_analysis_defects/test_supercells.json
evaluation/Tools/mattools/src/code_segments/pymatgen_analysis_defects/test_thermo.json
evaluation/Tools/mattools/src/code_segments/pymatgen_analysis_defects/test_utils.json
evaluation/Tools/mattools/src/defects_doc/api_overview.txt
evaluation/Tools/mattools/src/defects_doc/pymatgen_analysis_defects_ccd.txt
evaluation/Tools/mattools/src/defects_doc/pymatgen_analysis_defects_core.txt
evaluation/Tools/mattools/src/defects_doc/pymatgen_analysis_defects_finder.txt
evaluation/Tools/mattools/src/defects_doc/pymatgen_analysis_defects_generators.txt
evaluation/Tools/mattools/src/defects_doc/pymatgen_analysis_defects_recombination.txt
evaluation/Tools/mattools/src/defects_doc/pymatgen_analysis_defects_supercells.txt
evaluation/Tools/mattools/src/defects_doc/pymatgen_analysis_defects_thermo.txt
evaluation/Tools/mattools/src/defects_doc/pymatgen_analysis_defects_utils.txt
evaluation/Tools/mattools/src/docker_sandbox.py
evaluation/Tools/mattools/src/json_handler.py
evaluation/Tools/mattools/src/mtr_rag_test/__init__.py
evaluation/Tools/mattools/src/mtr_rag_test/mtb_logger.py
evaluation/Tools/mattools/src/mtr_rag_test/prompts.py
evaluation/Tools/mattools/src/mtr_rag_test/rag.py
evaluation/Tools/mattools/src/pure_agent_test/build_agent.py
evaluation/Tools/mattools/src/pure_agent_test/mtb_logger.py
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_boltzmann/new_unit_test.py
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_boltzmann/properties.json
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_boltzmann/question.txt
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_get_Rad_coef/new_unit_test.py
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_get_Rad_coef/properties.json
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_get_Rad_coef/question.txt
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_get_SRH_coef/new_unit_test.py
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_get_SRH_coef/properties.json
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_get_SRH_coef/question.txt
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_get_vibronic_matrix_elements/new_unit_test.py
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_get_vibronic_matrix_elements/properties.json
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_get_vibronic_matrix_elements/question.txt
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_lower_envelope/new_unit_test.py
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_lower_envelope/properties.json
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_lower_envelope/question.txt
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_pchip_eval/new_unit_test.py
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_pchip_eval/properties.json
evaluation/Tools/mattools/src/question_segments/pymatgen_analysis_defects/test_pchip_eval/question.txt
evaluation/Tools/mattools/src/result_analysis.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/.editorconfig
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/alchemy/__init__.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/alchemy/filters.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/alchemy/materials.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/alchemy/transmuters.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/adsorption.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/aflow_prototypes.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/atomic_subshell_photoionization_cross_sections.csv
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/bond_dissociation.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/bond_valence.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/bonds_jmol_ob.yaml
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/bvparam_1991.yaml
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/__init__.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/connectivity/__init__.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/connectivity/connected_components.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/connectivity/connectivity_finder.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/connectivity/environment_nodes.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/connectivity/structure_connectivity.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/__init__.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/chemenv_strategies.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries.py
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/A#2.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/AC#12.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/BO_1#8.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/BO_2#8.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/BO_3#8.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/BS_1#10.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/BS_2#10.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/C#12.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/C#8.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/CO#11.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/DD#20.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/DD#8.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/DDPN#8.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/DI#11.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/ET#7.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/FO#7.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/H#10.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/H#11.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/HA#12.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/HB#8.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/HD#9.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/HP#12.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/I#12.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/L#2.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/MI#10.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/O#6.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/O#6_explicit.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/PA#10.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/PB#7.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/PBP#12.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/PCPA#11.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/PP#10.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/PP#5.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/PP#6.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/S#1.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/S#10.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/S#12.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/S#4.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/S#5.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/SA#8.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/SBSA#10.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/SBT#8.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/SC#12.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/SH#11.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/SH#13.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/SMA#9.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/SS#4.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/SS#9.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/ST#7.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/SY#4.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/T#4.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/T#5.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/T#6.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/TBSA#10.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/TBT#8.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/TC#9.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/TI#9.json
evaluation/Tools/mattools/src/tool_source_code/pymatgen/src/pymatgen/analysis/chemenv/coordination_environments/coordination_geometries_files/TL#3.json
… (truncated)
```

## Detected entry points

- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Tools/mattools/src/agentic_RAG_test/main.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Tools/tau2/src/tau2/run.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Tools/vita/src/vita/run.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/judger/evaluate.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/inference/agent.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/inference/multimodal.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/inference/prompt.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/inference/run_inference.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/inference/tool_python.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/inference/tool_search.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/inference/tool_visit.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/judger/aggregation.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/judger/constants.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/judger/data_loading.py`
- `projects/PROJ-806-scaling-the-horizon-not-the-parameters-r/external/Agents-A1/evaluation/Search/judger/judge.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `Agents-A1` — not re-implementing it.
