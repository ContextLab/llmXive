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


# Data-file extensions the resolver can sample-stream + sniff. The HF dataset
# landing page is HTML (rejected by the sniffer), so the candidate URL must
# point at an actual data file via the HF resolve URL (design: "HF resolve URL"
# / "stream first rows"). Order encodes preference (most sniffable first).
_HF_DATA_EXTS = (
    ".parquet", ".csv", ".tsv", ".jsonl", ".json",
    ".h5", ".hdf5", ".zip", ".gz", ".npz", ".npy",
    ".arrow", ".feather", ".xyz", ".sdf", ".txt",
)


def _hf_pick_data_file(api, ds_id: str) -> str | None:
    """Deterministically pick the best sample-able data file in an HF dataset.

    Returns the in-repo path (e.g. ``data/train-...parquet``) or ``None`` when
    the dataset exposes no recognizable data file.
    """
    try:
        info = api.dataset_info(ds_id)
    except Exception:
        return None
    files = [
        getattr(s, "rfilename", None)
        for s in (getattr(info, "siblings", None) or [])
    ]
    files = [f for f in files if f and not f.startswith(".")]
    candidates = [f for f in files if f.lower().endswith(_HF_DATA_EXTS)]
    if not candidates:
        return None
    # Stable, deterministic order: by extension preference, then path.
    def _rank(path: str) -> tuple[int, str]:
        lower = path.lower()
        for i, ext in enumerate(_HF_DATA_EXTS):
            if lower.endswith(ext):
                return (i, path)
        return (len(_HF_DATA_EXTS), path)

    candidates.sort(key=_rank)
    return candidates[0]


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
        data_file = _hf_pick_data_file(api, ds_id)
        if not data_file:
            continue
        out.append(DatasetCandidate(
            intent=intent,
            url=f"https://huggingface.co/datasets/{ds_id}/resolve/main/{data_file}",
            title=ds_id,
            source="huggingface",
            hf_id=ds_id,
        ))
    return out


def _get_json(url: str, *, params: dict | None = None) -> dict | list | None:
    try:
        r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=_TIMEOUT)
        if r.status_code != 200:
            return None
        return r.json()
    except (requests.RequestException, ValueError, OSError):
        return None


def search_figshare(intent: str, *, limit: int = 5) -> list[DatasetCandidate]:
    data = _get_json("https://api.figshare.com/v2/articles", params={"search_for": intent, "page_size": limit})
    out: list[DatasetCandidate] = []
    for item in data or []:
        url = item.get("url_public_html") or item.get("url")
        if url:
            out.append(DatasetCandidate(intent, url, item.get("title", ""), "figshare"))
    return out


def search_zenodo(intent: str, *, limit: int = 5) -> list[DatasetCandidate]:
    data = _get_json("https://zenodo.org/api/records", params={"q": intent, "size": limit})
    hits = ((data or {}).get("hits") or {}).get("hits") or []
    out: list[DatasetCandidate] = []
    for h in hits:
        url = (h.get("links") or {}).get("html") or h.get("doi_url")
        if url:
            out.append(DatasetCandidate(intent, url, (h.get("metadata") or {}).get("title", ""), "zenodo"))
    return out


def search_datacite(intent: str, *, limit: int = 5) -> list[DatasetCandidate]:
    # intent may be a DOI (resolve) or a free-text query (search).
    looks_doi = intent.strip().lower().startswith("10.")
    params = {"query": intent, "page[size]": limit} if not looks_doi else None
    url = f"https://api.datacite.org/dois/{intent}" if looks_doi else "https://api.datacite.org/dois"
    data = _get_json(url, params=params)
    records = []
    if looks_doi and isinstance(data, dict) and "data" in data:
        records = [data["data"]]
    elif isinstance(data, dict):
        records = data.get("data") or []
    out: list[DatasetCandidate] = []
    for rec in records:
        attrs = rec.get("attributes") or {}
        doi = attrs.get("doi")
        if doi:
            titles = attrs.get("titles") or [{}]
            out.append(DatasetCandidate(intent, f"https://doi.org/{doi}", titles[0].get("title", ""), "datacite"))
    return out
