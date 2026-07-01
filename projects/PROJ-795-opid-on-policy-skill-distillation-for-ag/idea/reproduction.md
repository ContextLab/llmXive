# Reproduce & validate: OPID: On-Policy Skill Distillation for Agentic Reinforcement Learning

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/   (clone of https://github.com/jinyangwu/OPID)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** OPID: On-Policy Skill Distillation for Agentic Reinforcement Learning

**Abstract:** Outcome-based reinforcement learning provides a stable optimization backbone for language agents, but its sparse trajectory-level rewards provide little guidance on which intermediate decisions should be reinforced or suppressed. On-policy self-distillation offers dense token-level supervision, yet existing skill-conditioned variants often rely on external skill memories or retrieved privileged context, which are costly to maintain and can be mismatched with the state distribution induced by the current policy in multi-turn interaction. We propose \textbf{OPID} (\textbf{O}n-\textbf{P}olicy Sk\textbf{i}ll \textbf{D}istillation), a framework that extracts skill supervision directly from completed on-policy trajectories. OPID represents trajectory hindsight as hierarchical skills: episode-level skills capture global workflows or failure-avoidance rules, while step-level skills capture local decision knowledge at critical timesteps. A critical-first routing mechanism uses step-level skills when critical decisions are identified and falls back to episode-level skills as default guidance otherwise. The selected skill is injected into the interaction history, allowing the old policy to re-score the same sampled response under both original and skill-augmented contexts. The resulting log-probability shift yields a token-level self-distillation advantage, which is combined with the outcome advantage for policy optimization. OPID thus preserves RL as the primary training objective while introducing dense, distribution-matched hindsight supervision. Experiments on ALFWorld, WebShop and Search-based QA demonstrate that OPID generally improves agent performance, sample efficiency, and robustness over outcome-only RL and existing skill-distillation baselines. Our code is available at https://github.com/jinyangwu/OPID/tree/main.

## Shipped code — file tree (`projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/`)

```
.codex
.gitignore
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
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan208-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan208-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan209-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan209-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan209-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan21-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan21-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan21-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan210-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan210-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan210-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan211-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan211-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan211-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan212-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan212-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan212-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan213-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan213-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan213-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan214-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan214-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan214-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan215-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan215-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan215-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan216-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan216-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan216-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan217-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan217-objects.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan217-openable.json
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan218-layout.npy
agent_system/environments/env_package/alfworld/alfworld/gen/layouts/FloorPlan218-objects.json
… (truncated)
```

## Detected entry points

- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/tests/ray_cpu/check_worker_alive/main.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/agent_system/environments/env_package/alfworld/alfworld/agents/detector/train.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/docs/conf.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/external_source/sitecustomize.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/gigpo/core_gigpo.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/opid/analysis.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/opid/prompting.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/scripts/converter_hf_to_mcore.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/scripts/demo_opid_analysis_prompt.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/scripts/diagnose.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/scripts/model_merger.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/scripts/test_azure_openai.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/scripts/test_google_genai.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/scripts/test_openai_api.py`
- `projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/external/OPID/scripts/test_sciworld.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `OPID` — not re-implementing it.
