"""
Configuration initialization script.

This script validates that all required environment variables are set
and provides a clean way to initialize configuration for the pipeline.

Usage:
    python code/00_init_config.py

This will:
1. Check for required environment variables
2. Set random seeds for Python and R
3. Print a success message if all checks pass
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from config import init_config, ConfigError

def main():
    """Main entry point for configuration initialization."""
    try:
        config = init_config()
        print("\n✓ Configuration initialized successfully!")
        print(f"  - Dryad API key: {'*' * len(config['dryad_api_key'])}")
        print(f"  - AnAge API key: {'*' * len(config['anage_api_key'])}")
        print(f"  - Random seed: {config['seed']}")
        return 0
    except ConfigError as e:
        print(f"\n✗ Configuration error: {e}", file=sys.stderr)
        print("\nPlease ensure the following environment variables are set:", file=sys.stderr)
        print("  - DRYAD_API_KEY", file=sys.stderr)
        print("  - ANAGE_API_KEY", file=sys.stderr)
        print("  - RANDOM_SEED", file=sys.stderr)
        print("\nYou can copy .env.example to .env and fill in your keys.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())