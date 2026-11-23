"""Capture the recorded Hugging Face fixtures used by the spec 027 tests.

Writes six files under ``tests/fixtures/hf_funded/``, each shaped
``{"captured_at", "source_url", "status", "payload"}``:

- ``router_models.json``: keyless GET of the router catalog (free).
- ``lmarena_text_overall.json`` / ``lmarena_text_coding.json``: every page of the
  keyless datasets-server ``/filter`` endpoint. Real row shapes, model names,
  organizations, licenses, vote counts and publish dates are kept; every rating
  field is replaced by :func:`synthetic_rating` and ``rank`` is recomputed from
  it, so no real leaderboard rating is committed. Rows are sorted by name.
- ``chat_200.json`` / ``chat_402.json`` / ``chat_403.json``: only with ``--with-chat``
  (one billed call of at most 64 tokens; the 402 is a request with no bill-to header and
  the 403 one naming an unknown resource group, neither billed). Needs ``HF_TOKEN``/Keychain
  (via ``credentials.load_hf_token``) and ``LLMXIVE_HF_BILL_TO``; neither value is
  written anywhere.

Usage: ``python scripts/hf/capture_fixtures.py [--with-chat]``
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "hf_funded"
ROUTER = "https://router.huggingface.co/v1"
FILTER_URL = "https://datasets-server.huggingface.co/filter"
UA = {"User-Agent": "llmxive-fixture-capture/1.0"}
ARENA = {"overall": "lmarena_text_overall.json", "coding": "lmarena_text_coding.json"}
ZERO_BILL_TO = "000000000000000000000000"


def synthetic_rating(category: str, model_name: str) -> tuple[float, float, float, float]:
    """Deterministic stand-in for a leaderboard rating: (rating, lower, upper, variance)."""
    h = int(hashlib.sha256(f"{category}|{model_name}".encode()).hexdigest(), 16)
    rating = 1000 + (h % 5000) / 10
    half = 2 + ((h >> 64) % 100) / 10
    return rating, round(rating - half, 1), round(rating + half, 1), round(half, 1)


def _write(name: str, source_url: str, status: int, payload: dict, **extra: object) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    doc = {"captured_at": dt.date.today().isoformat(), "source_url": source_url, "status": status,
           **extra, "payload": payload}
    (FIXTURES / name).write_text(json.dumps(doc, indent=1) + "\n")


def capture_router(client: httpx.Client) -> dict:
    url = f"{ROUTER}/models"
    r = client.get(url)
    r.raise_for_status()
    _write("router_models.json", url, r.status_code, r.json())
    return r.json()


def _get_with_retry(client: httpx.Client, params: dict, tries: int = 8) -> httpx.Response:
    """The datasets server returns the odd transient 5xx; retry those, fail on anything else."""
    for attempt in range(tries):
        r = client.get(FILTER_URL, params=params)
        if r.status_code < 500 or attempt == tries - 1:
            r.raise_for_status()
            return r
        time.sleep(3 * (attempt + 1))
    raise AssertionError("unreachable")


def capture_arena(client: httpx.Client, category: str) -> None:
    params = {"dataset": "lmarena-ai/leaderboard-dataset", "config": "text", "split": "latest",
              "where": f'"category"=\'{category}\'', "length": 100}
    rows: list[dict] = []
    offset, total, pages, first_url = 0, None, 0, ""
    while total is None or offset < total:
        r = _get_with_retry(client, {**params, "offset": offset})
        body = r.json()
        if offset == 0:
            first_url = str(r.url)
        total = body["num_rows_total"]
        page = [x["row"] for x in body["rows"]]
        if not page:
            raise RuntimeError(f"empty page at offset {offset} of {total}")
        rows.extend(page)
        pages += 1
        offset += 100
    for row in rows:
        row["rating"], row["rating_lower"], row["rating_upper"], row["variance"] = synthetic_rating(
            category, row["model_name"])
    ratings = [r["rating"] for r in rows]
    for row in rows:
        row["rank"] = float(1 + sum(1 for x in ratings if x > row["rating"]))
    rows.sort(key=lambda r: r["model_name"])
    _write(ARENA[category], first_url, 200,
           {"num_rows_total": total, "pages": pages, "rows": rows}, ratings_synthetic=True)


def _cheapest_live_model(catalog: dict) -> str:
    best: tuple[float, str] | None = None
    for m in catalog["data"]:
        for p in m.get("providers", []):
            pr = p.get("pricing")
            if p.get("status") == "live" and pr and not p.get("is_free"):
                cost = pr["input"] + pr["output"]
                if best is None or cost < best[0]:
                    best = (cost, f"{m['id']}:{p['provider']}")
    if best is None:
        raise RuntimeError("no live priced provider in the catalog")
    return best[1]


def capture_chat(client: httpx.Client, catalog: dict) -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from llmxive.credentials import load_hf_token

    token, bill_to = load_hf_token(), os.environ.get("LLMXIVE_HF_BILL_TO")
    if not token or not bill_to:
        raise SystemExit("--with-chat needs the HF token and LLMXIVE_HF_BILL_TO")
    body = {"model": _cheapest_live_model(catalog), "max_tokens": 64,
            "messages": [{"role": "user", "content": "Reply with the single word: ok"}]}
    url = f"{ROUTER}/chat/completions"
    # Observed live 2026-11-23: no bill-to header -> 402 (billed to the personal
    # account, which has no credits); an unknown group id -> 403.
    for bt, name in ((bill_to, "chat_200.json"), (None, "chat_402.json"), (ZERO_BILL_TO, "chat_403.json")):
        headers = {"Authorization": f"Bearer {token}"}
        if bt is not None:
            headers["X-HF-Bill-To"] = bt
        r = client.post(url, json=body, headers=headers)
        payload = r.json()
        payload.pop("id", None)
        payload.pop("system_fingerprint", None)
        _write(name, url, r.status_code, payload, provenance="recorded")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-chat", action="store_true")
    args = ap.parse_args()
    with httpx.Client(headers=UA, timeout=60) as client:
        catalog = capture_router(client)
        for cat in ARENA:
            capture_arena(client, cat)
        if args.with_chat:
            capture_chat(client, catalog)


if __name__ == "__main__":
    main()
