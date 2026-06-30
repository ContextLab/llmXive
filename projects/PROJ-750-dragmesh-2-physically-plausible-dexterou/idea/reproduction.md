# Reproduce & validate: DragMesh-2: Physically Plausible Dexterous Hand-Object Interaction with Articulated Objects

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/   (clone of https://github.com/AIGeeksGroup/DragMesh-2)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** DragMesh-2: Physically Plausible Dexterous Hand-Object Interaction with Articulated Objects

**Abstract:** Dexterous interaction with articulated objects is important for household, assistive, and humanoid manipulation, where multi-finger hands can provide compliant contact patterns beyond parallel-jaw grasping. However, articulated-object manipulation differs from static-object manipulation: the target part cannot be directly actuated, and its motion must emerge through sustained physical hand--handle contact. This makes the transition from object-centric articulated generation to hand-driven dexterous hand--object interaction non-trivial, since geometric trajectory replay or open-loop execution does not model the contact dynamics required to move the articulated part. Moreover, policies trained only for task completion under fixed dynamics can overfit nominal contact loads, especially without tactile or force feedback, and may degrade when the contact load changes. To address these challenges, we present DragMesh-2, a contact-driven framework for dexterous interaction with articulated objects that extends articulated interaction from object-centric generation to hand-driven dexterous hand--object interaction, where articulated motion must arise through physical contact. We further propose PICA, a physically informed contact-aware training mechanism that injects physical signals into policy learning without tactile or force feedback, improving robustness and task success under changing contact loads. Finally, we conduct systematic evaluation across multiple damping conditions and articulated-object categories to study robustness under contact-load variation, and provide a pure-geometry dexterous interaction resource to support future loco-manipulation and humanoid hand--object interaction research. Across seven GAPartNet objects, DragMesh-2 achieves stronger robustness under contact-load variation than the compared methods while maintaining high task success across damping conditions.

## Shipped code — file tree (`projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/`)

```
.gitignore
README.md
assets/.gitkeep
assets/README.md
backbones/README.md
backbones/__init__.py
backbones/gla/README.md
backbones/gla/__init__.py
backbones/gla/a2c_network.py
backbones/gru/README.md
backbones/mlp/README.md
backbones/transformer/README.md
configs/README.md
configs/env/README.md
configs/env/hand_config.yaml
configs/train/README.md
configs/train/gla/README.md
configs/train/gla/ppo.yaml
configs/train/gla/ppo_pool_mean.yaml
configs/train/mlp/README.md
configs/train/mlp/pica.yaml
configs/train/mlp/pica_drand12.yaml
configs/train/mlp/ppo.yaml
configs/train/pica/README.md
configs/train/pica/train_config_gla_pica.yaml
configs/train/pica/train_config_gla_pica_drand12.yaml
configs/train/pica/train_config_gla_pica_drand12_aux.yaml
configs/train/pica/train_config_gla_pica_drand12_aux_v2c.yaml
configs/train/pica/train_config_gla_pica_drand14.yaml
configs/train/pica/train_config_gla_pica_drand14_aux_v2c.yaml
configs/train/pica/train_config_gla_pica_drand14_aux_v2c_save25.yaml
configs/train/pica/train_config_gla_pica_v2d_aram.yaml
configs/train/pica/train_config_gla_pica_v2d_both.yaml
configs/train/pica/train_config_gla_pica_v2d_both_ft_continue_save25.yaml
configs/train/pica/train_config_gla_pica_v2d_both_jointaware.yaml
configs/train/pica/train_config_gla_pica_v2d_reconfig.yaml
configs/train/pica/train_config_gla_pica_v2e_v2_stallpull_ft.yaml
configs/train/pica/train_config_gla_pica_v2e_v3_damprange_ft.yaml
data/README.md
data/manifest.example.csv
dataset/__init__.py
dataset/geometric/README.md
dataset/geometric/__init__.py
dataset/geometric/build_hand_urdf.py
dataset/geometric/hand_object_gym.py
dataset/geometric/run_hand_drag.py
dataset/geometric/utils.py
demos/real_robot/README.md
demos/simulation/README.md
environment.yml
hands/README.md
hands/floating/README.md
hands/floating/smplx_right_hand_floating.urdf
hands/smplx_variants/README.md
hands/smplx_variants/full_fingers/metadata.json
hands/smplx_variants/full_fingers/smplx_full_fingers.urdf
hands/smplx_variants/full_fingers/smplx_full_fingers.xml
hands/smplx_variants/generate_smplx_variants.py
hands/smplx_variants/hands_only/metadata.json
hands/smplx_variants/hands_only/smplx_left_hand.json
hands/smplx_variants/hands_only/smplx_left_hand.urdf
hands/smplx_variants/hands_only/smplx_left_hand.xml
hands/smplx_variants/hands_only/smplx_right_hand.json
hands/smplx_variants/hands_only/smplx_right_hand.urdf
hands/smplx_variants/hands_only/smplx_right_hand.xml
hands/smplx_variants/overview.json
hands/smplx_variants/palms_only/metadata.json
hands/smplx_variants/palms_only/smplx_left_palm_wrist.json
hands/smplx_variants/palms_only/smplx_left_palm_wrist.urdf
hands/smplx_variants/palms_only/smplx_left_palm_wrist.xml
hands/smplx_variants/palms_only/smplx_right_palm_wrist.json
hands/smplx_variants/palms_only/smplx_right_palm_wrist.urdf
hands/smplx_variants/palms_only/smplx_right_palm_wrist.xml
pica/README.md
pica/__init__.py
pica/a2c_agent.py
ppo/README.md
ppo/__init__.py
ppo/hand_drag_task.py
ppo/rlgames_wrapper.py
ppo/train.py
requirements.txt
scripts/README.md
scripts/baselines/run_trajectory_tracking.sh
scripts/compare_history_vs_ppo.py
scripts/eval/eval_det_stoch_damping.sh
scripts/eval_postprocess.py
scripts/evaluate_ppo_baseline.py
scripts/run_trajectory_baselines.py
scripts/track_trajectory_baseline.py
scripts/train/train_pica.sh
scripts/utils/check_checkpoint.sh
```

## Detected entry points

- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/ppo/train.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/pica/a2c_agent.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/ppo/hand_drag_task.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/ppo/rlgames_wrapper.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/scripts/compare_history_vs_ppo.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/scripts/eval_postprocess.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/scripts/evaluate_ppo_baseline.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/scripts/run_trajectory_baselines.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/scripts/track_trajectory_baseline.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/backbones/gla/a2c_network.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/dataset/geometric/build_hand_urdf.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/dataset/geometric/hand_object_gym.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/dataset/geometric/run_hand_drag.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/dataset/geometric/utils.py`
- `projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/external/DragMesh-2/hands/smplx_variants/generate_smplx_variants.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `DragMesh-2` — not re-implementing it.
