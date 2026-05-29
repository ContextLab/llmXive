"""Deterministic dataset-source clients (spec: dataset-resolver design).

Each ``search_*`` returns a list of :class:`DatasetCandidate` for a dataset
intent (a name like "QM9" or a DOI). No ranking or verification here — that is
the resolver's job. All network errors are swallowed into an empty list so one
dead source never breaks resolution; the resolver decides what to do with the
union of candidates.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests  # type: ignore[import-untyped]  # no stub package available

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


def _hf_pick_data_file(api: Any, ds_id: str) -> str | None:
    """Deterministically pick the best sample-able data file in an HF dataset.

    Returns the in-repo path (e.g. ``data/train-...parquet``) or ``None`` when
    the dataset exposes no recognizable data file.
    """
    try:
        info = api.dataset_info(ds_id)
    except Exception:
        return None
    raw_files: list[Any] = [
        getattr(s, "rfilename", None)
        for s in (getattr(info, "siblings", None) or [])
    ]
    files: list[str] = [f for f in raw_files if f and not f.startswith(".")]
    candidates: list[str] = [f for f in files if f.lower().endswith(_HF_DATA_EXTS)]
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


def _get_json(url: str, *, params: dict[str, object] | None = None) -> dict[str, Any] | list[Any] | None:
    try:
        r = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=_TIMEOUT)
        if r.status_code != 200:
            return None
        result: dict[str, Any] | list[Any] = r.json()
        return result
    except (requests.RequestException, ValueError, OSError):
        return None


def search_figshare(intent: str, *, limit: int = 5) -> list[DatasetCandidate]:
    data = _get_json("https://api.figshare.com/v2/articles", params={"search_for": intent, "page_size": limit})
    items: list[Any] = data if isinstance(data, list) else []
    out: list[DatasetCandidate] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        url = item.get("url_public_html") or item.get("url")
        if url:
            out.append(DatasetCandidate(intent, str(url), str(item.get("title", "")), "figshare"))
    return out


def search_zenodo(intent: str, *, limit: int = 5) -> list[DatasetCandidate]:
    data = _get_json("https://zenodo.org/api/records", params={"q": intent, "size": limit})
    data_dict: dict[str, Any] = data if isinstance(data, dict) else {}
    hits_outer = data_dict.get("hits")
    hits_inner: dict[str, Any] = hits_outer if isinstance(hits_outer, dict) else {}
    raw_hits = hits_inner.get("hits")
    hits_list: list[Any] = raw_hits if isinstance(raw_hits, list) else []
    out: list[DatasetCandidate] = []
    for h in hits_list:
        if not isinstance(h, dict):
            continue
        links = h.get("links")
        url = (links.get("html") if isinstance(links, dict) else None) or h.get("doi_url")
        if url:
            metadata = h.get("metadata")
            title = metadata.get("title", "") if isinstance(metadata, dict) else ""
            out.append(DatasetCandidate(intent, str(url), str(title), "zenodo"))
    return out


def search_datacite(intent: str, *, limit: int = 5) -> list[DatasetCandidate]:
    # intent may be a DOI (resolve) or a free-text query (search).
    looks_doi = intent.strip().lower().startswith("10.")
    params: dict[str, object] | None = {"query": intent, "page[size]": limit} if not looks_doi else None
    url = f"https://api.datacite.org/dois/{intent}" if looks_doi else "https://api.datacite.org/dois"
    data = _get_json(url, params=params)
    records: list[Any] = []
    if looks_doi and isinstance(data, dict) and "data" in data:
        records = [data["data"]]
    elif isinstance(data, dict):
        raw = data.get("data")
        records = list(raw) if isinstance(raw, list) else []
    out: list[DatasetCandidate] = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        attrs: dict[str, Any] = rec.get("attributes") or {}
        doi = attrs.get("doi")
        if doi:
            titles_raw = attrs.get("titles")
            titles: list[Any] = titles_raw if isinstance(titles_raw, list) else [{}]
            first = titles[0] if titles else {}
            title = first.get("title", "") if isinstance(first, dict) else ""
            out.append(DatasetCandidate(intent, f"https://doi.org/{doi}", str(title), "datacite"))
    return out
