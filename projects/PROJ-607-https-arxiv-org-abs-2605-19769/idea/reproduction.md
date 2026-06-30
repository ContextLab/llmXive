# Reproduce & validate: OpenComputer: Verifiable Software Worlds for Computer-Use Agents

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/   (clone of https://github.com/echo0715/OpenComputer)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** OpenComputer: Verifiable Software Worlds for Computer-Use Agents

**Abstract:** We present OpenComputer, a verifier-grounded framework for constructing verifiable software worlds for computer-use agents. OpenComputer integrates four components: (1) app-specific state verifiers that expose structured inspection endpoints over real applications, (2) a self-evolving verification layer that improves verifier reliability using execution-grounded feedback, (3) a task-generation pipeline that synthesizes realistic and machine-checkable desktop tasks, and (4) an evaluation harness that records full trajectories and computes auditable partial-credit rewards. In its current form, OpenComputer covers 33 desktop applications and 1,000 finalized tasks spanning browsers, office tools, creative software, development environments, file managers, and communication applications. Experiments show that OpenComputer's hard-coded verifiers align more closely with human adjudication than LLM-as-judge evaluation, especially when success depends on fine-grained application state. Frontier agents struggle with end-to-end completion despite partial progress, and open-source models exhibit sharp drops from their OSWorld-Verified scores, exposing a persistent gap in robust computer automation.

## Shipped code — file tree (`projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/`)

```
.claude/hooks/block_verifier_reads.py
.claude/settings.json
.env.example
.gitignore
CLAUDE.md
LICENSE
README.md
agents/__init__.py
agents/base.py
agents/chatgpt_agent.py
agents/claude_agent.py
agents/dart_agent.py
agents/evocua_agent.py
agents/gemini_agent.py
agents/kimi_agent.py
agents/mano_agent.py
agents/opencua_agent.py
agents/owl15_agent.py
agents/qwen_agent.py
agents/registry.py
computer_env/README.md
computer_env/__init__.py
computer_env/backends/__init__.py
computer_env/backends/base.py
computer_env/backends/docker/cleanup_containers.py
computer_env/backends/docker/runtime.py
computer_env/backends/e2b/cleanup_sandboxes.py
computer_env/backends/e2b/runtime.py
computer_env/backends/e2b/sandbox_cli.py
computer_env/backends/remote_docker/__init__.py
computer_env/backends/remote_docker/runtime.py
computer_env/backends/remote_docker/worker_client.py
computer_env/config.py
computer_env/factory.py
computer_env/provision/__init__.py
computer_env/provision/aws/AWS_SSO_SETUP.md
computer_env/provision/aws/README.md
computer_env/provision/aws/__init__.py
computer_env/provision/aws/launch_workers.py
computer_env/provision/aws/setup_prereqs.py
computer_env/provision/aws/terminate_workers.py
computer_env/provision/aws/worker_agent/app.py
computer_env/provision/aws/worker_agent/requirements.txt
computer_env/provision/aws/worker_agent/systemd/gui-synth-worker.service
computer_env/provision/aws/worker_user_data.sh
computer_env/provision/docker/Dockerfile
computer_env/provision/docker/README.md
computer_env/provision/docker/__init__.py
computer_env/provision/docker/build_image.sh
computer_env/provision/docker/entrypoint.sh
computer_env/provision/docker/healthcheck.sh
computer_env/provision/docker/install_app_wrappers.py
computer_env/provision/docker/install_app_wrappers.sh
computer_env/provision/e2b/README.md
computer_env/provision/e2b/__init__.py
computer_env/provision/e2b/build_all_apps_template.py
computer_env/provision/remote_docker/__init__.py
computer_env/provision/remote_docker/stream_dashboard.py
computer_env/provision/tencentcloud/README.md
computer_env/provision/tencentcloud/README_zh.md
computer_env/provision/tencentcloud/TENCENTCLOUD_SETUP.md
computer_env/provision/tencentcloud/TENCENTCLOUD_SETUP_zh.md
computer_env/provision/tencentcloud/__init__.py
computer_env/provision/tencentcloud/api.py
computer_env/provision/tencentcloud/launch_workers.py
computer_env/provision/tencentcloud/setup_prereqs.py
computer_env/provision/tencentcloud/terminate_workers.py
computer_env/provision/tencentcloud/worker_user_data.sh
dashboard/server.py
dashboard/static/index.html
dashboard/static/opencomputer.svg
docs/demo.html
docs/index.html
docs/opencomputer-white.svg
docs/opencomputer.svg
evaluation/apps/__init__.py
evaluation/apps/base.py
evaluation/apps/launcher_contract.py
evaluation/apps/registry.py
evaluation/apps/save.py
evaluation/apps/specs/__init__.py
evaluation/apps/specs/audacity.py
evaluation/apps/specs/blender.py
evaluation/apps/specs/brave.py
evaluation/apps/specs/chrome.py
evaluation/apps/specs/cloudcompare.py
evaluation/apps/specs/darktable.py
evaluation/apps/specs/drawio.py
evaluation/apps/specs/eclipse.py
evaluation/apps/specs/firefox.py
evaluation/apps/specs/freecad.py
evaluation/apps/specs/galculator.py
evaluation/apps/specs/gedit.py
evaluation/apps/specs/gimp.py
evaluation/apps/specs/godot4.py
evaluation/apps/specs/inkscape.py
evaluation/apps/specs/kdenlive.py
evaluation/apps/specs/krita.py
evaluation/apps/specs/libreoffice_calc.py
evaluation/apps/specs/libreoffice_draw.py
evaluation/apps/specs/libreoffice_impress.py
evaluation/apps/specs/libreoffice_writer.py
evaluation/apps/specs/musescore3.py
evaluation/apps/specs/obs.py
evaluation/apps/specs/obsidian.py
evaluation/apps/specs/pcmanfm.py
evaluation/apps/specs/renderdoc.py
evaluation/apps/specs/shotcut.py
evaluation/apps/specs/thunderbird.py
evaluation/apps/specs/vlc.py
evaluation/apps/specs/vscode.py
evaluation/apps/specs/zoom.py
evaluation/apps/specs/zotero.py
evaluation/apps/utils.py
evaluation/interactive_sandbox.py
evaluation/llm_judge.md
evaluation/repair/README.md
evaluation/repair/prompts/comparator.md
evaluation/repair/prompts/judge.md
evaluation/repair/prompts/repair.md
evaluation/repair/repair_loop.py
evaluation/run_eval.py
evaluation/run_eval_from_run.py
evaluation/runtime/__init__.py
evaluation/runtime/agent_runner.py
evaluation/runtime/reporting.py
evaluation/runtime/run_config.py
evaluation/runtime/sandbox_session.py
evaluation/runtime/task_runner.py
evaluation/runtime/tasks.py
evaluation/runtime/verification.py
requirements.txt
smoke/CLAUDE.md
smoke/README.md
smoke/prompts/smoke_task_gen.md
smoke/smoke_loop.py
task_generator/CLAUDE.md
task_generator/ENDPOINT_EXTENSION.md
task_generator/LESSONS.md
task_generator/README.md
task_generator/TASK_EXTENSION.md
task_generator/tasks/COVERAGE_GAPS.md
task_generator/tasks/_build_draw_v2_envs.py
task_generator/tasks/_calc_v2_gen_env.py
task_generator/tasks/_calc_v2_gen_env_new.py
task_generator/tasks/_cloudcompare_v2_gen.py
task_generator/tasks/_eclipse_v2_gen_env.py
task_generator/tasks/_freecad_gap_gen.py
task_generator/tasks/_freecad_v2_gen/build_envs.py
task_generator/tasks/_freecad_v2_gen/gen_fcstd.py
task_generator/tasks/_gen_darktable_gap_envs.py
task_generator/tasks/_gen_darktable_gap_manifests.py
task_generator/tasks/_gen_gimp_gap_envs.py
task_generator/tasks/_gen_inkscape_gap_envs.py
task_generator/tasks/_gen_krita_envs.py
task_generator/tasks/_gen_krita_gaps_envs.py
task_generator/tasks/_gen_krita_r2_envs.py
task_generator/tasks/_gen_krita_v3_envs.py
task_generator/tasks/_gen_obs_v2_envs.py
task_generator/tasks/_gen_zotero_gaps.py
task_generator/tasks/_musescore3_gen_env.py
task_generator/tasks/_musescore3_gen_env_gap.py
task_generator/tasks/_musescore3_gen_env_harder.py
task_generator/tasks/_musescore3_gen_env_v2.py
task_generator/tasks/_shotcut_v2_gen_env.py
task_generator/tasks/_thicken_verification.py
task_generator/tasks/_vlc_v2_gen.py
task_generator/tasks/audacity_add_chapter_labels/env/audiobook.aup
task_generator/tasks/audacity_add_chapter_labels/env/audiobook_data/e00/d00/e000001.au
task_generator/tasks/audacity_add_chapter_labels/env_manifest.json
task_generator/tasks/audacity_add_chapter_labels/task.json
task_generator/tasks/audacity_change_project_rate_48k/env/project.aup
task_generator/tasks/audacity_change_project_rate_48k/env/project_data/e00/d00/e000001.au
task_generator/tasks/audacity_change_project_rate_48k/env_manifest.json
task_generator/tasks/audacity_change_project_rate_48k/task.json
task_generator/tasks/audacity_export_flac_mono/env/input.wav
task_generator/tasks/audacity_export_flac_mono/env_manifest.json
task_generator/tasks/audacity_export_flac_mono/task.json
task_generator/tasks/audacity_export_mp3_stereo/env/source.wav
task_generator/tasks/audacity_export_mp3_stereo/env_manifest.json
task_generator/tasks/audacity_export_mp3_stereo/task.json
task_generator/tasks/audacity_export_ogg_vorbis/env/voice.wav
task_generator/tasks/audacity_export_ogg_vorbis/env_manifest.json
task_generator/tasks/audacity_export_ogg_vorbis/task.json
task_generator/tasks/audacity_export_segment_wav/env/long.wav
task_generator/tasks/audacity_export_segment_wav/env_manifest.json
task_generator/tasks/audacity_export_segment_wav/task.json
task_generator/tasks/audacity_export_wav_440/env/tone.wav
task_generator/tasks/audacity_export_wav_440/env_manifest.json
task_generator/tasks/audacity_export_wav_440/task.json
task_generator/tasks/audacity_export_with_project_metadata/env/song.aup
task_generator/tasks/audacity_export_with_project_metadata/env/song_data/e00/d00/e000001.au
task_generator/tasks/audacity_export_with_project_metadata/env/song_data/e00/d00/e000002.au
task_generator/tasks/audacity_export_with_project_metadata/env_manifest.json
task_generator/tasks/audacity_export_with_project_metadata/task.json
task_generator/tasks/audacity_gap_amplify_export/env/quiet.wav
task_generator/tasks/audacity_gap_amplify_export/env_manifest.json
task_generator/tasks/audacity_gap_amplify_export/task.json
task_generator/tasks/audacity_gap_cut_middle_export/env/long.wav
task_generator/tasks/audacity_gap_cut_middle_export/env_manifest.json
… (truncated)
```

## Detected entry points

- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/task_generator/tasks/pcmanfm_cleanup_temp_files/env/main.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/task_generator/tasks/pcmanfm_multi_extension_split/env/main.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/base.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/chatgpt_agent.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/claude_agent.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/dart_agent.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/evocua_agent.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/gemini_agent.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/kimi_agent.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/mano_agent.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/opencua_agent.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/owl15_agent.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/qwen_agent.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/agents/registry.py`
- `projects/PROJ-607-https-arxiv-org-abs-2605-19769/external/OpenComputer/computer_env/config.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `OpenComputer` — not re-implementing it.
