# Reproduce & validate: Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/   (clone of https://github.com/AMAP-ML/roleagent)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Role-Agent: Bootstrapping LLM Agents via Dual-Role Evolution

**Abstract:** Although Large Language Model (LLM) agents have demonstrated strong performance on complex tasks, their learning is often limited by inefficient interaction feedback and static training environments, which hinder broader generalization. To address these limitations, this paper introduces Role-Agent, \textcolor{black}{a framework} that harnesses a single LLM to function concurrently as both the agent and the environment, enabling a bootstrapped co-evolution. Role-Agent comprises two synergistic components: World-In-Agent (WIA) and Agent-In-World (AIW). In WIA, the LLM acts as the agent and predicts future states after each action; the alignment between predicted and actual states is then used as a process reward, encouraging environment-aware reasoning. In AIW, the LLM analyzes failure modes from failed trajectories and retrieves tasks with similar failure patterns, thereby reshaping the training data distribution for targeted practice. Experiments on multiple benchmarks show that Role-Agent consistently improves performance, yielding an average gain of over 4\% over strong baselines.

## Shipped code — file tree (`projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/`)

```
.github/CODEOWNERS
.github/PULL_REQUEST_TEMPLATE.md
.github/dependabot.yml
.github/workflows/checkpoint_converter.yml
.github/workflows/dataset.yml
.github/workflows/disabled/e2e_ascend.yml
.github/workflows/disabled/e2e_prime.yml
.github/workflows/doc.yml
.github/workflows/e2e_dapo.yml
.github/workflows/e2e_eval_aime24.yml
.github/workflows/e2e_ppo_trainer.yml
.github/workflows/e2e_ppo_trainer_megatron.yml
.github/workflows/e2e_sft.yml
.github/workflows/e2e_spin.yml
.github/workflows/e2e_sppo.yml
.github/workflows/kernels.yml
.github/workflows/model.yml
.github/workflows/pre-commit-full.yml
.github/workflows/pre-commit.yml
.github/workflows/ray_cpu_test.yml
.github/workflows/ray_gpu_test.yml
.github/workflows/sandbox.yml
.github/workflows/sanity.yml
.github/workflows/scorecard.yml
.github/workflows/secrets_scan.yml
.github/workflows/sgl.yml
.github/workflows/utils_cpu_test.yml
.github/workflows/utils_gpu_test.yml
.github/workflows/vllm.yml
.gitignore
.pre-commit-config.yaml
.readthedocs.yaml
.vscode/settings.json
LICENSE
Notice.txt
README.md
agent_system/environments/README.md
agent_system/environments/__init__.py
agent_system/environments/base.py
agent_system/environments/env_manager.py
agent_system/environments/env_package/alfworld/__init__.py
agent_system/environments/env_package/alfworld/alfworld/__init__.py
agent_system/environments/env_package/alfworld/alfworld/agents/README.md
agent_system/environments/env_package/alfworld/alfworld/agents/__init__.py
agent_system/environments/env_package/alfworld/alfworld/agents/agent/__init__.py
agent_system/environments/env_package/alfworld/alfworld/agents/agent/base_agent.py
agent_system/environments/env_package/alfworld/alfworld/agents/agent/text_dagger_agent.py
agent_system/environments/env_package/alfworld/alfworld/agents/agent/text_dqn_agent.py
agent_system/environments/env_package/alfworld/alfworld/agents/agent/vision_dagger_agent.py
agent_system/environments/env_package/alfworld/alfworld/agents/config/rewards.json
agent_system/environments/env_package/alfworld/alfworld/agents/controller/__init__.py
agent_system/environments/env_package/alfworld/alfworld/agents/controller/base.py
agent_system/environments/env_package/alfworld/alfworld/agents/controller/mrcnn.py
agent_system/environments/env_package/alfworld/alfworld/agents/controller/mrcnn_astar.py
agent_system/environments/env_package/alfworld/alfworld/agents/controller/oracle.py
agent_system/environments/env_package/alfworld/alfworld/agents/controller/oracle_astar.py
agent_system/environments/env_package/alfworld/alfworld/agents/detector/__init__.py
agent_system/environments/env_package/alfworld/alfworld/agents/detector/coco_eval.py
agent_system/environments/env_package/alfworld/alfworld/agents/detector/coco_utils.py
agent_system/environments/env_package/alfworld/alfworld/agents/detector/engine.py
agent_system/environments/env_package/alfworld/alfworld/agents/detector/group_by_aspect_ratio.py
agent_system/environments/env_package/alfworld/alfworld/agents/detector/mrcnn.py
agent_system/environments/env_package/alfworld/alfworld/agents/detector/train.py
agent_system/environments/env_package/alfworld/alfworld/agents/detector/transforms.py
agent_system/environments/env_package/alfworld/alfworld/agents/detector/utils.py
agent_system/environments/env_package/alfworld/alfworld/agents/environment/__init__.py
agent_system/environments/env_package/alfworld/alfworld/agents/environment/alfred_hybrid.py
agent_system/environments/env_package/alfworld/alfworld/agents/environment/alfred_thor_env.py
agent_system/environments/env_package/alfworld/alfworld/agents/environment/alfred_tw_env.py
agent_system/environments/env_package/alfworld/alfworld/agents/eval/__init__.py
agent_system/environments/env_package/alfworld/alfworld/agents/eval/evaluate_dagger.py
agent_system/environments/env_package/alfworld/alfworld/agents/eval/evaluate_dqn.py
agent_system/environments/env_package/alfworld/alfworld/agents/eval/evaluate_vision_dagger.py
agent_system/environments/env_package/alfworld/alfworld/agents/expert/__init__.py
agent_system/environments/env_package/alfworld/alfworld/agents/expert/handcoded_expert.py
agent_system/environments/env_package/alfworld/alfworld/agents/expert/handcoded_expert_thor.py
agent_system/environments/env_package/alfworld/alfworld/agents/expert/handcoded_expert_tw.py
agent_system/environments/env_package/alfworld/alfworld/agents/modules/__init__.py
agent_system/environments/env_package/alfworld/alfworld/agents/modules/generic.py
agent_system/environments/env_package/alfworld/alfworld/agents/modules/layers.py
agent_system/environments/env_package/alfworld/alfworld/agents/modules/memory.py
agent_system/environments/env_package/alfworld/alfworld/agents/modules/model.py
agent_system/environments/env_package/alfworld/alfworld/agents/modules/segment_tree.py
agent_system/environments/env_package/alfworld/alfworld/agents/utils/__init__.py
agent_system/environments/env_package/alfworld/alfworld/agents/utils/misc.py
agent_system/environments/env_package/alfworld/alfworld/data/README.md
agent_system/environments/env_package/alfworld/alfworld/data/alfred.pddl
agent_system/environments/env_package/alfworld/alfworld/data/alfred.twl2
agent_system/environments/env_package/alfworld/alfworld/env/__init__.py
agent_system/environments/env_package/alfworld/alfworld/env/reward.py
agent_system/environments/env_package/alfworld/alfworld/env/tasks.py
agent_system/environments/env_package/alfworld/alfworld/env/thor_env.py
agent_system/environments/env_package/alfworld/alfworld/gen/README.md
agent_system/environments/env_package/alfworld/alfworld/gen/__init__.py
agent_system/environments/env_package/alfworld/alfworld/gen/agents/__init__.py
agent_system/environments/env_package/alfworld/alfworld/gen/agents/agent_base.py
agent_system/environments/env_package/alfworld/alfworld/gen/agents/deterministic_planner_agent.py
agent_system/environments/env_package/alfworld/alfworld/gen/agents/plan_agent.py
agent_system/environments/env_package/alfworld/alfworld/gen/agents/semantic_map_planner_agent.py
agent_system/environments/env_package/alfworld/alfworld/gen/constants.py
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/README.md
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/expressions.c
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/expressions.h
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/ff.h
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/inst_easy.c
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/inst_easy.h
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/inst_final.c
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/inst_final.h
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/inst_hard.c
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/inst_hard.h
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/inst_pre.c
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/inst_pre.h
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/lex-fct_pddl.l
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/lex-ops_pddl.l
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/main.c
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/makefile
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/memory.c
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/memory.h
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/output.c
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/output.h
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/parse.c
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/parse.h
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/relax.c
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/relax.h
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/run_sample.sh
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/samples/PutTask_domain.pddl
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/samples/problem_0_0.pddl
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/scan-fct_pddl.y
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/scan-ops_pddl.y
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/search.c
agent_system/environments/env_package/alfworld/alfworld/gen/ff_planner/search.h
agent_system/environments/env_package/alfworld/alfworld/gen/game_states/__init__.py
agent_system/environments/env_package/alfworld/alfworld/gen/game_states/game_state_base.py
agent_system/environments/env_package/alfworld/alfworld/gen/game_states/planned_game_state.py
agent_system/environments/env_package/alfworld/alfworld/gen/game_states/task_game_state.py
agent_system/environments/env_package/alfworld/alfworld/gen/game_states/task_game_state_full_knowledge.py
agent_system/environments/env_package/alfworld/alfworld/gen/goal_library.py
agent_system/environments/env_package/alfworld/alfworld/gen/graph/__init__.py
agent_system/environments/env_package/alfworld/alfworld/gen/graph/graph_obj.py
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan1-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan1-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan1-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan10-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan10-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan10-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan11-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan11-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan11-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan12-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan12-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan12-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan13-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan13-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan13-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan14-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan14-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan14-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan15-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan15-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan15-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan16-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan16-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan16-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan17-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan17-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan17-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan18-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan18-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan18-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan19-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan19-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan19-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan2-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan2-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan2-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan20-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan20-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan20-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan201-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan201-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan201-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan202-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan202-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan202-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan203-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan203-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan203-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan204-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan204-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan204-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan205-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan205-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan205-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan206-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan206-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan206-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan207-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan207-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan207-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan208-layout.npy
… (truncated)
```

## Detected entry points

- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/tests/ray_cpu/check_worker_alive/main.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/agent_system/environments/env_package/alfworld/alfworld/agents/detector/train.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/docs/conf.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/gigpo/core_gigpo.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/role_agent/aiw_curriculum.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/role_agent/aiw_offline.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/role_agent/paper_prompts.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/role_agent/wia_utils.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/scripts/converter_hf_to_mcore.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/scripts/diagnose.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/scripts/model_merger.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/tests/test_protocol.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/verl/protocol.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/agent_system/environments/base.py`
- `projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/external/roleagent/agent_system/environments/env_manager.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `roleagent` — not re-implementing it.
