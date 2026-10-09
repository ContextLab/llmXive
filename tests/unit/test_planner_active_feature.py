"""Planner setup uses the persisted feature and preserves revision inputs."""
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.speckit.plan_cmd import PlannerAgent
from llmxive.state import project as project_store
from llmxive.types import Project, Stage
from tests.unit.test_plan_revision_loop import (
    _BAD_CONTRACT_MULTI_DOC,
    _make_planner_ctx,
    _valid_five_file_block,
)


def _project(tmp_path, monkeypatch):
    ctx, mech, feature = _make_planner_ctx(tmp_path)
    ctx.project_id = "PROJ-901-plan-revloop"
    root = Path(__file__).resolve().parents[2]
    shutil.copytree(root/'.specify/scripts', ctx.project_dir/'.specify/scripts')
    shutil.copytree(root/'.specify/templates', ctx.project_dir/'.specify/templates')
    subprocess.run(['git','init','-q','-b','main',str(tmp_path)],check=True)
    now = datetime.now(UTC)
    project_store.save(Project(id=ctx.project_id,title='test',field='mathematics',
        current_stage=Stage.CLARIFIED,created_at=now,updated_at=now,
        speckit_research_dir=str(feature.relative_to(tmp_path))),repo_root=tmp_path)
    monkeypatch.setattr('llmxive.execution.data_source.requires_external_data',lambda _:False)
    monkeypatch.setattr(PlannerAgent,'_plan_time_discovered_block',staticmethod(lambda _:''))
    return ctx, mech, feature


@pytest.mark.parametrize('metadata',['missing','stale','ambiguous'])
def test_new_plan_uses_authoritative_feature_on_parent_main(tmp_path,monkeypatch,metadata):
    ctx, _, feature = _project(tmp_path,monkeypatch)
    old = ctx.project_dir/('specs/001-duplicate' if metadata == 'ambiguous' else 'specs/999-stale')
    old.mkdir()
    (old/'plan.md').write_text('Preserved unrelated feature plan\n')
    if metadata == 'stale':
        (ctx.project_dir/'.specify/feature.json').write_text(json.dumps({'feature_directory':str(old)}))
    result = PlannerAgent().mechanical_step(ctx)
    assert Path(result['script_result']['SPECS_DIR']).resolve() == feature.resolve()
    assert (feature/'plan.md').is_file()
    assert (old/'plan.md').read_text() == 'Preserved unrelated feature plan\n'
    assert subprocess.check_output(['git','symbolic-ref','--short','HEAD'],cwd=tmp_path,text=True).strip() == 'main'


def test_replanning_keeps_existing_plan_and_supplies_it_to_model(tmp_path,monkeypatch):
    ctx, _, feature = _project(tmp_path,monkeypatch)
    original = '# Existing Plan\nReuse the validated sieve and preserve p=5,7,11.\n'
    (feature/'plan.md').write_text(original)
    (feature/'quickstart.md').write_text('python -m src.run --max-n 1000000\n')
    result = PlannerAgent().mechanical_step(ctx)
    assert (feature/'plan.md').read_text() == original
    prompt = PlannerAgent().build_prompt(ctx,result)[-1].content
    assert original in prompt
    assert 'python -m src.run --max-n 1000000' in prompt
    assert 'Preserve unaffected requirements' in prompt


def test_rejected_revision_restores_prior_artifacts_instead_of_deleting(tmp_path):
    ctx, mech, feature = _make_planner_ctx(tmp_path)
    prior = {'plan.md':b'Prior valid plan\n','research.md':b'Prior references\n',
             'contracts/clone-cluster.schema.yaml':b'title: Existing schema\n'}
    for rel, content in prior.items():
        path = feature/rel
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(content)
    from llmxive.speckit._research_guard import InconsistentDataModel
    with pytest.raises(InconsistentDataModel):
        PlannerAgent()._write_and_validate(ctx,mech,
            _valid_five_file_block(bad_contract=_BAD_CONTRACT_MULTI_DOC))
    for rel, content in prior.items():
        assert (feature/rel).read_bytes() == content
    assert not (feature/'quickstart.md').exists()
