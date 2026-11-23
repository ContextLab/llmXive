"""
Orchestration script for the RD Missing Data Mechanisms study.

This script validates configuration before simulation starts.
It serves as the entry point for the entire pipeline.
"""
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.logging_config import setup_logging, get_logger, log_simulation_start, log_error
from src.validators import validate_simulation_config
from src.generators.missingness import (
    load_simulation_config,
    load_missingness_config,
    load_estimation_config
)
from src.models import SimulationConfig

logger = get_logger(__name__)

def validate_configuration() -> bool:
    """
    Validate all configuration files before simulation starts.
    
    Returns:
        bool: True if all configurations are valid, False otherwise.
    """
    logger.info("Starting configuration validation...")
    
    try:
        # Load simulation configuration
        logger.info("Loading simulation configuration...")
        sim_config_raw = load_simulation_config()
        
        # Validate simulation configuration against schema
        logger.info("Validating simulation configuration schema...")
        is_valid, errors = validate_simulation_config(sim_config_raw)
        
        if not is_valid:
            logger.error("Simulation configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        
        logger.info("Simulation configuration is valid.")
        
        # Load missingness configuration
        logger.info("Loading missingness configuration...")
        missing_config_raw = load_missingness_config()
        
        # Basic validation of missingness config (rates and mechanisms)
        if "rates" not in missing_config_raw:
            logger.error("Missing 'rates' key in missingness configuration")
            return False
        
        if "mechanisms" not in missing_config_raw:
            logger.error("Missing 'mechanisms' key in missingness configuration")
            return False
        
        logger.info("Missingness configuration is valid.")
        
        # Load estimation configuration
        logger.info("Loading estimation configuration...")
        est_config_raw = load_estimation_config()
        
        # Basic validation of estimation config
        if "bandwidth_rule" not in est_config_raw:
            logger.error("Missing 'bandwidth_rule' key in estimation configuration")
            return False
        
        logger.info("Estimation configuration is valid.")
        
        # Create SimulationConfig object for further processing
        logger.info("Creating SimulationConfig object...")
        try:
            # Note: We use **sim_config_raw to unpack the dictionary
            # The actual SimulationConfig dataclass will be used later
            # for more detailed validation if needed
            pass
        except Exception as e:
            logger.error(f"Failed to create SimulationConfig object: {str(e)}")
            return False
        
        logger.info("All configurations validated successfully.")
        return True
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during configuration validation: {str(e)}")
        return False

def main():
    """
    Main entry point for the orchestration script.
    """
    # Setup logging
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("Starting RD Missing Data Mechanisms Study Orchestration")
    logger.info("=" * 60)
    
    log_simulation_start("T009", "Configuration Validation")
    
    try:
        # Validate configurations
        if not validate_configuration():
            logger.error("Configuration validation failed. Exiting.")
            return 1
        
        logger.info("Configuration validation passed. Ready to start simulation.")
        # TODO: Future tasks will implement the actual simulation logic here
        # For now, we just validate and exit successfully
        
        return 0
        
    except Exception as e:
        log_error("T009", str(e))
        logger.error(f"Orchestration failed: {str(e)}")
        return 1
    finally:
        log_simulation_end("T009")

if __name__ == "__main__":
    sys.exit(main())
