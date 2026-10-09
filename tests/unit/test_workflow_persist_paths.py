"""Every pipeline lane delegates persistence to the shared guarded profile.

The former test merely found `git add -A` in shell text (including comments)
and therefore could not establish which paths actually reached Git. Real
staging/push coverage lives in test_pipeline_write_profiles.py; this check
pins workflow delegation and the safe default rather than blanket staging.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = ROOT / ".github/workflows"
COMMIT_SCRIPT = ROOT / "scripts/ci/commit-and-push.sh"


def _pass_running_workflows():
    found = [path for path in sorted(WORKFLOWS_DIR.glob("*.yml"))
             if "-m llmxive run" in path.read_text()]
    assert found, "no pass-running workflows found"
    return found


@pytest.mark.parametrize("workflow", _pass_running_workflows(), ids=lambda p: p.name)
def test_pipeline_lane_uses_guarded_research_persistence(workflow):
    text = workflow.read_text()
    assert "commit-and-push.sh" in text, f"{workflow.name} bypasses guarded persistence"
    script = COMMIT_SCRIPT.read_text()
    assert 'profile="${2:-research}"' in script
    assert "pipeline_writes.py" in script and '--profile "$profile" --stage' in script
    # Pages is a separate static deployment job, never a research pass profile.
    calls = [line for line in text.splitlines() if "bash scripts/ci/commit-and-push.sh" in line]
    assert calls
    assert all(not line.rstrip().endswith(" pages") for line in calls)
