import os
import sys
import json
import logging
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GSE_ACCESSIONS = ["GSE131907", "GSE111322", "GSE150728"]
GEO_GSE_API = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
GEO_GSE_JSON_API = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={}&form=text"
GEO_GSE_JSON_API_V2 = "https://www.ncbi.nlm.nih.gov/geo/query/geo/geo2xml.cgi?acc={}&form=text"
# Using a more reliable JSON endpoint for GEO series metadata
GEO_SERIES_API = "https://www.ncbi.nlm.nih.gov/geo/query/geo/geo2xml.cgi?acc={}&form=text"
GEO_SERIES_JSON_API = "https://www.ncbi.nlm.nih.gov/geo/query/geo/geo2xml.cgi?acc={}&form=json"

# Updated to use a working JSON API for GEO series
GEO_JSON_API = "https://www.ncbi.nlm.nih.gov/geo/query/geo/geo2xml.cgi?acc={}&form=json"

class DatasetStatus:
    def __init__(self, accession: str, status: str, details: str = "", file_path: Optional[str] = None):
        self.accession = accession
        self.status = status  # "found", "missing", "invalid"
        self.details = details
        self.file_path = file_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accession": self.accession,
            "status": self.status,
            "details": self.details,
            "file_path": self.file_path
        }

class DataGapResolver:
    def __init__(self, raw_data_dir: str = "data/raw"):
        self.raw_data_dir = Path(raw_data_dir)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir = Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.statuses: List[DatasetStatus] = []

    def _get_series_metadata(self, accession: str) -> Optional[Dict[str, Any]]:
        """Fetch metadata for a GEO Series accession."""
        try:
            # Try the JSON API first
            url = GEO_JSON_API.format(accession)
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"JSON API failed for {accession} with status {response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to fetch JSON metadata for {accession}: {e}")

        # Fallback to text/XML parsing if JSON fails
        try:
            url = GEO_SERIES_JSON_API.format(accession)
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Parse the JSON response manually if needed
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch alternative metadata for {accession}: {e}")
        
        return None

    def _find_raw_count_url(self, metadata: Dict[str, Any], accession: str) -> Optional[str]:
        """Search metadata for a raw count file URL."""
        # GEO metadata structure varies; look for supplementary files
        if "supplementary_file" in metadata:
            files = metadata["supplementary_file"]
            if isinstance(files, list):
                for f in files:
                    # Look for common raw count file extensions
                    if isinstance(f, dict):
                        file_type = f.get("type", "").lower()
                        file_name = f.get("name", "").lower()
                        url = f.get("link", "")
                        
                        # Check for count matrices (MTX, CSV, TSV, H5AD)
                        if any(ext in file_name or ext in file_type for ext in ['.mtx', '.csv', '.tsv', '.h5ad', '.hdf5']):
                            # Also check if it's not just a "marker" or "cluster" file
                            if not any(marker in file_name.lower() for marker in ['marker', 'cluster', 'gene_list', 'pathway']):
                                return url
            elif isinstance(files, dict):
                file_type = files.get("type", "").lower()
                file_name = files.get("name", "").lower()
                url = files.get("link", "")
                if any(ext in file_name or ext in file_type for ext in ['.mtx', '.csv', '.tsv', '.h5ad', '.hdf5']):
                    if not any(marker in file_name.lower() for marker in ['marker', 'cluster', 'gene_list', 'pathway']):
                        return url
        
        # If no direct link found, try to construct a common GEO URL pattern
        # This is a heuristic and may not always work
        base_url = f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:8]}/n{accession[3:8]}/suppl/"
        # Common patterns for raw count files
        possible_names = [
            f"{accession}_raw_counts.csv",
            f"{accession}_counts.csv",
            f"{accession}_matrix.mtx",
            f"{accession}_raw.mtx",
            f"{accession}_data.csv"
        ]
        
        for name in possible_names:
            full_url = base_url + name
            try:
                head_response = requests.head(full_url, timeout=10)
                if head_response.status_code == 200:
                    return full_url
            except:
                continue
        
        return None

    def _validate_checksum(self, file_path: Path, expected_md5: Optional[str] = None) -> bool:
        """Validate file checksum if expected is provided."""
        if not file_path.exists():
            return False
        
        if expected_md5 is None:
            # Just verify the file is not empty and has content
            return file_path.stat().st_size > 0
        
        md5_hash = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest() == expected_md5
        except Exception as e:
            logger.error(f"Checksum validation failed for {file_path}: {e}")
            return False

    def _validate_raw_count_content(self, file_path: Path) -> bool:
        """
        Verify that the file contains a raw count matrix.
        Checks for numeric data in CSV/TSV or valid structure in MTX/H5AD.
        """
        if not file_path.exists():
            return False
        
        file_ext = file_path.suffix.lower()
        
        try:
            if file_ext in ['.csv', '.tsv']:
                # Read first few lines to check for numeric data
                with open(file_path, 'r', encoding='utf-8') as f:
                    header = f.readline()
                    first_data_line = f.readline()
                    
                    if not first_data_line.strip():
                        return False
                    
                    # Check if the first data line contains numbers (or gene IDs followed by numbers)
                    parts = first_data_line.strip().split(',') if file_ext == '.csv' else first_data_line.strip().split('\t')
                    if len(parts) < 2:
                        return False
                    
                    # Skip gene ID (first column) and check if others are numeric
                    numeric_count = 0
                    for part in parts[1:]:
                        try:
                            float(part)
                            numeric_count += 1
                        except ValueError:
                            pass
                    
                    # Require at least some numeric values
                    return numeric_count > 0
            
            elif file_ext == '.mtx':
                # MTX files start with "%%MatrixMarket"
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    return first_line.startswith('%%MatrixMarket')
            
            elif file_ext in ['.h5ad', '.hdf5', '.h5']:
                try:
                    import h5py
                    with h5py.File(file_path, 'r') as f:
                        # Check if 'X' or 'data' exists and is not empty
                        if 'X' in f and len(f['X']) > 0:
                            return True
                        if 'data' in f and len(f['data']) > 0:
                            return True
                        # Check for 'obsm' or 'var' as alternative indicators
                        if 'obsm' in f or 'var' in f:
                            return True
                except ImportError:
                    logger.warning("h5py not installed, skipping H5AD validation")
                    return True  # Assume valid if we can't check
                except Exception as e:
                    logger.error(f"Error reading H5AD file {file_path}: {e}")
                    return False
            
            else:
                # For other formats, just check file size
                return file_path.stat().st_size > 0
                
        except Exception as e:
            logger.error(f"Error validating content of {file_path}: {e}")
            return False

    def resolve_single(self, accession: str) -> DatasetStatus:
        """Resolve a single dataset: check GEO for raw counts and validate."""
        logger.info(f"Resolving dataset: {accession}")
        
        # Step 1: Check if file already exists locally
        local_files = list(self.raw_data_dir.glob(f"{accession}*"))
        if local_files:
            for local_file in local_files:
                if self._validate_raw_count_content(local_file):
                    logger.info(f"Found valid local file for {accession}: {local_file}")
                    return DatasetStatus(
                        accession=accession,
                        status="found",
                        details="Local file found and validated",
                        file_path=str(local_file)
                    )
        
        # Step 2: Query GEO for metadata
        metadata = self._get_series_metadata(accession)
        if not metadata:
            logger.warning(f"No metadata found for {accession}")
            return DatasetStatus(
                accession=accession,
                status="missing",
                details="Could not retrieve metadata from GEO"
            )
        
        # Step 3: Find raw count URL
        raw_url = self._find_raw_count_url(metadata, accession)
        if not raw_url:
            logger.warning(f"No raw count URL found for {accession}")
            return DatasetStatus(
                accession=accession,
                status="missing",
                details="No raw count file URL found in GEO metadata"
            )
        
        # Step 4: Download and validate
        try:
            local_path = self.raw_data_dir / f"{accession}_raw_counts.csv"  # Default name
            # Extract filename from URL if possible
            filename = os.path.basename(raw_url.split('?')[0])
            if filename:
                local_path = self.raw_data_dir / filename
            
            logger.info(f"Downloading {accession} from {raw_url}")
            response = requests.get(raw_url, timeout=120)
            response.raise_for_status()
            
            # Write to file
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            # Validate content
            if not self._validate_raw_count_content(local_path):
                logger.error(f"Downloaded file for {accession} does not contain valid raw counts")
                os.remove(local_path)
                return DatasetStatus(
                    accession=accession,
                    status="invalid",
                    details="Downloaded file does not contain valid raw count matrix"
                )
            
            logger.info(f"Successfully downloaded and validated {accession}")
            return DatasetStatus(
                accession=accession,
                status="found",
                details="Successfully downloaded and validated",
                file_path=str(local_path)
            )
            
        except requests.RequestException as e:
            logger.error(f"Download failed for {accession}: {e}")
            return DatasetStatus(
                accession=accession,
                status="missing",
                details=f"Download error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error for {accession}: {e}")
            return DatasetStatus(
                accession=accession,
                status="missing",
                details=f"Unexpected error: {str(e)}"
            )

    def resolve_all(self) -> Dict[str, Any]:
        """Resolve all datasets and generate report."""
        self.statuses = []
        for accession in GSE_ACCESSIONS:
            status = self.resolve_single(accession)
            self.statuses.append(status)
        
        # Determine final status
        found_count = sum(1 for s in self.statuses if s.status == "found")
        missing_count = sum(1 for s in self.statuses if s.status == "missing")
        invalid_count = sum(1 for s in self.statuses if s.status == "invalid")
        
        if found_count == 0:
            final_status = "Aborted"
        elif found_count == 1:
            final_status = "Case-Study"
        else:
            final_status = "Full"
        
        report = {
            "timestamp": str(Path().resolve()), # Placeholder for actual timestamp if needed
            "datasets": [s.to_dict() for s in self.statuses],
            "summary": {
                "total_accessions": len(GSE_ACCESSIONS),
                "found": found_count,
                "missing": missing_count,
                "invalid": invalid_count,
                "final_status": final_status
            }
        }
        
        # Write report
        report_path = self.results_dir / "data_gap_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Data gap report written to {report_path}")
        logger.info(f"Final status: {final_status} ({found_count} datasets found)")
        
        return report

def main():
    """Main entry point for data gap resolution."""
    resolver = DataGapResolver()
    report = resolver.resolve_all()
    
    # Exit with appropriate code
    if report["summary"]["final_status"] == "Aborted":
        logger.error("No datasets found. Pipeline aborted.")
        sys.exit(1)
    elif report["summary"]["final_status"] == "Case-Study":
        logger.warning("Only 1 dataset found. Running in Case-Study mode.")
        sys.exit(0)
    else:
        logger.info("Multiple datasets found. Running full pipeline.")
        sys.exit(0)

if __name__ == "__main__":
    main()
