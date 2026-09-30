"""
Checksum utility for verifying and calculating SHA256 hashes.
Used by the run-book to verify data integrity.
"""
import argparse
import hashlib
import sys
import logging
from pathlib import Path
import json

# Configure logging to stderr for CLI usage
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify a file's checksum against an expected value."""
    try:
        actual_checksum = calculate_sha256(file_path)
        if actual_checksum.lower() == expected_checksum.lower():
            logger.info(f"Checksum verified for {file_path}")
            return True
        else:
            logger.error(f"Checksum mismatch for {file_path}. "
                         f"Expected: {expected_checksum}, Got: {actual_checksum}")
            return False
    except Exception as e:
        logger.error(f"Verification failed for {file_path}: {e}")
        return False

def load_checksum_file(checksum_file: Path) -> dict:
    """Load a JSON checksum file."""
    if not checksum_file.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
    try:
        with open(checksum_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in checksum file {checksum_file}: {e}")

def generate_checksum_file(file_path: Path, output_path: Path) -> dict:
    """Generate a JSON checksum file for a given file."""
    checksum = calculate_sha256(file_path)
    data = {
        "file": str(file_path),
        "sha256": checksum,
        "algorithm": "sha256"
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Checksum file generated: {output_path}")
    return data

def cmd_verify(args):
    """CLI command to verify a file's checksum."""
    if not args.file or not args.checksum:
        parser_verify.error("--file and --checksum are required for verify")
    
    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    success = verify_checksum(file_path, args.checksum)
    sys.exit(0 if success else 1)

def cmd_calculate(args):
    """CLI command to calculate a file's checksum."""
    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    checksum = calculate_sha256(file_path)
    print(checksum)
    sys.exit(0)

def cmd_generate(args):
    """CLI command to generate a checksum file."""
    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    output_path = Path(args.output) if args.output else file_path.with_suffix(file_path.suffix + '.sha256.json')
    generate_checksum_file(file_path, output_path)
    sys.exit(0)

def main():
    """Main entry point for the checksum CLI."""
    parser = argparse.ArgumentParser(
        description='Calculate and verify SHA256 checksums.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Verify command
    parser_verify = subparsers.add_parser('verify', help='Verify a file against a checksum')
    parser_verify.add_argument('--file', required=True, help='Path to the file to verify')
    parser_verify.add_argument('--checksum', required=True, help='Expected SHA256 checksum')
    parser_verify.set_defaults(func=cmd_verify)

    # Calculate command
    parser_calc = subparsers.add_parser('calculate', help='Calculate SHA256 checksum of a file')
    parser_calc.add_argument('--file', required=True, help='Path to the file')
    parser_calc.set_defaults(func=cmd_calculate)

    # Generate command
    parser_gen = subparsers.add_parser('generate', help='Generate a JSON checksum file')
    parser_gen.add_argument('--file', required=True, help='Path to the file')
    parser_gen.add_argument('--output', help='Output path for the JSON file (default: <file>.sha256.json)')
    parser_gen.set_defaults(func=cmd_generate)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == '__main__':
    main()
