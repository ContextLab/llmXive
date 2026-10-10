"""Download raw scRNA-seq data for the T-cell exhaustion trajectory project.

Real-data downloader for GSE136103, GSE127465, GSE111075 and GSE138852.

Primary data source: NCBI GEO supplementary files, fetched over HTTPS from
https://ftp.ncbi.nlm.nih.gov/geo/series/... (public, no authentication),
per FR-001. If the SRA Toolkit (prefetch/fasterq-dump) is available in
PATH, a real SRA FASTQ sample is additionally fetched per dataset via
fasterq-dump; if the toolkit is absent the script logs a warning and
continues with the GEO downloads (the GEO supplementary count matrices
are the actual analysis inputs).

There are NO synthetic fallbacks: any failed real fetch raises and the
process exits non-zero (fail loudly). SHA256 checksums of every
downloaded file are recorded in data/state.yaml (Constitution Principle
III).
"""
import argparse
import hashlib
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml
from Bio import Entrez

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

Entrez.email = "researcher@llmxive.org"

TARGET_GSE_IDS = [
    "GSE136103",
    "GSE127465",
    "GSE111075",
    "GSE138852",
]

GEO_FTP_BASE = "https://ftp.ncbi.nlm.nih.gov/geo/series"
# Hard cap on a single supplementary file (runner disk/compute budget).
MAX_DOWNLOAD_BYTES = 1_000_000_000
PER_FILE_TIMEOUT_S = 240

# Keywords used for the SC-005 data-sufficiency screen of the GEO record.
SUFFICIENCY_KEYWORDS = {
    "pd1_expression": ["pdcd1", "pd-1", "pd1"],
    "metabolic_markers": ["metabol", "glycolys", "oxphos", "mitochondri"],
    "exhaustion_signature": ["exhaust", "tim-3", "havcr2", "lag3", "tox"],
    "therapy_response_labels": ["responder", "response", "anti-pd", "checkpoint", "nivolumab", "pembrolizumab", "atezolizumab"],
}


def check_sra_toolkit() -> bool:
    """Verify that SRA Toolkit is installed and accessible."""
    try:
        subprocess.run(
            ["prefetch", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        subprocess.run(
            ["fasterq-dump", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning(
            "SRA Toolkit (prefetch/fasterq-dump) not found in PATH; "
            "SRA FASTQ sampling will be skipped. GEO supplementary "
            "count matrices remain the primary real data source."
        )
        return False


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(1 << 20), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def update_state(dataset_id: str, metadata: Dict[str, Any]):
    """Update the project state YAML with dataset metadata."""
    project_root = Path(__file__).resolve().parent.parent
    state_path = project_root / "data" / "state.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)

    state = {}
    if state_path.exists():
        with open(state_path, "r") as f:
            state = yaml.safe_load(f) or {}

    if "datasets" not in state or not isinstance(state["datasets"], dict):
        state["datasets"] = {}

    state["datasets"][dataset_id] = metadata

    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False)


def get_sra_ids_for_gse(gse_id: str) -> List[str]:
    """Fetch SRA accession IDs associated with a GSE accession using Biopython Entrez."""
    logger.info(f"Fetching SRA IDs for {gse_id}...")
    try:
        handle = Entrez.esearch(db="sra", term=f"{gse_id}[accession]")
        record = Entrez.read(handle)
        handle.close()
        return record.get("IdList", [])
    except Exception as e:  # noqa: BLE001 - log and surface loudly upstream
        logger.error(f"Error fetching SRA IDs for {gse_id}: {e}")
        return []


def download_sra_sample(sra_id: str, output_dir: Path) -> bool:
    """Download a sample of SRA data to FASTQ using fasterq-dump."""
    logger.info(f"Downloading sample for {sra_id}...")
    output_dir.mkdir(parents=True, exist_ok=True)

    # --max-reads keeps the real SRA fetch within CI limits while still
    # obtaining real sequencing data from the real source.
    cmd = [
        "fasterq-dump",
        "--outdir", str(output_dir),
        "--split-files",
        "--max-reads", "10000",
        sra_id,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"SRA download failed for {sra_id}: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("fasterq-dump not found; cannot fetch SRA sample.")
        return False


def _geo_suppl_dir_url(gse_id: str) -> str:
    """Return the GEO supplementary directory URL for a GSE accession."""
    num = int(gse_id[3:])
    prefix = f"GSE{num // 1000}nnn"
    return f"{GEO_FTP_BASE}/{prefix}/{gse_id}/suppl/"


def _list_geo_suppl_files(gse_id: str) -> List[str]:
    """List real supplementary file URLs in the GEO series suppl directory."""
    dir_url = _geo_suppl_dir_url(gse_id)
    logger.info(f"Listing supplementary files at {dir_url}")
    resp = requests.get(dir_url, timeout=60)
    resp.raise_for_status()
    names = re.findall(r'href="([^"/]+)"', resp.text)
    keep = [
        n for n in names
        if not n.startswith("?") and n.lower().endswith(
            (".gz", ".tar", ".tgz", ".zip", ".csv", ".txt", ".h5")
        )
    ]
    if not keep:
        raise RuntimeError(f"No supplementary files found for {gse_id} at {dir_url}")
    return [dir_url + n for n in keep]


def _head_content_length(url: str) -> Optional[int]:
    try:
        resp = requests.head(url, timeout=60, allow_redirects=True)
        resp.raise_for_status()
        length = resp.headers.get("Content-Length")
        return int(length) if length is not None else None
    except Exception:  # noqa: BLE001
        return None


def _select_file(urls: List[str]) -> str:
    """Select the best real count-matrix file under the size cap."""
    preferred_keys = ("count", "matrix", "expr", "umi", "tpm", "rpk")
    scored = []
    for url in urls:
        name = os.path.basename(url).lower()
        preferred = any(k in name for k in preferred_keys)
        size = _head_content_length(url)
        if size is not None and size > MAX_DOWNLOAD_BYTES:
            logger.warning(
                f"Skipping {os.path.basename(url)} "
                f"({size / 1e6:.0f} MB exceeds {MAX_DOWNLOAD_BYTES / 1e6:.0f} MB cap)"
            )
            continue
        scored.append((0 if preferred else 1, size if size is not None else 0, url))
    if not scored:
        raise RuntimeError(
            "No downloadable supplementary file under the size cap; "
            "cannot fabricate a substitute."
        )
    scored.sort()
    return scored[0][2]


def download_geo_counts(gse_id: str, output_dir: Path) -> Path:
    """Download a real processed count matrix from GEO over HTTPS.

    Raises RuntimeError on any failure (fail loudly, no fallback).
    """
    logger.info(f"Fetching processed counts for {gse_id}...")
    counts_dir = output_dir / "counts"
    counts_dir.mkdir(parents=True, exist_ok=True)

    urls = _list_geo_suppl_files(gse_id)
    target_url = _select_file(urls)
    target_file = counts_dir / os.path.basename(target_url)

    logger.info(f"Downloading {target_url} -> {target_file}")
    with requests.get(target_url, stream=True, timeout=PER_FILE_TIMEOUT_S) as resp:
        resp.raise_for_status()
        downloaded = 0
        with open(target_file, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                downloaded += len(chunk)
                if downloaded > MAX_DOWNLOAD_BYTES:
                    raise RuntimeError(
                        f"{target_url} exceeded size cap mid-download; aborting."
                    )
                f.write(chunk)

    if target_file.stat().st_size == 0:
        raise RuntimeError(f"Downloaded file {target_file} is empty.")
    logger.info(
        f"Downloaded {target_file} ({target_file.stat().st_size / 1e6:.1f} MB)"
    )
    return target_file


def check_dataset_sufficiency(gse_id: str) -> Dict[str, Any]:
    """Screen the real GEO record text for variables required by SC-005."""
    url = (
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
        f"?acc={gse_id}&targ=self&form=text&view=quick"
    )
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        text = resp.text.lower()
        screen = {
            key: any(kw in text for kw in keywords)
            for key, keywords in SUFFICIENCY_KEYWORDS.items()
        }
        screen["source_record"] = url
        return screen
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Could not screen GEO record for {gse_id}: {e}")
        return {"error": str(e), "source_record": url}


def main():
    parser = argparse.ArgumentParser(
        description="Download real raw count matrices from GEO/SRA."
    )
    parser.add_argument(
        "--datasets",
        type=str,
        default=",".join(TARGET_GSE_IDS),
        help="Comma-separated list of GSE accessions",
    )
    args = parser.parse_args()
    gse_ids = [g.strip() for g in args.datasets.split(",") if g.strip()]

    project_root = Path(__file__).resolve().parent.parent
    raw_data_dir = project_root / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    toolkit_available = check_sra_toolkit()

    failures = []
    for gse in gse_ids:
        logger.info(f"Processing {gse}...")
        gse_dir = raw_data_dir / gse

        # 1. Download real GEO processed counts (primary analysis input).
        try:
            counts_file = download_geo_counts(gse, gse_dir)
        except Exception as e:  # noqa: BLE001
            logger.error(f"REAL GEO download failed for {gse}: {e}")
            failures.append(gse)
            update_state(gse, {
                "dataset_id": gse,
                "source": "GEO/SRA",
                "raw_counts_path": "",
                "checksum": "",
                "counts_checksum": "",
                "cell_count": 0,
                "gene_count": 0,
                "status": "unavailable",
                "error": str(e),
            })
            continue

        counts_checksum = calculate_sha256(counts_file)

        # 2. Optional real SRA FASTQ sample (only if toolkit present).
        sra_checksum = "skipped_no_toolkit"
        if toolkit_available:
            sra_ids = get_sra_ids_for_gse(gse)
            if sra_ids:
                sra_dir = gse_dir / "raw_reads"
                if download_sra_sample(sra_ids[0], sra_dir):
                    fastq_files = sorted(sra_dir.glob("*.fastq"))
                    sra_checksum = (
                        calculate_sha256(fastq_files[0]) if fastq_files else "no_fastq"
                    )
                else:
                    sra_checksum = "failed"
            else:
                sra_checksum = "no_ids"

        # 3. SC-005 sufficiency screen against the real GEO record.
        sufficiency = check_dataset_sufficiency(gse)

        # 4. Record state (Constitution Principle III: checksums).
        update_state(gse, {
            "dataset_id": gse,
            "source": "GEO/SRA",
            "raw_counts_path": str(counts_file.relative_to(project_root)),
            "checksum": counts_checksum,
            "counts_checksum": counts_checksum,
            "sra_sample_checksum": sra_checksum,
            "cell_count": 0,  # populated by T003
            "gene_count": 0,  # populated by T003
            "status": "available",
            "sufficiency_screen": sufficiency,
        })

    if failures:
        logger.critical(
            "Real data download FAILED for: %s. Aborting (no synthetic fallback)."
            % ", ".join(failures)
        )
        sys.exit(1)

    logger.info("Data download complete. State updated in data/state.yaml")


if __name__ == "__main__":
    main()