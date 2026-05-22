"""Deterministic dataset-source clients (spec: dataset-resolver design).

Each ``search_*`` returns a list of :class:`DatasetCandidate` for a dataset
intent (a name like "QM9" or a DOI). No ranking or verification here — that is
the resolver's job. All network errors are swallowed into an empty list so one
dead source never breaks resolution; the resolver decides what to do with the
union of candidates.
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

USER_AGENT = "llmxive-dataset-resolver/1.0 (https://github.com/ContextLab/llmXive)"
_TIMEOUT = 20


@dataclass(frozen=True)
class DatasetCandidate:
    intent: str
    url: str
    title: str
    source: str
    hf_id: str | None = None


def search_huggingface(intent: str, *, limit: int = 5) -> list[DatasetCandidate]:
    from huggingface_hub import HfApi

    try:
        api = HfApi()
        results = list(api.list_datasets(search=intent, limit=limit))
    except Exception:
        return []
    out: list[DatasetCandidate] = []
    for d in results:
        ds_id = getattr(d, "id", None)
        if not ds_id:
            continue
        out.append(DatasetCandidate(
            intent=intent,
            url=f"https://huggingface.co/datasets/{ds_id}",
            title=ds_id,
            source="huggingface",
            hf_id=ds_id,
        ))
    return out
