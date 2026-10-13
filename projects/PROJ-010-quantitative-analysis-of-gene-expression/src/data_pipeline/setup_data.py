import os
import hashlib
import yaml
import GEOparse
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    # 1. Initialize directories
    # Using paths.data and paths.figures creates the folders automatically
    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")
    figures_dir = paths.figures()
    
    log.info(f"Initializing project directories: {raw_dir}, {processed_dir}, {figures_dir}")

    # 2. Verify accessibility and download raw metadata
    # GSE124310 is a known human fetal brain scRNA-seq dataset
    gse_id = "GSE124310"
    log.info(f"Verifying accessibility of {gse_id} via GEOparse...")
    
    try:
        # Download the metadata (SOFT file) to verify connectivity and provide a raw artifact
        gse = GEOparse.get_GEO(geo=gse_id, destdir=str(raw_dir))
        # GEOparse saves files as GSEXXXX_family.soft or similar. 
        # We locate the actual downloaded file to checksum it.
        downloaded_files = [f for f in os.listdir(raw_dir) if gse_id in f]
        if not downloaded_files:
            raise FileNotFoundError(f"GEOparse did not save files for {gse_id} in {raw_dir}")
        
        target_file = raw_dir / downloaded_files[0]
        log.info(f"Successfully verified and downloaded: {target_file}")
    except Exception as e:
        log.error(f"Failed to access GEO data: {e}")
        raise

    # 3. Generate SHA-256 checksums
    log.info("Generating checksums for raw inputs...")
    checksum = calculate_sha256(target_file)
    
    # 4. Record in project state YAML
    state = {
        "project_id": "PROJ-010-quantitative-analysis-of-gene-expression",
        "raw_inputs": [
            {
                "file": str(target_file.relative_to(paths.root)),
                "sha256": checksum,
                "source": f"GEO:{gse_id}"
            }
        ],
        "status": "initialized"
    }
    
    state_path = paths.data("project_state.yaml")
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False)
    
    log.info(f"Project state recorded at {state_path}")

if __name__ == "__main__":
    main()
