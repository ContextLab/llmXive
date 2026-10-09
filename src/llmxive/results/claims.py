"""Ground result prose only in current, signed execution artifacts."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from llmxive.claims.models import Claim, ClaimStatus, Verdict
from llmxive.results.harness import result_backed, source_fingerprint
from llmxive.state import results


def evidence_fingerprint(evidence: dict[str, Any], project_id: str, repo: Path) -> str | None:
    """Revalidate every artifact supporting a cached result claim."""
    sources = evidence.get('result_artifacts')
    if not isinstance(sources, list) or not sources:
        return None
    fingerprints = []
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get('path'), str):
            return None
        receipt = result_backed(source['path'], project_id, repo_root=repo)
        if receipt is None or receipt.kind != 'table':
            return None
        digest = source_fingerprint(receipt)
        if digest != source.get('sha256'):
            return None
        fingerprints.append([receipt.value, digest])
    return hashlib.sha256(json.dumps(sorted(fingerprints)).encode()).hexdigest()


def resolve_artifact_claim(claim: Claim, *, project_id: str, backend: Any,
                           model: str | None, repo_root: Path) -> Verdict:
    """Receipts authenticate bytes; entailment checks what those bytes assert.

    This does not establish that the experiment's scientific method is valid.
    Never search the web, fill absent measurements, mint receipts, or accept a
    model assertion without authenticated source text and a verbatim quotation.
    """
    from llmxive.grounding.entailment import assess
    from llmxive.grounding.full_text import RetrievedDoc
    from llmxive.grounding.service import number_substantiated

    evidence: dict[str, Any] = {'result_artifacts': []}
    chunks = []
    remaining = 24000
    for stored in results.load_all(project_id, repo_root=repo_root):
        if stored.kind != 'table' or Path(stored.value).suffix.lower() not in {'.csv', '.tsv', '.json'}:
            continue
        receipt = result_backed(stored.value, project_id, repo_root=repo_root)
        if receipt is None:
            continue
        path = repo_root / 'projects' / project_id / receipt.value
        try:
            if path.stat().st_size > remaining:
                continue
            with path.open('rb') as stream:
                raw = stream.read(remaining + 1)
            if len(raw) > remaining or hashlib.sha256(raw).hexdigest() != receipt.captured['sha256']:
                continue
            body = raw.decode('utf-8')
        except (OSError, UnicodeError):
            continue
        chunks.append(f"Artifact {receipt.value}:\n{body}")
        evidence['result_artifacts'].append({'path': receipt.value, 'sha256': source_fingerprint(receipt)})
        remaining -= len(raw)
        if len(chunks) >= 32:
            break
    source_hash = evidence_fingerprint(evidence, project_id, repo_root)
    if not chunks or not source_hash:
        return Verdict(ClaimStatus.NOT_ENOUGH_INFO, None,
                       {'note': 'no current signed text artifacts backing this result'},
                       'resolve_result')
    text = '\n\n'.join(chunks)
    doc = RetrievedDoc('result', project_id, 'signed-artifact', text, None,
                       'Authenticated execution artifacts', '')
    verdict = assess(claim.raw_text, doc, backend=backend, model=model, repo_root=repo_root)
    evidence.update(quote=verdict.evidence, note=verdict.note, artifact_sha256=source_hash)
    # All reported numbers must appear, not merely the first parameter value.
    numbers = re.findall(r'\d[\d,_]*(?:\.\d+)?(?:[eE][+-]?\d+)?', claim.raw_text)
    if evidence_fingerprint(evidence, project_id, repo_root) != source_hash:
        evidence['note'] = 'supporting artifacts changed during verification'
        return Verdict(ClaimStatus.NOT_ENOUGH_INFO, None, evidence, 'resolve_result')
    if verdict.status == 'grounded' and all(number_substantiated(n, text) for n in numbers):
        # Return the original prose, never replace it with a file path or a
        # model-generated "corrected" result.
        return Verdict(ClaimStatus.VERIFIED, claim.raw_text, evidence, 'resolve_result')
    status = ClaimStatus.REFUTED if verdict.status == 'contradicted' else ClaimStatus.NOT_ENOUGH_INFO
    return Verdict(status, None, evidence, 'resolve_result')
