import json
import sys
import logging
from pathlib import Path

# Ensure code/ is in path for imports if running as script
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from data.mock_generator import generate_all_mock_data
from utils.logging import configure_root_logger
from config import get_config

logger = logging.getLogger(__name__)

def main():
    """Generate mock data files to disk for CI runs."""
    configure_root_logger()
    logger.info("Starting mock data generation for CI runs.")
    
    try:
        config = get_config()
        # Use a smaller default for CI if not specified, or read from config
        n_populations = getattr(config, 'mock_n_populations', 50)
        
        logger.info(f"Generating {n_populations} population records.")
        data = generate_all_mock_data(n_populations)
        
        # Define output paths relative to project root
        project_root = Path(__file__).parent.parent
        data_raw_dir = project_root / "data" / "raw"
        data_raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Write genomic data
        genomic_path = data_raw_dir / "genomic_vcf.json"
        with open(genomic_path, 'w') as f:
            json.dump(data['genomic'], f, indent=2)
        logger.info(f"Wrote genomic data to {genomic_path}")
        
        # Write environmental data
        env_path = data_raw_dir / "env_data.json"
        with open(env_path, 'w') as f:
            json.dump(data['environmental'], f, indent=2)
        logger.info(f"Wrote environmental data to {env_path}")
        
        # Write compound data
        compound_path = data_raw_dir / "compound_data.json"
        with open(compound_path, 'w') as f:
            json.dump(data['compound'], f, indent=2)
        logger.info(f"Wrote compound data to {compound_path}")
        
        logger.info("Mock data generation completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate mock data: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
