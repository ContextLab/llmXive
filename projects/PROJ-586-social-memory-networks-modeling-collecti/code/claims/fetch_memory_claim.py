from __future__ import annotations
import argparse
import json
from pathlib import Path
import requests

# Mapping from internal claim identifiers to Wikidata entity IDs.
CLAIM_MAP = {
    "c_9aceca76": "Q26876",
}


def fetch_claim(claim_id: str) -> dict:
    """
    Retrieve the full Wikidata JSON representation for a known claim.

    Parameters
    ----------
    claim_id: str
        Internal claim identifier (e.g., "c_9aceca76").

    Returns
    -------
    dict
        Parsed JSON response from Wikidata.

    Raises
    ------
    ValueError
        If the claim_id is not recognised.
    requests.HTTPError
        If the HTTP request fails.
    """
    if claim_id not in CLAIM_MAP:
        raise ValueError(f"Unknown claim identifier: {claim_id}")

    wikidata_entity = CLAIM_MAP[claim_id]
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{wikidata_entity}.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def main() -> None:
    """
    CLI entry point: fetch a claim and write it to ``data/claims/<claim_id>.json``.
    """
    parser = argparse.ArgumentParser(
        description="Fetch a claim from Wikidata and store the JSON locally."
    )
    parser.add_argument(
        "claim_id",
        nargs="?",
        default="c_9aceca76",
        help="Internal claim identifier (default: c_9aceca76)",
    )
    args = parser.parse_args()

    try:
        claim_data = fetch_claim(args.claim_id)
    except Exception as e:
        print(f"Error fetching claim {args.claim_id}: {e}")
        raise

    out_dir = Path("data/claims")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.claim_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(claim_data, f, indent=2)

    print(f"Claim {args.claim_id} saved to {out_path}")


if __name__ == "__main__":
    main()
