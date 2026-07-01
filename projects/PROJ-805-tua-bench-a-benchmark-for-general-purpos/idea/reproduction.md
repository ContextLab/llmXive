# Reproduce & validate: TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/   (clone of https://github.com/facebookresearch/TUA-Bench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** TUA-Bench: A Benchmark for General-Purpose Terminal-Use Agents

**Abstract:** As large language models and harness frameworks continue to advance, agents operating in terminals are increasingly capable of performing a broader range of general computer-use tasks beyond coding. However, existing benchmarks do not adequately evaluate general-purpose terminal computer-use agents (TUAs): general computer-use benchmarks primarily target graphical user interfaces (GUIs), whereas terminal-based benchmarks largely emphasize technical and programming-centric workflows historically native to the shell. We introduce TUA-Bench, a general-purpose benchmark for terminal-use agents. TUA-Bench includes 120 real-world tasks across five task families, covering routine digital activities-including document editing, email management, and live-web information seeking-as well as scientific and engineering workflows co-designed with PhD-level domain experts that require specialized software. This breadth distinguishes TUA-Bench from prior shell-focused or domain-specific benchmarks. Each task is manually designed, runs in a real terminal with a deterministic setup script, and is evaluated by an execution-based scoring protocol. We find that the strongest frontier agent, Claude Code with Claude Opus 4.8 max reasoning effort, achieves 65.8% overall performance, with substantial gaps across both tracks. By providing a broad and realistic evaluation of terminal-use capabilities, TUA-Bench aims to accelerate the transition from narrow, task-specific assistants to general-purpose agents capable of operating reliably across diverse digital environments.

## Shipped code — file tree (`projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/`)

```
.gitignore
.python-version
CODE_OF_CONDUCT.md
CONTRIBUTING.md
LICENSE
README.md
dataset.toml
docs/imgs/tua-banner.png
docs/imgs/tua-bench-overview.png
pyproject.toml
repo_env/__init__.py
repo_env/podman_env.py
repo_env/setup_env.py
tasks/000-count-nuclei/.gitignore
tasks/000-count-nuclei/README.md
tasks/000-count-nuclei/environment/Dockerfile
tasks/000-count-nuclei/instruction.md
tasks/000-count-nuclei/solution/reference/Nuclei.csv
tasks/000-count-nuclei/solution/solve.sh
tasks/000-count-nuclei/task.toml
tasks/000-count-nuclei/tests/reference/Nuclei.csv
tasks/000-count-nuclei/tests/test.sh
tasks/000-count-nuclei/tests/test_outputs.py
tasks/001-locate-nuclei-centers/.gitignore
tasks/001-locate-nuclei-centers/README.md
tasks/001-locate-nuclei-centers/environment/Dockerfile
tasks/001-locate-nuclei-centers/instruction.md
tasks/001-locate-nuclei-centers/solution/reference/Nuclei.csv
tasks/001-locate-nuclei-centers/solution/solve.sh
tasks/001-locate-nuclei-centers/task.toml
tasks/001-locate-nuclei-centers/tests/reference/Nuclei.csv
tasks/001-locate-nuclei-centers/tests/test.sh
tasks/001-locate-nuclei-centers/tests/test_outputs.py
tasks/002-count-enter-key-presses/.gitignore
tasks/002-count-enter-key-presses/README.md
tasks/002-count-enter-key-presses/environment/Dockerfile
tasks/002-count-enter-key-presses/environment/input/.gitkeep
tasks/002-count-enter-key-presses/instruction.md
tasks/002-count-enter-key-presses/solution/solve.sh
tasks/002-count-enter-key-presses/task.toml
tasks/002-count-enter-key-presses/tests/test.sh
tasks/002-count-enter-key-presses/tests/verify.py
tasks/003-rebuild-energy-model/.gitignore
tasks/003-rebuild-energy-model/README.md
tasks/003-rebuild-energy-model/environment/Dockerfile
tasks/003-rebuild-energy-model/environment/input/task_plan.json
tasks/003-rebuild-energy-model/environment/input/weather.epw
tasks/003-rebuild-energy-model/environment/task-support/render_openstudio_model.py
tasks/003-rebuild-energy-model/input/task_plan.json
tasks/003-rebuild-energy-model/input/weather.epw
tasks/003-rebuild-energy-model/instruction.md
tasks/003-rebuild-energy-model/solution/reference/building_reference.osm
tasks/003-rebuild-energy-model/solution/reference/eplusout.sql
tasks/003-rebuild-energy-model/solution/reference/wa_building_100094_renders/energy_model_summary.txt
tasks/003-rebuild-energy-model/solution/reference/wa_building_100094_renders/floorplan_openings.csv
tasks/003-rebuild-energy-model/solution/reference/wa_building_100094_renders/floorplan_reconstruction.txt
tasks/003-rebuild-energy-model/solution/reference/wa_building_100094_renders/floorplan_schedule.csv
tasks/003-rebuild-energy-model/solution/reference/wa_building_100094_renders/space_type_loads.csv
tasks/003-rebuild-energy-model/solution/solve.sh
tasks/003-rebuild-energy-model/task.toml
tasks/003-rebuild-energy-model/tests/reference/eplusout.sql
tasks/003-rebuild-energy-model/tests/test.sh
tasks/003-rebuild-energy-model/tests/test_outputs.py
tasks/004-place-heater-for-sensors/.gitignore
tasks/004-place-heater-for-sensors/README.md
tasks/004-place-heater-for-sensors/environment/Dockerfile
tasks/004-place-heater-for-sensors/environment/input/heater_design_request.json
tasks/004-place-heater-for-sensors/input/heater_design_request.json
tasks/004-place-heater-for-sensors/instruction.md
tasks/004-place-heater-for-sensors/solution/reference/heater_placement_solution.json
tasks/004-place-heater-for-sensors/solution/solve.sh
tasks/004-place-heater-for-sensors/task.toml
tasks/004-place-heater-for-sensors/tests/reference/heater_placement_solution.json
tasks/004-place-heater-for-sensors/tests/test.sh
tasks/004-place-heater-for-sensors/tests/test_outputs.py
tasks/005-optimize-cold-plate/README.md
tasks/005-optimize-cold-plate/environment/Dockerfile
tasks/005-optimize-cold-plate/environment/input/task_plan.json
tasks/005-optimize-cold-plate/input/task_plan.json
tasks/005-optimize-cold-plate/instruction.md
tasks/005-optimize-cold-plate/solution/solve.sh
tasks/005-optimize-cold-plate/solution/template_case/0/fluid/T
tasks/005-optimize-cold-plate/solution/template_case/0/fluid/U
tasks/005-optimize-cold-plate/solution/template_case/0/fluid/p
tasks/005-optimize-cold-plate/solution/template_case/0/fluid/p_rgh
tasks/005-optimize-cold-plate/solution/template_case/0/solid/T
tasks/005-optimize-cold-plate/solution/template_case/build_case.py
tasks/005-optimize-cold-plate/solution/template_case/constant/fluid/g
tasks/005-optimize-cold-plate/solution/template_case/constant/fluid/momentumTransport
tasks/005-optimize-cold-plate/solution/template_case/constant/fluid/physicalProperties
tasks/005-optimize-cold-plate/solution/template_case/constant/solid/fvModels
tasks/005-optimize-cold-plate/solution/template_case/constant/solid/physicalProperties
tasks/005-optimize-cold-plate/solution/template_case/design.json
tasks/005-optimize-cold-plate/solution/template_case/extract_metrics.py
tasks/005-optimize-cold-plate/solution/template_case/render_svgs.py
tasks/005-optimize-cold-plate/solution/template_case/run_case.sh
tasks/005-optimize-cold-plate/solution/template_case/system/controlDict
tasks/005-optimize-cold-plate/solution/template_case/system/fluid/fvSchemes
tasks/005-optimize-cold-plate/solution/template_case/system/fluid/fvSolution
tasks/005-optimize-cold-plate/solution/template_case/system/fvSolution
tasks/005-optimize-cold-plate/solution/template_case/system/solid/fvSchemes
tasks/005-optimize-cold-plate/solution/template_case/system/solid/fvSolution
tasks/005-optimize-cold-plate/solution/template_case/system/solidZonesDict
tasks/005-optimize-cold-plate/task.toml
tasks/005-optimize-cold-plate/tests/reference_case/0/fluid/T
tasks/005-optimize-cold-plate/tests/reference_case/0/fluid/U
tasks/005-optimize-cold-plate/tests/reference_case/0/fluid/p
tasks/005-optimize-cold-plate/tests/reference_case/0/fluid/p_rgh
tasks/005-optimize-cold-plate/tests/reference_case/0/solid/T
tasks/005-optimize-cold-plate/tests/reference_case/build_case.py
tasks/005-optimize-cold-plate/tests/reference_case/constant/fluid/g
tasks/005-optimize-cold-plate/tests/reference_case/constant/fluid/momentumTransport
tasks/005-optimize-cold-plate/tests/reference_case/constant/fluid/physicalProperties
tasks/005-optimize-cold-plate/tests/reference_case/constant/solid/fvModels
tasks/005-optimize-cold-plate/tests/reference_case/constant/solid/physicalProperties
tasks/005-optimize-cold-plate/tests/reference_case/design.json
tasks/005-optimize-cold-plate/tests/reference_case/extract_metrics.py
tasks/005-optimize-cold-plate/tests/reference_case/render_svgs.py
tasks/005-optimize-cold-plate/tests/reference_case/run_case.sh
tasks/005-optimize-cold-plate/tests/reference_case/system/controlDict
tasks/005-optimize-cold-plate/tests/reference_case/system/fluid/fvSchemes
tasks/005-optimize-cold-plate/tests/reference_case/system/fluid/fvSolution
tasks/005-optimize-cold-plate/tests/reference_case/system/fvSolution
tasks/005-optimize-cold-plate/tests/reference_case/system/solid/fvSchemes
tasks/005-optimize-cold-plate/tests/reference_case/system/solid/fvSolution
tasks/005-optimize-cold-plate/tests/reference_case/system/solidZonesDict
tasks/005-optimize-cold-plate/tests/test.sh
tasks/005-optimize-cold-plate/tests/test_outputs.py
tasks/006-extract-gym-auditorium/.gitignore
tasks/006-extract-gym-auditorium/README.md
tasks/006-extract-gym-auditorium/environment/Dockerfile
tasks/006-extract-gym-auditorium/environment/input/building.osm
tasks/006-extract-gym-auditorium/environment/input/task_plan.json
tasks/006-extract-gym-auditorium/environment/input/weather.epw
tasks/006-extract-gym-auditorium/environment/task-support/render_openstudio_model.py
tasks/006-extract-gym-auditorium/input/building.osm
tasks/006-extract-gym-auditorium/input/weather.epw
tasks/006-extract-gym-auditorium/instruction.md
tasks/006-extract-gym-auditorium/solution/reference/gym_auditorium_reference.osm
tasks/006-extract-gym-auditorium/solution/solve.sh
tasks/006-extract-gym-auditorium/task.toml
tasks/006-extract-gym-auditorium/tests/reference/gym_auditorium_reference.osm
tasks/006-extract-gym-auditorium/tests/test.sh
tasks/006-extract-gym-auditorium/tests/test_outputs.py
tasks/007-reconstruct-prostate-obj/.gitignore
tasks/007-reconstruct-prostate-obj/README.md
tasks/007-reconstruct-prostate-obj/environment/Dockerfile
tasks/007-reconstruct-prostate-obj/environment/input/task_plan.json
tasks/007-reconstruct-prostate-obj/input/task_plan.json
tasks/007-reconstruct-prostate-obj/instruction.md
tasks/007-reconstruct-prostate-obj/solution/reference/prostate_00_prostate.obj
tasks/007-reconstruct-prostate-obj/solution/solve.sh
tasks/007-reconstruct-prostate-obj/task.toml
tasks/007-reconstruct-prostate-obj/tests/reference/prostate_00_prostate.obj
tasks/007-reconstruct-prostate-obj/tests/test.sh
tasks/007-reconstruct-prostate-obj/tests/test_outputs.py
tasks/008-find-bird-chase-frames/.gitignore
tasks/008-find-bird-chase-frames/README.md
tasks/008-find-bird-chase-frames/environment/Dockerfile
tasks/008-find-bird-chase-frames/environment/input/.gitkeep
tasks/008-find-bird-chase-frames/instruction.md
tasks/008-find-bird-chase-frames/solution/solve.sh
tasks/008-find-bird-chase-frames/task.toml
tasks/008-find-bird-chase-frames/tests/test.sh
tasks/008-find-bird-chase-frames/tests/verify.py
tasks/009-repair-org-chart-layout/.gitignore
tasks/009-repair-org-chart-layout/README.md
tasks/009-repair-org-chart-layout/environment/Dockerfile
tasks/009-repair-org-chart-layout/environment/input/.gitkeep
tasks/009-repair-org-chart-layout/instruction.md
tasks/009-repair-org-chart-layout/solution/solve.sh
tasks/009-repair-org-chart-layout/task.toml
tasks/009-repair-org-chart-layout/tests/reference/.gitkeep
tasks/009-repair-org-chart-layout/tests/test.sh
tasks/009-repair-org-chart-layout/tests/test_outputs.py
tasks/010-pivot-product-revenue/.gitignore
tasks/010-pivot-product-revenue/README.md
tasks/010-pivot-product-revenue/environment/Dockerfile
tasks/010-pivot-product-revenue/instruction.md
tasks/010-pivot-product-revenue/solution/solve.sh
tasks/010-pivot-product-revenue/task.toml
tasks/010-pivot-product-revenue/tests/test.sh
tasks/010-pivot-product-revenue/tests/test_outputs.py
tasks/011-epw-parquet-check/.gitignore
tasks/011-epw-parquet-check/README.md
tasks/011-epw-parquet-check/environment/Dockerfile
tasks/011-epw-parquet-check/environment/input/building.osm
tasks/011-epw-parquet-check/environment/input/task_plan.json
tasks/011-epw-parquet-check/environment/input/weather.epw
tasks/011-epw-parquet-check/input/building.osm
tasks/011-epw-parquet-check/input/task_plan.json
tasks/011-epw-parquet-check/input/weather.epw
tasks/011-epw-parquet-check/instruction.md
tasks/011-epw-parquet-check/solution/solve.sh
tasks/011-epw-parquet-check/task.toml
tasks/011-epw-parquet-check/tests/reference_metrics.json
tasks/011-epw-parquet-check/tests/test.sh
tasks/011-epw-parquet-check/tests/test_outputs.py
tasks/012-hide-na-budget-values/.gitignore
tasks/012-hide-na-budget-values/README.md
… (truncated)
```

## Detected entry points

- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/repo_env/podman_env.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/repo_env/setup_env.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/000-count-nuclei/tests/test_outputs.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/001-locate-nuclei-centers/tests/test_outputs.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/002-count-enter-key-presses/tests/verify.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/003-rebuild-energy-model/tests/test_outputs.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/004-place-heater-for-sensors/tests/test_outputs.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/005-optimize-cold-plate/tests/test_outputs.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/006-extract-gym-auditorium/tests/test_outputs.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/007-reconstruct-prostate-obj/tests/test_outputs.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/008-find-bird-chase-frames/tests/verify.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/009-repair-org-chart-layout/tests/test_outputs.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/010-pivot-product-revenue/tests/test_outputs.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/011-epw-parquet-check/tests/test_outputs.py`
- `projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/external/TUA-Bench/tasks/012-hide-na-budget-values/tests/test_outputs.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `TUA-Bench` — not re-implementing it.
