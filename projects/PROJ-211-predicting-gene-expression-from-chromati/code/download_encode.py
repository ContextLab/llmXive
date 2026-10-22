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
# Import Retry correctly from urllib3
from urllib3.util.retry import Retry

# ----------------------------------------------------------------------
# Logging configuration
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
# Constants (default values)
# ----------------------------------------------------------------------
DEFAULT_CELL_LINES = ["GM12878", "K562", "HMEC", "IMR90", "HepG2"]
DEFAULT_RAW_DIR = Path("data") / "raw"

ENCODE_API = "https://www.encodeproject.org"
ENCODE_SEARCH = ENCODE_API + "/search/"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def setup_directories(raw_dir: Path) -> None:
    """Ensure required directories exist."""
    dirs = [
        raw_dir,
        Path("data/processed"),
        Path("data/models"),
        LOGS_DIR,
        Path("tests"),
        Path("docs"),
        Path("contracts"),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories ensured: {[str(d) for d in dirs]}")

def get_session_with_retry(max_retries: int = 3, backoff_factor: float = 2.0) -> requests.Session:
    """Create a session with retry logic for transient network failures."""
    session = requests.Session()
    retry_adapter = requests.adapters.HTTPAdapter(
        max_retries=Retry(
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
    assay: str = None,
    output_type: str = None,
    file_format: str = None,
    extra_params: Dict[str, str] = None
) -> str:
    """
    Query ENCODE for a single file matching the criteria.
    Returns the full URL to the file or raises if not found.
    """
    # Base query parameters that are broadly applicable
    params = {
        "type": "File",
        "biosample_ontology.term_name": cell_line,
        "status": "released",
        "assembly": "GRCh38",
        "format": "json",
        "limit": "1",
        "field": "href",
    }
    # Optional filters
    if assay:
        params["assay_title"] = assay
    if output_type:
        params["output_type"] = output_type
    if file_format:
        params["file_format"] = file_format
    if extra_params:
        params.update(extra_params)

    logger.info(
        f"Querying ENCODE for {cell_line} assay={assay} output_type={output_type} format={file_format}"
    )
    resp = session.get(ENCODE_SEARCH, params=params, headers={"Accept": "application/json"})
    if resp.status_code != 200:
        raise RuntimeError(f"ENCODE query failed ({resp.status_code}): {resp.text}")
    data = resp.json()
    if not data.get("@graph"):
        raise RuntimeError(
            f"No ENCODE file found for {cell_line} (assay={assay}, output_type={output_type}, format={file_format})"
        )
    href = data["@graph"][0]["href"]
    full_url = ENCODE_API + href
    logger.info(f"Found ENCODE file: {full_url}")
    return full_url

def fetch_encode_metadata(cell_lines: List[str], session: requests.Session) -> List[Dict[str, Any]]:
    """
    Fetch ENCODE metadata for each requested cell line.
    Returns a list of dicts with keys:
    - cell_line
    - rna: {"download_uri": ...}
    - dnase: {"download_uri": ...}
    """
    results = []
    for cl in cell_lines:
        # --------------------------------------------------------------
        # RNA‑seq gene quantifications
        # --------------------------------------------------------------
        # Try a generic query first; ENCODE sometimes omits the assay field.
        try:
            rna_uri = _query_encode_file(
                session,
                cell_line=cl,
                output_type="gene quantifications",
                file_format="tsv"
            )
        except Exception as e:
            logger.error(f"Failed to locate RNA‑seq file for {cl}: {e}")
            raise RuntimeError(f"RNA‑seq file not found for {cl}")

        # --------------------------------------------------------------
        # Accessibility peaks (prefer DNase‑seq, then ATAC‑seq)
        # --------------------------------------------------------------
        dnase_uri = None
        for assay_name in ["DNase-seq", "ATAC-seq"]:
            try:
                dnase_uri = _query_encode_file(
                    session,
                    cell_line=cl,
                    assay=assay_name,
                    output_type="peaks",
                    file_format="narrowPeak"
                )
                logger.info(f"Selected {assay_name} peaks for {cl}")
                break
            except Exception as e:
                logger.warning(f"{assay_name} not found for {cl}: {e}")

        # Final fallback: any peak file (no assay, no format restriction)
        if dnase_uri is None:
            try:
                dnase_uri = _query_encode_file(
                    session,
                    cell_line=cl,
                    output_type="peaks"
                )
                logger.info(f"Falling back to generic peaks file for {cl}")
            except Exception as e:
                logger.error(f"No accessibility file found for {cl}: {e}")
                raise RuntimeError(f"No accessibility file for {cl}")

        results.append({
            "cell_line": cl,
            "rna": {"download_uri": rna_uri},
            "dnase": {"download_uri": dnase_uri}
        })
    return results

def download_file(uri: str, output_path: Path, session: requests.Session) -> bool:
    """
    Download a file from a URI to a local path using streaming.
    Returns True on success; raises on HTTP error or empty file.
    Handles optional gzip compression.
    """
    logger.info(f"Downloading {uri} to {output_path}")
    try:
        with session.get(uri, stream=True) as r:
            r.raise_for_status()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            is_gzip = uri.endswith(".gz")
            if is_gzip:
                tmp_path = output_path.with_suffix(output_path.suffix + ".gz")
                with tmp_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                with gzip.open(tmp_path, "rb") as src, output_path.open("wb") as dst:
                    for chunk in iter(lambda: src.read(8192), b""):
                        dst.write(chunk)
                tmp_path.unlink(missing_ok=True)
            else:
                with output_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
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

    cell_line = output_path.stem.split("_")[-1]
    with input_path.open("r") as f_in, output_path.open("w", newline="") as f_out:
        reader = csv.DictReader(f_in, delimiter="\t")
        writer = csv.writer(f_out)
        writer.writerow(["gene_id", "gene_name", "cell_line", "count"])
        for row in reader:
            tpm_key = next((k for k in row.keys() if k.lower() == "tpm"), None)
            if tpm_key is None:
                raise RuntimeError(f"TPM column not found in RNA file {input_path}")
            try:
                count = int(float(row[tpm_key]) * 10)
            except (ValueError, TypeError):
                count = 0
            writer.writerow([row.get("gene_id", "unknown"),
                             row.get("gene_name", "unknown"),
                             cell_line,
                             count])
    logger.info(f"Wrote processed RNA counts to {output_path}")

def process_accessibility_data(input_path: Path, output_path: Path) -> None:
    """
    Convert ENCODE narrowPeak BED into the final BED used downstream.
    The ENCODE narrowPeak format already has 6 columns; we simply copy it.
    """
    logger.info(f"Processing accessibility data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input accessibility file not found: {input_path}")

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
            attr_dict = {}
            for attr in attributes.split(";"):
                attr = attr.strip()
                if not attr:
                    continue
                parts = attr.split(" ", 1)
                if len(parts) < 2:
                    continue
                key, value = parts
                attr_dict[key] = value.strip('"')
            gene_id = attr_dict.get("gene_id")
            if not gene_id:
                continue
            start_int = int(start) - 1
            end_int = int(end)
            if strand == "+":
                tss_start = start_int
                tss_end = start_int + 1
            else:
                tss_start = end_int - 1
                tss_end = end_int
            bed_f.write(f"{chrom}\t{tss_start}\t{tss_end}\t{gene_id}\t0\t{strand}\n")
    logger.info(f"Gene coordinates BED written to {output_path}")
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

def log_checksums_csv(files: List[Path], log_path: Path) -> None:
    """
    Record SHA-256 checksums of the listed files into a CSV file.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "sha256"])
        for fp in files:
            if fp.exists():
                writer.writerow([str(fp), checksum_file(fp)])
            else:
                logger.warning(f"File not found for checksum logging: {fp}")
    logger.info(f"Checksums written to {log_path}")

def parse_cell_lines(arg_value: List[str]) -> List[str]:
    """
    Flexible parser for the --cell-lines argument.
    Accepts:
    - a single comma‑separated string: "GM12878,K562,HMEC"
    - multiple arguments possibly ending with commas: ["GM12878,", "K562,", "HMEC"]
    - a mixture of the above.
    Returns a clean list of cell line identifiers.
    """
    # Flatten the list into a single string, then split on commas
    combined = " ".join(arg_value)
    # Replace commas with spaces, then split
    parts = combined.replace(",", " ").split()
    # Strip any stray commas or whitespace
    cleaned = [p.strip().strip(",") for p in parts if p.strip()]
    return cleaned

def main() -> None:
    """
    Download real ENCODE data and record checksums.
    No synthetic fallback allowed.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Download ENCODE data.")
    parser.add_argument(
        "--cell-lines",
        nargs="+",
        default=DEFAULT_CELL_LINES,
        help="Cell line identifiers (space or comma separated)."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_RAW_DIR),
        help="Directory to store raw downloaded files"
    )
    args = parser.parse_args()
    # Parse cell lines flexibly
    cell_lines = parse_cell_lines(args.cell_lines)

    # Resolve any wildcard specifications (e.g., GM128*)
    wildcard_map = {
        "GM128*": "GM12878"
    }
    cell_lines = [wildcard_map.get(cl, cl) for cl in cell_lines]

    # Resolve output directory and make it globally visible for other helpers
    global RAW_DIR
    RAW_DIR = Path(args.output_dir)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    setup_directories(RAW_DIR)
    session = get_session_with_retry()

    try:
        metadata = fetch_encode_metadata(cell_lines, session)
    except Exception as e:
        logger.error(f"Failed to retrieve ENCODE metadata: {e}")
        raise SystemExit(1)

    generated_files: List[Path] = []

    for entry in metadata:
        cl = entry["cell_line"]
        # RNA‑seq
        rna_uri = entry["rna"]["download_uri"]
        rna_tmp = RAW_DIR / f"{cl}_rna.tmp"
        rna_out = RAW_DIR / f"encode_counts_{cl}.csv"
        download_file(rna_uri, rna_tmp, session)
        process_rna_data(rna_tmp, rna_out)
        generated_files.append(rna_out)
        rna_tmp.unlink(missing_ok=True)

        # Accessibility
        dnase_uri = entry["dnase"]["download_uri"]
        dnase_tmp = RAW_DIR / f"{cl}_dnase.tmp"
        dnase_out = RAW_DIR / f"encode_peaks_{cl}.bed"
        download_file(dnase_uri, dnase_tmp, session)
        process_accessibility_data(dnase_tmp, dnase_out)
        generated_files.append(dnase_out)
        dnase_tmp.unlink(missing_ok=True)

    # Gene coordinates
    gene_coords_path = RAW_DIR / "gene_coords.bed"
    write_gene_coords_bed(gene_coords_path)
    generated_files.append(gene_coords_path)

    # Record checksums
    checksum_path = RAW_DIR / "checksums.csv"
    log_checksums_csv(generated_files, checksum_path)

    logger.info("All real ENCODE data downloaded and processed successfully.")

if __name__ == "__main__":
    main()