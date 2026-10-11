"""
NCBI Metadata Fetcher for Honeybee CCD Study (T003).

Fetches metadata ONLY from NCBI BioProject PRJNA639195 (CCD) and
PRJNA566029 (Healthy) via the NCBI EUtils REST API (replacing the
unavailable Entrez Direct command-line tools). Does NOT download
FASTQ files.

Implements FR-001 (SSL-validated download, hard stop on certificate
failure) and provides the sample count required by FR-012.

Outputs:
  - data/processed/ncbi_metadata.json
  - data/processed/ncbi_fetch_log.json
  - data/processed/ncbi_metadata_checksum.txt
"""
import sys
import json
import time
import hashlib
import argparse
import csv
import io
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import requests

try:
    from llmxive_toolkit import paths
    OUTPUT_DIR = paths.data("processed")
except Exception:
    OUTPUT_DIR = Path("data/processed")

# Constants
CCD_PROJECT = "PRJNA639195"
HEALTHY_PROJECT = "PRJNA566029"
OUTPUT_FILE = OUTPUT_DIR / "ncbi_metadata.json"
FETCH_LOG = OUTPUT_DIR / "ncbi_fetch_log.json"
CHECKSUM_FILE = OUTPUT_DIR / "ncbi_metadata_checksum.txt"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ERR_SAMPLE_SIZE_INSUFFICIENT = "ERR_SAMPLE_SIZE_INSUFFICIENT"
SSL_VERIFY_FAILED = "SSL Verification Failed"
REQUEST_TIMEOUT = 60
RETRIES = 4

_session = requests.Session()
_session.headers.update({
    "User-Agent": "llmXive-PROJ207-metadata-fetcher/1.0"
})


def _eutils_get(endpoint: str, params: Dict[str, str]) -> requests.Response:
    """GET an EUtils endpoint (e.g. 'esearch.fcgi') with retries,
    rate limiting and SSL verification."""
    url = f"{EUTILS}/{endpoint}"
    last_exc: Optional[Exception] = None
    for attempt in range(RETRIES):
        try:
            resp = _session.get(url, params=params,
                                timeout=REQUEST_TIMEOUT, verify=True)
            if resp.status_code in (429, 500, 502, 503):
                last_exc = RuntimeError(
                    f"EUtils HTTP {resp.status_code} for {url}")
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            time.sleep(0.4)  # NCBI rate limit: max 3 req/s
            return resp
        except requests.exceptions.SSLError as e:
            # Certificate failure: hard stop, never proceed unverified.
            print(f"{SSL_VERIFY_FAILED}: {e}", file=sys.stderr)
            sys.exit(1)
        except requests.RequestException as e:
            last_exc = e
            time.sleep(2 ** attempt)
    raise RuntimeError(
        f"EUtils request failed after {RETRIES} attempts: {last_exc}")


def check_ssl_verification() -> bool:
    """
    Validates SSL certificates using a verified CA bundle by connecting
    to the NCBI EUtils endpoint with certificate verification enabled.
    Returns True if verification passes, False otherwise.
    """
    try:
        resp = _session.get(f"{EUTILS}/einfo.fcgi",
                            params={"db": "sra"},
                            timeout=REQUEST_TIMEOUT, verify=True)
        return resp.status_code == 200
    except requests.exceptions.SSLError as e:
        print(f"{SSL_VERIFY_FAILED}: {e}", file=sys.stderr)
        return False
    except requests.RequestException as e:
        print(f"SSL/connection check failed: {e}", file=sys.stderr)
        return False


def _esearch_sra(project_id: str) -> Tuple[int, str, str]:
    """Run esearch on db=sra for a BioProject; return (count, webenv, query_key)."""
    resp = _eutils_get("esearch.fcgi", {
        "db": "sra",
        "term": f"{project_id}[BioProject]",
        "usehistory": "y",
        "retmax": "0",
    })
    root = ET.fromstring(resp.text)
    count = int(root.findtext("Count") or 0)
    webenv = root.findtext("WebEnv") or ""
    query_key = root.findtext("QueryKey") or ""
    if count == 0 or not webenv:
        raise RuntimeError(f"No SRA entries found for {project_id}")
    return count, webenv, query_key


def _efetch_runinfo(webenv: str, query_key: str) -> List[Dict[str, str]]:
    """Fetch the SRA runinfo CSV for an esearch result set."""
    resp = _eutils_get("efetch.fcgi", {
        "db": "sra",
        "rettype": "runinfo",
        "retmode": "csv",
        "query_key": query_key,
        "WebEnv": webenv,
    })
    reader = csv.DictReader(io.StringIO(resp.text))
    rows = [r for r in reader if r.get("Run")]
    if not rows:
        raise RuntimeError("runinfo CSV contained no runs")
    return rows


def _find_attribute_pairs(obj: Any) -> List[Tuple[str, str]]:
    """Recursively locate (name, value) attribute pairs in BioSample JSON."""
    pairs: List[Tuple[str, str]] = []
    if isinstance(obj, dict):
        name, value = obj.get("name"), obj.get("value")
        if isinstance(name, str) and isinstance(value, str):
            pairs.append((name, value))
        for v in obj.values():
            pairs.extend(_find_attribute_pairs(v))
    elif isinstance(obj, list):
        for item in obj:
            pairs.extend(_find_attribute_pairs(item))
    return pairs


def _fetch_biosample_attributes(accessions: List[str]) -> Dict[str, List[Tuple[str, str]]]:
    """Fetch BioSample summaries (batched) and return attribute pairs per accession."""
    out: Dict[str, List[Tuple[str, str]]] = {}
    batch_size = 150
    for i in range(0, len(accessions), batch_size):
        batch = accessions[i:i + batch_size]
        try:
            resp = _eutils_get("esummary.fcgi", {
                "db": "biosample",
                "id": ",".join(batch),
                "retmode": "json",
            })
            data = resp.json().get("result", {})
        except (RuntimeError, ValueError) as e:
            print(f"Warning: BioSample summary fetch failed for batch: {e}",
                  file=sys.stderr)
            continue
        for acc in batch:
            entry = data.get(acc)
            if isinstance(entry, dict):
                out[acc] = _find_attribute_pairs(entry)
    return out


def _extract_varroa(pairs: List[Tuple[str, str]]) -> Optional[Any]:
    for name, value in pairs:
        if "varroa" in name.lower():
            try:
                return float(value)
            except (TypeError, ValueError):
                return value
    return None


def _extract_region(pairs: List[Tuple[str, str]]) -> Optional[str]:
    for name, value in pairs:
        low = name.lower()
        if "geo" in low or "location" in low or "region" in low:
            if value and value.strip():
                return value.strip()
    return None


def _extract_year(pairs: List[Tuple[str, str]]) -> Optional[int]:
    for name, value in pairs:
        if "date" in name.lower() or "year" in name.lower():
            m = re.search(r"(19|20)\d{2}", str(value))
            if m:
                return int(m.group(0))
    return None


def fetch_project_metadata(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a specific BioProject via the NCBI EUtils REST API.
    Returns a dict with project_id, accession_count and per-sample records,
    or None on failure.
    """
    try:
        count, webenv, query_key = _esearch_sra(project_id)
        print(f"  {project_id}: {count} SRA entries found", flush=True)
        rows = _efetch_runinfo(webenv, query_key)
    except RuntimeError as e:
        print(f"Error fetching metadata for {project_id}: {e}", file=sys.stderr)
        return None

    # Deduplicate runs by BioSample (fall back to Run accession).
    samples: Dict[str, Dict[str, str]] = {}
    for row in rows:
        bio_sample = (row.get("BioSample") or "").strip()
        key = bio_sample if bio_sample else row["Run"]
        if key not in samples:
            samples[key] = row

    # Enrich with BioSample attributes (geographic region, collection
    # date, Varroa load where the submitters recorded it).
    bio_accessions = [k for k in samples if k.startswith("SAM")]
    attr_map = _fetch_biosample_attributes(bio_accessions)

    records: List[Dict[str, Any]] = []
    for key, row in samples.items():
        pairs = attr_map.get(key, [])
        records.append({
            "sample_accession": key,
            "run_accession": row.get("Run", ""),
            "bio_project": row.get("BioProject", project_id),
            "library_strategy": row.get("LibraryStrategy", "WGS"),
            "instrument_platform": row.get("Platform", "Unknown"),
            "varroa_load": _extract_varroa(pairs),
            "geographic_region": _extract_region(pairs),
            "sampling_year": _extract_year(pairs),
        })

    return {
        "project_id": project_id,
        "accession_count": count,
        "records": records,
    }


def extract_sample_info(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract sample records with the CCD status derived from the source
    BioProject (PRJNA639195 = CCD cases, PRJNA566029 = healthy controls),
    per the study design.
    """
    ccd_status = "CCD" if metadata["project_id"] == CCD_PROJECT else "Healthy"
    samples = []
    for rec in metadata.get("records", []):
        samples.append({
            "sample_accession": rec["sample_accession"],
            "run_accession": rec.get("run_accession", ""),
            "ccd_status": ccd_status,
            "varroa_load": rec.get("varroa_load"),
            "geographic_region": rec.get("geographic_region") or "Unknown",
            "sampling_year": rec.get("sampling_year"),
            "library_strategy": rec.get("library_strategy", "WGS"),
            "instrument_platform": rec.get("instrument_platform", "Unknown"),
        })
    return samples


def validate_ccd_criteria(samples: List[Dict[str, Any]]) -> Dict[str, int]:
    """Validate samples against CCD criteria (FR-011) mapping."""
    ccd_count = sum(1 for s in samples if s.get("ccd_status") == "CCD")
    healthy_count = sum(1 for s in samples if s.get("ccd_status") == "Healthy")
    return {
        "ccd": ccd_count,
        "healthy": healthy_count,
        "ambiguous": len(samples) - ccd_count - healthy_count,
        "total": len(samples),
    }


def calculate_varroa_coverage(samples: List[Dict[str, Any]]) -> float:
    """Percentage of samples with Varroa data."""
    if not samples:
        return 0.0
    with_varroa = sum(
        1 for s in samples
        if s.get("varroa_load") not in (None, "", "Unknown")
    )
    return (with_varroa / len(samples)) * 100


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def main():
    """Main entry point for metadata fetch."""
    parser = argparse.ArgumentParser(
        description="Fetch metadata from NCBI BioProjects for CCD study"
    )
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE))
    parser.add_argument("--log", type=str, default=str(FETCH_LOG))
    parser.add_argument("--checksum", type=str, default=str(CHECKSUM_FILE))
    args = parser.parse_args()

    output_path = Path(args.output)
    log_path = Path(args.log)
    checksum_path = Path(args.checksum)
    for p in (output_path, log_path, checksum_path):
        p.parent.mkdir(parents=True, exist_ok=True)

    # SSL Hard-Stop (FR-001)
    if not check_ssl_verification():
        print(f"{SSL_VERIFY_FAILED}: Could not verify SSL certificates.",
              file=sys.stderr)
        sys.exit(1)

    print(f"Fetching metadata for {CCD_PROJECT} and {HEALTHY_PROJECT}...")
    ccd_meta = fetch_project_metadata(CCD_PROJECT)
    healthy_meta = fetch_project_metadata(HEALTHY_PROJECT)

    if not ccd_meta and not healthy_meta:
        print("Failed to fetch metadata from both projects. Exiting.",
              file=sys.stderr)
        sys.exit(1)

    all_samples: List[Dict[str, Any]] = []
    if ccd_meta:
        all_samples.extend(extract_sample_info(ccd_meta))
    if healthy_meta:
        all_samples.extend(extract_sample_info(healthy_meta))

    if not all_samples:
        print("No samples found in metadata. Exiting.", file=sys.stderr)
        sys.exit(1)

    validation = validate_ccd_criteria(all_samples)
    varroa_coverage = calculate_varroa_coverage(all_samples)
    n_samples = len(all_samples)

    fetch_log = {
        "ccd_project": CCD_PROJECT,
        "healthy_project": HEALTHY_PROJECT,
        "ccd_entries_found": ccd_meta["accession_count"] if ccd_meta else 0,
        "healthy_entries_found": healthy_meta["accession_count"] if healthy_meta else 0,
        "total_samples": n_samples,
        "validation": validation,
        "varroa_coverage_percent": varroa_coverage,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(log_path, "w") as f:
        json.dump(fetch_log, f, indent=2)

    print(f"Fetch complete. Found {n_samples} total samples.")
    print(f"CCD: {validation['ccd']}, Healthy: {validation['healthy']}, "
          f"Ambiguous: {validation['ambiguous']}")
    print(f"Varroa coverage: {varroa_coverage:.1f}%")

    # Sample Count Check (FR-012)
    if n_samples < 80:
        print(f"{ERR_SAMPLE_SIZE_INSUFFICIENT}: Only {n_samples} samples found. "
              f"Minimum required: 80.", file=sys.stderr)
        sys.exit(1)

    output_data = {
        "ccd_project_id": CCD_PROJECT,
        "healthy_project_id": HEALTHY_PROJECT,
        "sample_count": n_samples,
        "ccd_count": validation["ccd"],
        "healthy_count": validation["healthy"],
        "ambiguous_count": validation["ambiguous"],
        "varroa_coverage_percent": varroa_coverage,
        "samples": all_samples,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"Metadata written to {output_path}")
    print(f"Log written to {log_path}")

    # Compute and write SHA-256 checksum (sha256sum-compatible format).
    checksum = calculate_checksum(output_path)
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {output_path.name}\n")
    print(f"SHA-256 checksum written to {checksum_path}")

    # Verify checksum round-trip.
    stored = checksum_path.read_text().split()[0]
    if stored != calculate_checksum(output_path):
        print("Error: checksum verification failed after write.",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
