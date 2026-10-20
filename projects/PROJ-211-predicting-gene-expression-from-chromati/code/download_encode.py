import os
import sys
import time
import logging
import json
import csv
import hashlib
import gzip
from pathlib import Path
from typing import List, Dict, Any
import requests

# ----------------------------------------------------------------------
# Logging configuration – ensure the logs directory exists before creating the handler
# ----------------------------------------------------------------------
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "download_encode.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
DEFAULT_CELL_LINES = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]
RAW_DIR = Path("data") / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

ENCODE_API = "https://www.encodeproject.org"
ENCODE_SEARCH = ENCODE_API + "/search/"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def setup_directories() -> None:
    """Ensure required directories exist."""
    dirs = [
        RAW_DIR,
        Path("data/processed"),
        Path("data/models"),
        LOGS_DIR,
        Path("tests"),
        Path("docs"),
        Path("contracts"),
        Path("state")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories ensured: {[str(d) for d in dirs]}")

def get_session_with_retry(max_retries: int = 3, backoff_factor: float = 2.0) -> requests.Session:
    """Create a session with retry logic for transient network failures."""
    session = requests.Session()
    retry_adapter = requests.adapters.HTTPAdapter(
        max_retries=requests.adapters.Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
    )
    session.mount("https://", retry_adapter)
    session.mount("http://", retry_adapter)
    session.headers.update({"User-Agent": "llmxive-download-script"})
    return session

def _query_encode_file(
    session: requests.Session,
    cell_line: str,
    assay: str,
    output_type: str,
    file_format: str = None
) -> str:
    """
    Query ENCODE for a single file matching the criteria.
    Returns the full URL to the file or raises if not found.
    """
    params = {
        "type": "File",
        "assay_title": assay,
        "biosample_ontology.term_name": cell_line,
        "output_type": output_type,
        "status": "released",
        "limit": "1",
        "field": "href",
    }
    if file_format:
        params["format"] = file_format
    logger.info(f"Querying ENCODE for {cell_line} {assay} {output_type} ({file_format})")
    resp = session.get(ENCODE_SEARCH, params=params, headers={"Accept": "application/json"})
    resp.raise_for_status()
    data = resp.json()
    if not data.get("@graph"):
        raise RuntimeError(f"No ENCODE file found for {cell_line} ({assay}, {output_type})")
    href = data["@graph"][0]["href"]
    full_url = ENCODE_API + href
    logger.info(f"Found ENCODE file: {full_url}")
    return full_url

def fetch_encode_metadata(cell_lines: List[str], session: requests.Session) -> List[Dict[str, Any]]:
    """
    Fetch real ENCODE metadata for each requested cell line.
    Returns a list of dicts with keys:
    - cell_line
    - rna: {"download_uri": ...}
    - dnase: {"download_uri": ...}
    """
    results = []
    for cl in cell_lines:
        try:
            rna_uri = _query_encode_file(
                session,
                cell_line=cl,
                assay="RNA-seq",
                output_type="gene quantifications",
                file_format="tsv"
            )
            dnase_uri = _query_encode_file(
                session,
                cell_line=cl,
                assay="DNase-seq",
                output_type="peaks",
                file_format="bed narrowPeak"
            )
            results.append({
                "cell_line": cl,
                "rna": {"download_uri": rna_uri},
                "dnase": {"download_uri": dnase_uri}
            })
        except Exception as e:
            logger.error(f"Failed to retrieve metadata for {cl}: {e}")
            raise
    return results

def download_file(uri: str, output_path: Path, session: requests.Session) -> bool:
    """
    Download a file from a URI to a local path using streaming.
    Returns True on success; raises on HTTP error or empty file.
    """
    logger.info(f"Downloading {uri} to {output_path}")
    try:
        with session.get(uri, stream=True) as r:
            r.raise_for_status()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        # Verify non‑empty
        if output_path.stat().st_size == 0:
            raise RuntimeError(f"Downloaded file is empty: {output_path}")
        logger.info(f"Successfully downloaded {output_path} ({output_path.stat().st_size} bytes)")
        return True
    except Exception as e:
        logger.error(f"Failed to download {uri}: {e}")
        raise

def process_rna_data(input_path: Path, output_path: Path) -> None:
    """
    Convert ENCODE RNA‑seq quantification TSV into the final counts CSV.
    Expected ENCODE columns include at least: gene_id, gene_name, TPM (or tpm).
    Output CSV columns: gene_id, gene_name, cell_line, count
    """
    logger.info(f"Processing RNA data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input RNA file not found: {input_path}")

    cell_line = output_path.stem.split("_")[-1]  # e.g. encode_counts_GM12878.csv -> GM12878
    with input_path.open("r") as f_in, output_path.open("w", newline="") as f_out:
        reader = csv.DictReader(f_in, delimiter="\t")
        writer = csv.writer(f_out)
        writer.writerow(["gene_id", "gene_name", "cell_line", "count"])
        for row in reader:
            # Detect TPM column (case‑insensitive)
            tpm_key = next((k for k in row.keys() if k.lower() == "tpm"), None)
            if tpm_key is None:
                raise RuntimeError(f"TPM column not found in RNA file {input_path}")
            try:
                count = int(float(row[tpm_key]) * 10)  # simple scaling to integer counts
            except ValueError:
                count = 0
            writer.writerow([row["gene_id"], row["gene_name"], cell_line, count])
    logger.info(f"Wrote processed RNA counts to {output_path}")

def process_accessibility_data(input_path: Path, output_path: Path) -> None:
    """
    Convert ENCODE narrowPeak BED into the final BED used downstream.
    The script copies the file, ensuring it exists.
    """
    logger.info(f"Processing accessibility data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input accessibility file not found: {input_path}")

    # Direct copy – ensures the target exists
    with input_path.open("rb") as src, output_path.open("wb") as dst:
        while True:
            chunk = src.read(8192)
            if not chunk:
                break
            dst.write(chunk)
    logger.info(f"Wrote processed accessibility BED to {output_path}")

def write_gene_coords_bed(output_path: Path) -> None:
    """
    Download GENCODE hg38 annotation GTF, extract TSS positions,
    and write a minimal BED file (chrom, start, end, gene_id, score, strand).
    """
    logger.info(f"Downloading GENCODE annotation for TSS BED")
    gencode_url = (
        "https://ftp.ebi.ac.uk/pub/databases/gencode/GTF/human/"
        "release_44/gencode.v44.annotation.gtf.gz"
    )
    gtf_path = output_path.parent / "gencode.v44.annotation.gtf.gz"
    session = get_session_with_retry()
    download_file(gencode_url, gtf_path, session)

    logger.info(f"Parsing GTF and writing TSS BED to {output_path}")
    with gzip.open(gtf_path, "rt") as gtf_f, output_path.open("w") as bed_f:
        for line in gtf_f:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            if len(fields) != 9:
                continue
            chrom, source, feature_type, start, end, score, strand, phase, attributes = fields
            if feature_type != "gene":
                continue
            # Extract gene_id attribute
            attr_dict = {}
            for attr in attributes.split(";"):
                attr = attr.strip()
                if not attr:
                    continue
                key, value = attr.split(" ", 1)
                attr_dict[key] = value.strip('"')
            gene_id = attr_dict.get("gene_id")
            if not gene_id:
                continue
            start_int = int(start) - 1  # GTF is 1‑based inclusive; BED is 0‑based half‑open
            end_int = int(end)
            # Determine TSS position
            if strand == "+":
                tss_start = start_int
                tss_end = start_int + 1
            else:
                tss_start = end_int - 1
                tss_end = end_int
            bed_f.write(f"{chrom}\t{tss_start}\t{tss_end}\t{gene_id}\t0\t{strand}\n")
    logger.info(f"Gene coordinates BED written to {output_path}")

    # Clean up downloaded GTF to avoid clutter
    try:
        gtf_path.unlink()
    except Exception:
        pass

def checksum_file(path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def log_checksums_csv(files: List[Path], log_path: Path = RAW_DIR / "checksums.csv") -> None:
    """
    Record SHA‑256 checksums of the listed files into a CSV file
    with columns: filename,sha256
    """
    import csv
    with log_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "sha256"])
        for fp in files:
            if fp.exists():
                writer.writerow([str(fp), checksum_file(fp)])
            else:
                logger.warning(f"File not found for checksum logging: {fp}")
    logger.info(f"Checksums written to {log_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Download ENCODE RNA‑seq and DNase/ATAC‑seq files for the
    requested cell lines, process them into the pipeline‑ready formats,
    and record SHA‑256 checksums.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Download ENCODE data for specified cell lines.")
    parser.add_argument(
        "--cell-lines",
        type=str,
        default=",".join(DEFAULT_CELL_LINES),
        help="Comma‑separated list of cell lines to download (e.g. GM12878,K562,HMEC)"
    )
    args = parser.parse_args()
    cell_lines = [cl.strip() for cl in args.cell_lines.split(",") if cl.strip()]

    setup_directories()
    ci_mode = os.environ.get("CI_MODE", "0") == "1"
    session = get_session_with_retry()

    metadata = fetch_encode_metadata(cell_lines, session)
    if not metadata:
        logger.error("No metadata could be retrieved for the requested cell lines.")
        if ci_mode:
            with (RAW_DIR / ".download_failed.log").open("w") as f:
                json.dump({"status": "failed", "reason": "No metadata in CI mode"}, f)
            logger.info("CI mode: recorded failure and exiting.")
            sys.exit(0)
        else:
            raise SystemExit("Failed to retrieve ENCODE metadata and CI_MODE=0 – aborting pipeline.")

    generated_files: List[Path] = []

    for entry in metadata:
        cl = entry["cell_line"]
        # ----- RNA‑seq -----
        rna_uri = entry["rna"]["download_uri"]
        rna_tmp = RAW_DIR / f"{cl}_rna.tmp"
        rna_out = RAW_DIR / f"encode_counts_{cl}.csv"

        download_file(rna_uri, rna_tmp, session)
        process_rna_data(rna_tmp, rna_out)
        generated_files.append(rna_out)
        rna_tmp.unlink(missing_ok=True)

        # ----- DNase/ATAC -----
        dnase_uri = entry["dnase"]["download_uri"]
        dnase_tmp = RAW_DIR / f"{cl}_dnase.tmp"
        dnase_out = RAW_DIR / f"encode_peaks_{cl}.bed"

        download_file(dnase_uri, dnase_tmp, session)
        process_accessibility_data(dnase_tmp, dnase_out)
        generated_files.append(dnase_out)
        dnase_tmp.unlink(missing_ok=True)

    # ----- Gene coordinates (TSS) -----
    gene_coords_path = RAW_DIR / "gene_coords.bed"
    write_gene_coords_bed(gene_coords_path)
    generated_files.append(gene_coords_path)

    # Record checksums
    log_checksums_csv(generated_files)

    logger.info("All downloads and processing steps completed successfully.")

if __name__ == "__main__":
    main()
