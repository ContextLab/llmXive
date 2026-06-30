# Reproduce & validate: Agents' Last Exam

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-688-agents-last-exam/external/agents-last-exam/   (clone of https://github.com/rdi-berkeley/agents-last-exam)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Agents' Last Exam

**Abstract:** Recent AI systems have achieved strong results on a wide range of benchmarks, yet these gains have not translated into economically meaningful deployment across many professional domains. We argue that this gap is largely an evaluation problem: widely used benchmarks lack sustained performance measurement on real and economically valuable workflows. This paper introduces Agents' Last Exam (ALE), a benchmark designed to evaluate AI agents on long-horizon, economically valuable, real-world tasks with verifiable outcomes. Developed in collaboration with 250+ industry experts, ALE covers non-physical industries defined with reference to O*NET / SOC 2018 (the U.S. federal occupational taxonomy). It is organized around a task taxonomy with 55 subfields grouped into 13 industry clusters covering 1K+ tasks. Current results show that the hardest tier remains far from saturated: across mainstream harness and backbone configurations, the average full pass rate is 2.6%. ALE is designed as a living benchmark: its task pool grows continuously as new workflows and industries are onboarded. More broadly, ALE is intended not merely as another leaderboard, but as an instrument for closing the gap between benchmark success and GDP-relevant impact.

## Shipped code — file tree (`projects/PROJ-688-agents-last-exam/external/agents-last-exam/`)

```
.dockerignore
.gitignore
.gitmodules
AGENTS.md
LICENSE
LICENSE-DATA
README.md
ale_run/__main__.py
ale_run/agents/_assets/cua_mcp_server/README.md
ale_run/agents/_assets/cua_mcp_server/package-lock.json
ale_run/agents/_assets/cua_mcp_server/package.json
ale_run/agents/_assets/cua_mcp_server/src/cua-client.js
ale_run/agents/_assets/cua_mcp_server/src/index.js
ale_run/agents/_assets/vm_mcp_server/README.md
ale_run/agents/_assets/vm_mcp_server/package-lock.json
ale_run/agents/_assets/vm_mcp_server/package.json
ale_run/agents/_assets/vm_mcp_server/src/index.js
ale_run/agents/_assets/vm_mcp_server/src/vm-client.js
ale_run/agents/_bootstrap.py
ale_run/agents/ale_claw/README.md
ale_run/agents/ale_claw/__init__.py
ale_run/agents/ale_claw/config.py
ale_run/agents/ale_claw/deployer.py
ale_run/agents/ale_claw/harness/AGENTS.md
ale_run/agents/ale_claw/harness/AUDIT.md
ale_run/agents/ale_claw/harness/__init__.py
ale_run/agents/ale_claw/harness/adapters/__init__.py
ale_run/agents/ale_claw/harness/adapters/image_retention.py
ale_run/agents/ale_claw/harness/adapters/trajectory_saver.py
ale_run/agents/ale_claw/harness/agent_loop.py
ale_run/agents/ale_claw/harness/agent_loop_helpers.py
ale_run/agents/ale_claw/harness/canonical/__init__.py
ale_run/agents/ale_claw/harness/canonical/canonical.py
ale_run/agents/ale_claw/harness/canonical/canonical_sanitize.py
ale_run/agents/ale_claw/harness/canonical/canonical_types.py
ale_run/agents/ale_claw/harness/context/README.md
ale_run/agents/ale_claw/harness/context/__init__.py
ale_run/agents/ale_claw/harness/context/compaction.py
ale_run/agents/ale_claw/harness/context/context.py
ale_run/agents/ale_claw/harness/context/replay.py
ale_run/agents/ale_claw/harness/context/token_estimation.py
ale_run/agents/ale_claw/harness/context/transcript.py
ale_run/agents/ale_claw/harness/memory/README.md
ale_run/agents/ale_claw/harness/memory/__init__.py
ale_run/agents/ale_claw/harness/memory/memory.py
ale_run/agents/ale_claw/harness/memory/memory_flush.py
ale_run/agents/ale_claw/harness/memory/memory_flush_policy.py
ale_run/agents/ale_claw/harness/model/__init__.py
ale_run/agents/ale_claw/harness/model/_message_shapes.py
ale_run/agents/ale_claw/harness/model/cache_policy.py
ale_run/agents/ale_claw/harness/model/helper_runtime.py
ale_run/agents/ale_claw/harness/model/image_sanitization.py
ale_run/agents/ale_claw/harness/model/model_config.py
ale_run/agents/ale_claw/harness/model/thinking.py
ale_run/agents/ale_claw/harness/model/unified_loop.py
ale_run/agents/ale_claw/harness/prompt.py
ale_run/agents/ale_claw/harness/session.py
ale_run/agents/ale_claw/harness/subagent/README.md
ale_run/agents/ale_claw/harness/subagent/__init__.py
ale_run/agents/ale_claw/harness/subagent/subagent_general.py
ale_run/agents/ale_claw/harness/subagent/subagent_gui.py
ale_run/agents/ale_claw/harness/subagent/subagent_gui_protocol.py
ale_run/agents/ale_claw/harness/subagent/subagent_registry.py
ale_run/agents/ale_claw/harness/subagent/subagent_session.py
ale_run/agents/ale_claw/harness/subagent/subagent_tools.py
ale_run/agents/ale_claw/harness/tools/README.md
ale_run/agents/ale_claw/harness/tools/__init__.py
ale_run/agents/ale_claw/harness/tools/_paths.py
ale_run/agents/ale_claw/harness/tools/_tool_utils.py
ale_run/agents/ale_claw/harness/tools/analyze_image.py
ale_run/agents/ale_claw/harness/tools/computer_handler.py
ale_run/agents/ale_claw/harness/tools/fs_backends.py
ale_run/agents/ale_claw/harness/tools/mcp_runtime.py
ale_run/agents/ale_claw/harness/tools/tools.py
ale_run/agents/ale_claw/harness/tools/tools_fs.py
ale_run/agents/ale_claw/harness/tools/tools_shell.py
ale_run/agents/ale_claw/harness/tools/tools_web.py
ale_run/agents/ale_claw/pyproject.toml
ale_run/agents/ale_claw/transcript_to_trajectory.py
ale_run/agents/claude_code/__init__.py
ale_run/agents/claude_code/config.py
ale_run/agents/claude_code/deployer.py
ale_run/agents/claude_code/pyproject.toml
ale_run/agents/codex/AGENTS.md
ale_run/agents/codex/README.md
ale_run/agents/codex/__init__.py
ale_run/agents/codex/config.py
ale_run/agents/codex/deployer.py
ale_run/agents/codex/pyproject.toml
ale_run/agents/cursor_cli/AGENTS.md
ale_run/agents/cursor_cli/README.md
ale_run/agents/cursor_cli/__init__.py
ale_run/agents/cursor_cli/config.py
ale_run/agents/cursor_cli/deployer.py
ale_run/agents/cursor_cli/pyproject.toml
ale_run/agents/droid/AGENTS.md
ale_run/agents/droid/README.md
ale_run/agents/droid/__init__.py
ale_run/agents/droid/config.py
ale_run/agents/droid/deployer.py
ale_run/agents/droid/pyproject.toml
ale_run/agents/dummy/__init__.py
ale_run/agents/dummy/config.py
ale_run/agents/dummy/deployer.py
ale_run/agents/dummy/pathscan.py
ale_run/agents/dummy/pyproject.toml
ale_run/agents/forgecode/AGENTS.md
ale_run/agents/forgecode/README.md
ale_run/agents/forgecode/__init__.py
ale_run/agents/forgecode/config.py
ale_run/agents/forgecode/deployer.py
ale_run/agents/forgecode/pyproject.toml
ale_run/agents/gemini_cli/AGENTS.md
ale_run/agents/gemini_cli/README.md
ale_run/agents/gemini_cli/__init__.py
ale_run/agents/gemini_cli/config.py
ale_run/agents/gemini_cli/deployer.py
ale_run/agents/gemini_cli/pyproject.toml
ale_run/agents/grok_cli/AGENTS.md
ale_run/agents/grok_cli/README.md
ale_run/agents/grok_cli/__init__.py
ale_run/agents/grok_cli/config.py
ale_run/agents/grok_cli/deployer.py
ale_run/agents/grok_cli/pyproject.toml
ale_run/agents/hermes/AGENTS.md
ale_run/agents/hermes/README.md
ale_run/agents/hermes/__init__.py
ale_run/agents/hermes/config.py
ale_run/agents/hermes/deployer.py
ale_run/agents/hermes/pyproject.toml
ale_run/agents/openclaw_cli/AGENTS.md
ale_run/agents/openclaw_cli/README.md
ale_run/agents/openclaw_cli/__init__.py
ale_run/agents/openclaw_cli/config.py
ale_run/agents/openclaw_cli/deployer.py
ale_run/agents/openclaw_cli/pyproject.toml
ale_run/agents/openhands_cli/AGENTS.md
ale_run/agents/openhands_cli/README.md
ale_run/agents/openhands_cli/__init__.py
ale_run/agents/openhands_cli/config.py
ale_run/agents/openhands_cli/deployer.py
ale_run/agents/openhands_cli/pyproject.toml
ale_run/agents/terminus_2/AGENTS.md
ale_run/agents/terminus_2/README.md
ale_run/agents/terminus_2/__init__.py
ale_run/agents/terminus_2/config.py
ale_run/agents/terminus_2/deployer.py
ale_run/agents/terminus_2/pyproject.toml
ale_run/base_interface/__init__.py
ale_run/base_interface/agent_deployer.py
ale_run/base_interface/executor.py
ale_run/base_interface/sandbox.py
ale_run/base_interface/task_data.py
ale_run/base_interface/trajectory.py
ale_run/cli.py
ale_run/environments/__init__.py
ale_run/environments/env.py
ale_run/environments/images/__init__.py
ale_run/environments/images/ale_kasm/Dockerfile
ale_run/environments/images/ale_kasm/src/ubuntu/install/firefox/custom_startup.sh
ale_run/environments/images/ale_kasm/src/ubuntu/install/firefox/firefox.desktop
ale_run/environments/images/ale_kasm/src/ubuntu/install/firefox/install_firefox.sh
ale_run/environments/images/ale_kasm.py
ale_run/environments/images/ale_qemu/Dockerfile
ale_run/environments/images/ale_qemu/README.md
ale_run/environments/images/ale_qemu/entrypoint.sh
ale_run/environments/images/ale_qemu/healthcheck.sh
ale_run/environments/images/ale_ubuntu22.py
ale_run/environments/images/ale_ubuntu22_docker/README.md
ale_run/environments/images/ale_ubuntu22_docker/bake_nested_images.sh
ale_run/environments/images/ale_ubuntu22_docker/build.sh
ale_run/environments/images/ale_ubuntu22_docker/cleanup.sh
ale_run/environments/images/ale_ubuntu22_docker/entrypoint.sh
ale_run/environments/images/ale_ubuntu22_docker/export_rootfs.sh
ale_run/environments/images/ale_ubuntu22_docker.py
ale_run/environments/images/ale_win10.py
ale_run/environments/images/ale_win_server.py
ale_run/environments/output_pull.py
ale_run/environments/providers/__init__.py
ale_run/environments/providers/aws.py
ale_run/environments/providers/docker.py
ale_run/environments/providers/gcloud.py
ale_run/environments/providers/qemu.py
ale_run/environments/providers/static.py
ale_run/environments/task_data/__init__.py
ale_run/environments/task_data/baked_in_sandbox.py
ale_run/environments/task_data/gsbucket.py
ale_run/environments/task_data/huggingface.py
ale_run/environments/task_data/local_host.py
ale_run/environments/task_data/s3bucket.py
ale_run/executors/Dockerfile.native_base
ale_run/executors/__init__.py
ale_run/executors/_docker_entry.py
ale_run/executors/_sandbox_entry.py
ale_run/executors/_secrets.py
ale_run/executors/docker.py
ale_run/executors/local.py
ale_run/executors/sandbox.py
ale_run/orchestration/__init__.py
ale_run/orchestration/config_loader.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/agriculture_env/crop_rotation_d02/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/agriculture_env/ndvi_zonal_statistics_d02/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/american_option_pricing_ls/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/ar_full_1500/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/ar_full_300/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/basel_operational_risk_bia_cn/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/bpmn_category_governance_restructuring_l3/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/bpmn_supply_disruption_l3/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/digital_marketing_ab_test_analysis_1/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/digital_marketing_audience_segmentation_1/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/equity_research_summary/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/ff5_public_reconstruction/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/financial_stmt_reconstruction_aapl_fy2024/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/internal_employee_agent_instance_1/main.py`
- `projects/PROJ-688-agents-last-exam/external/agents-last-exam/tasks/business_finance/legal_ma_consistency_audit_01/main.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `agents-last-exam` — not re-implementing it.
