import os
import sys
import json
import logging
import hashlib
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config import Config
from download import calculate_md5, validate_checksum, DownloadError

class DatasetStatus:
    """Enum-like class to represent the status of a dataset."""
    FOUND = "found"
    MISSING = "missing"
    INVALID_FORMAT = "invalid_format"
    CHECKSUM_MISMATCH = "checksum_mismatch"

class DataGapResolver:
    """
    Resolves data gaps by verifying downloaded files contain raw count matrices
    and validating checksums.
    """

    def __init__(self, config: Config):
        self.config = config
        self.raw_data_dir = config.RAW_DATA_DIR
        self.results_dir = config.RESULTS_DIR
        self.accessions = config.DATASET_ACCESSIONS

    def _is_raw_count_matrix(self, file_path: Path) -> Tuple[bool, str]:
        """
        Verifies if a downloaded file contains a raw count matrix.
        
        Strategies:
        1. Check file extension (.txt, .gz, .mtx).
        2. Inspect content:
           - For .mtx (Matrix Market): Look for '%%MatrixMarket' header.
           - For .txt/.tsv: Check for a header row with gene/cell identifiers 
             and numeric data, ensuring no 'cluster' or 'marker' keywords dominate.
           - For .gz: Attempt to read the first few bytes/lines.
        3. Reject files that look like cluster markers (e.g., small files, 
           headers containing 'Cluster', 'Marker', 'GeneSet').
        
        Returns:
            Tuple[bool, str]: (is_valid, reason)
        """
        if not file_path.exists():
            return False, "File does not exist"

        file_size = file_path.stat().st_size
        if file_size == 0:
            return False, "File is empty"

        # Heuristic: Raw count matrices are typically large (>1MB usually, 
        # but depends on dataset size; markers are often tiny <10KB).
        # We set a conservative lower bound of 10KB for a count matrix.
        if file_size < 10240: # 10KB
            logger.warning(f"File {file_path} is very small ({file_size} bytes). "
                           "Likely contains metadata/markers, not a raw count matrix.")
            return False, "File too small to be a raw count matrix"

        try:
            # Determine file type and read appropriate chunk
            content_bytes = b""
            is_gz = str(file_path).endswith('.gz')
            
            if is_gz:
                import gzip
                try:
                    with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                        content_bytes = f.read(2048).encode('utf-8', errors='ignore')
                except Exception as e:
                    return False, f"Failed to read gzipped file: {e}"
            else:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content_bytes = f.read(2048).encode('utf-8', errors='ignore')
                except Exception as e:
                    return False, f"Failed to read file: {e}"

            content_str = content_bytes.decode('utf-8', errors='ignore').lower()

            # Check for Matrix Market format
            if "%%matrixmarket" in content_str:
                logger.info(f"Detected Matrix Market format in {file_path}")
                return True, "Valid Matrix Market header"

            # Check for cluster markers or metadata
            # Common indicators of non-count data
            bad_keywords = ["cluster", "marker", "geneset", "pathway", "ontology"]
            # If the header or first few lines contain these, it's likely not raw counts
            # We check if these words appear in the first 500 characters
            header_snippet = content_str[:500]
            for keyword in bad_keywords:
                if keyword in header_snippet:
                    return False, f"Contains keyword '{keyword}' likely indicating cluster markers"

            # Check for typical count matrix structure
            # Should have numeric data. We expect a header row and then numeric rows.
            lines = content_str.split('\n')
            if len(lines) < 2:
                return False, "File has insufficient lines for a matrix"

            # Skip empty lines
            non_empty_lines = [l for l in lines if l.strip()]
            if len(non_empty_lines) < 2:
                return False, "File has insufficient non-empty lines"

            # Check if the second line (first data row) contains numbers
            # Raw count matrices usually have a header, then rows of numbers (or gene IDs + numbers)
            first_data_line = non_empty_lines[1].strip()
            parts = first_data_line.split()
            
            # Heuristic: At least one part should be a number or a string that looks like a count
            has_numeric = False
            for part in parts:
                # Remove common delimiters
                clean_part = part.replace(',', '').replace('.', '')
                try:
                    float(clean_part)
                    has_numeric = True
                    break
                except ValueError:
                    continue

            if not has_numeric:
                return False, "No numeric data found in first data row"

            return True, "Appears to be a raw count matrix"

        except Exception as e:
            logger.error(f"Error inspecting file {file_path}: {e}")
            return False, f"Inspection error: {e}"

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        return calculate_md5(file_path)

    def verify_dataset(self, accession: str) -> Dict[str, Any]:
        """
        Verifies a specific dataset:
        1. Checks if the file exists in raw_data_dir.
        2. Validates checksum if a checksum file exists.
        3. Verifies content is a raw count matrix.
        
        Args:
            accession: GSE accession ID (e.g., 'GSE131907')
        
        Returns:
            Dict containing status and details.
        """
        result = {
            "accession": accession,
            "status": DatasetStatus.MISSING,
            "file_path": None,
            "checksum_valid": None,
            "is_raw_count": None,
            "reason": None
        }

        # Determine expected file path
        # We assume the download logic saves files as {accession}_counts.{ext}
        # or similar. We'll look for files starting with the accession.
        expected_files = list(self.raw_data_dir.glob(f"{accession}*"))
        
        if not expected_files:
            result["reason"] = "No files found for accession"
            return result

        # Take the first matching file (assuming one per accession for now)
        file_path = expected_files[0]
        result["file_path"] = str(file_path)

        # 1. Validate Checksum
        checksum_file = file_path.with_suffix(file_path.suffix + '.md5')
        if checksum_file.exists():
            try:
                with open(checksum_file, 'r') as f:
                    expected_md5 = f.read().strip()
                
                actual_md5 = self._calculate_file_checksum(file_path)
                
                if actual_md5.lower() == expected_md5.lower():
                    result["checksum_valid"] = True
                    logger.info(f"Checksum valid for {accession}: {actual_md5}")
                else:
                    result["checksum_valid"] = False
                    result["status"] = DatasetStatus.CHECKSUM_MISMATCH
                    result["reason"] = f"Checksum mismatch. Expected: {expected_md5}, Got: {actual_md5}"
                    return result
            except Exception as e:
                result["checksum_valid"] = False
                result["reason"] = f"Checksum validation error: {e}"
                return result
        else:
            logger.warning(f"No checksum file found for {accession}. Skipping checksum validation.")
            result["checksum_valid"] = "skipped"

        # 2. Verify Raw Count Matrix Content
        is_valid, reason = self._is_raw_count_matrix(file_path)
        result["is_raw_count"] = is_valid
        
        if is_valid:
            result["status"] = DatasetStatus.FOUND
            result["reason"] = reason
        else:
            result["status"] = DatasetStatus.INVALID_FORMAT
            result["reason"] = reason

        return result

    def resolve_all_gaps(self) -> Dict[str, Any]:
        """
        Resolves data gaps for all configured accessions.
        
        Returns:
            Summary report of all datasets.
        """
        report = {
            "datasets": {},
            "summary": {
                "total": len(self.accessions),
                "found": 0,
                "missing": 0,
                "invalid": 0,
                "checksum_mismatch": 0
            }
        }

        for accession in self.accessions:
            logger.info(f"Verifying dataset: {accession}")
            verification = self.verify_dataset(accession)
            report["datasets"][accession] = verification
            
            status = verification["status"]
            if status == DatasetStatus.FOUND:
                report["summary"]["found"] += 1
            elif status == DatasetStatus.MISSING:
                report["summary"]["missing"] += 1
            elif status == DatasetStatus.INVALID_FORMAT:
                report["summary"]["invalid"] += 1
            elif status == DatasetStatus.CHECKSUM_MISMATCH:
                report["summary"]["checksum_mismatch"] += 1

        # Save report
        report_path = self.results_dir / "data_gap_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Data gap report saved to {report_path}")
        return report

def main():
    """Main entry point for data gap resolution."""
    config = Config()
    resolver = DataGapResolver(config)
    report = resolver.resolve_all_gaps()
    
    print(json.dumps(report, indent=2))
    
    # Exit with error if no datasets found
    if report["summary"]["found"] == 0:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()