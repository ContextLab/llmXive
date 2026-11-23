import sys
import os
from config import init_config, ConfigError

def main():
    """
    Entry point for initializing the project configuration.
    Validates that all required environment variables and seeds are set.
    """
    try:
        config = init_config()
        print("Configuration loaded successfully:")
        print(f"  RANDOM_SEED: {config['RANDOM_SEED']}")
        print(f"  DRYAD_API_KEY: {'Set' if config.get('DRYAD_API_KEY') else 'Not Set (Optional)'}")
        print(f"  ANAGE_API_KEY: {'Set' if config.get('ANAGE_API_KEY') else 'Not Set (Optional)'}")
        
        # Set the seed for downstream modules
        from config import set_random_seed
        set_random_seed()
        
        print("Random seed initialized.")
        return 0
    except ConfigError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error during initialization: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
