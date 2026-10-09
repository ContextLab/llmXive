"""Task instructions are executable requirements, not empirical result claims."""
from pathlib import Path

from llmxive.claims.pointer import _CLAIM_POINTER_RE, pointer_ids
from llmxive.state import claims as claim_store


def restore_requirements(text: str, *, artifact_path: str, project_id: str, repo_root: Path):
    """Recover exact stored spans, never a resolver's paraphrased factual value."""
    ids = pointer_ids(text)
    if not ids:
        return text, []
    originals = {c.claim_id: c.raw_text for c in claim_store.load(project_id, repo_root=repo_root)
                 if c.artifact_path == artifact_path and c.raw_text}
    def expand(match, seen=frozenset()):
        claim_id = match['id']
        if claim_id in seen or claim_id not in originals or len(seen) >= 64:
            return match[0]
        return _CLAIM_POINTER_RE.sub(
            lambda nested: expand(nested, seen | {claim_id}), originals[claim_id])

    restored = _CLAIM_POINTER_RE.sub(expand, text)
    return restored, pointer_ids(restored)


def read_task_document(path: Path, project_dir: Path, *, project_id: str | None = None,
                       repo_root: Path | None = None, persist: bool = False) -> str:
    text = path.read_text(encoding='utf-8') if path.exists() else ''
    if not pointer_ids(text):
        return text
    repo = repo_root or project_dir.parent.parent
    restored, missing = restore_requirements(text, artifact_path=str(path.relative_to(repo)),
        project_id=project_id or project_dir.name, repo_root=repo)
    if missing:
        from llmxive.speckit.task_lines import TaskFormatError
        raise TaskFormatError(f'Task requirements lost behind claim pointers {missing}; '
                              'restore their original instructions from the specification')
    if persist and restored != text:
        from llmxive.state._io import atomic_write_text
        atomic_write_text(path, restored)
    return restored
