"""
Compile Runner for LLM Inference Kernel Benchmarks.

Orchestrates compilation of C++ kernels with dynamic flag injection,
binary hashing, and verification.
"""
import os
import sys
import subprocess
import hashlib
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

# Import from project API surface
from benchmarks.config import BenchmarkConfig, ConfigManager, validate_flags


class CompileRunner:
    """Orchestrates compilation of C++ kernels with optimization flags."""

    def __init__(self, kernel_dir: str, output_dir: str, compiler: str = "g++"):
        """
        Initialize the CompileRunner.

        Args:
            kernel_dir: Directory containing C++ kernel source files.
            output_dir: Directory to place compiled binaries.
            compiler: Compiler to use (g++ or clang++).
        """
        self.kernel_dir = Path(kernel_dir)
        self.output_dir = Path(output_dir)
        self.compiler = compiler
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_compiler_version(self) -> str:
        """Get the compiler version string."""
        try:
            result = subprocess.run(
                [self.compiler, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.split('\n')[0]
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get compiler version: {e}")

    def _hash_binary(self, binary_path: Path) -> str:
        """
        Calculate SHA-256 hash of a binary file.

        Args:
            binary_path: Path to the binary file.

        Returns:
            Hexadecimal SHA-256 hash string.
        """
        sha256_hash = hashlib.sha256()
        with open(binary_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def compile_kernel(
        self,
        source_file: Path,
        flags: List[str],
        output_name: Optional[str] = None
    ) -> Tuple[Path, str]:
        """
        Compile a C++ kernel with specified flags.

        Args:
            source_file: Path to the C++ source file.
            flags: List of compiler flags (e.g., ['-O2', '-march=native']).
            output_name: Optional name for the output binary. If None, derived from source.

        Returns:
            Tuple of (path_to_binary, sha256_hash).

        Raises:
            RuntimeError: If compilation fails.
        """
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")

        if output_name is None:
            output_name = source_file.stem

        output_path = self.output_dir / output_name

        cmd = [self.compiler] + flags + ["-O2", "-std=c++17", str(source_file), "-o", str(output_path)]

        # Add -O2 to flags if not present to ensure optimization, 
        # but allow specific flags to override if needed. 
        # Actually, the flags passed should be the full set. 
        # Let's construct the command carefully.
        # The 'flags' argument is expected to be the optimization flags like ['-O2', '-march=native'].
        # We add -std=c++17 and the source/output.
        
        full_cmd = [self.compiler] + flags + ["-std=c++17", str(source_file), "-o", str(output_path)]

        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            error_msg = f"Compilation failed for {source_file}:\n{e.stderr}"
            raise RuntimeError(error_msg)

        if not output_path.exists():
            raise RuntimeError(f"Compilation succeeded but binary not found: {output_path}")

        binary_hash = self._hash_binary(output_path)
        return output_path, binary_hash

    def compile_all_kernels(
        self,
        flags: List[str],
        kernel_pattern: str = "*.cpp"
    ) -> Dict[str, Tuple[Path, str]]:
        """
        Compile all C++ kernels matching the pattern with given flags.

        Args:
            flags: List of compiler flags.
            kernel_pattern: Glob pattern for source files.

        Returns:
            Dictionary mapping source filename to (binary_path, hash).
        """
        results = {}
        source_files = list(self.kernel_dir.glob(kernel_pattern))

        if not source_files:
            raise FileNotFoundError(f"No source files found matching {kernel_pattern} in {self.kernel_dir}")

        for source_file in source_files:
            output_path, binary_hash = self.compile_kernel(source_file, flags)
            results[source_file.name] = (output_path, binary_hash)

        return results

    def run_test_compilation(self) -> str:
        """
        Create a dummy C++ file, compile it, and return its SHA-256 hash.
        Used for verification.

        Returns:
            SHA-256 hash of the dummy binary.
        """
        dummy_source_code = """
        int main() {
            return 0;
        }
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(dummy_source_code)
            dummy_source_path = Path(f.name)

        try:
            output_path, binary_hash = self.compile_kernel(
                dummy_source_path,
                flags=["-O2"],
                output_name="dummy_test_binary"
            )
            return binary_hash
        finally:
            # Cleanup source
            if dummy_source_path.exists():
                dummy_source_path.unlink()
            # Cleanup binary if we want a clean state, but keeping it for inspection is fine.
            # The task says "outputs a SHA-256 hash", doesn't strictly say delete binary.
            # We'll leave the binary in the output dir for verification.


def main():
    """Main entry point for the compile runner."""
    parser = argparse.ArgumentParser(description="Compile and hash C++ kernels.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a test compilation of a dummy binary and output its SHA-256 hash."
    )
    parser.add_argument(
        "--kernel-dir",
        type=str,
        default="code/kernels",
        help="Directory containing C++ kernel source files."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/intermediates/binaries",
        help="Directory to place compiled binaries."
    )
    parser.add_argument(
        "--compiler",
        type=str,
        default="g++",
        choices=["g++", "clang++"],
        help="Compiler to use."
    )
    parser.add_argument(
        "--flags",
        type=str,
        nargs="+",
        default=["-O2"],
        help="Compiler flags to use (e.g., -O2 -march=native)."
    )

    args = parser.parse_args()

    runner = CompileRunner(
        kernel_dir=args.kernel_dir,
        output_dir=args.output_dir,
        compiler=args.compiler
    )

    if args.test:
        print(f"Running test compilation with compiler: {runner.compiler}")
        try:
            binary_hash = runner.run_test_compilation()
            print(f"SHA-256 hash of dummy binary: {binary_hash}")
        except Exception as e:
            print(f"Test compilation failed: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Validate flags
        if not validate_flags(args.flags):
            print(f"Invalid flags provided: {args.flags}", file=sys.stderr)
            sys.exit(1)

        print(f"Compiling kernels in {args.kernel_dir} with flags: {args.flags}")
        print(f"Output directory: {args.output_dir}")
        print(f"Compiler: {args.compiler}")

        try:
            results = runner.compile_all_kernels(flags=args.flags)
            print(f"Successfully compiled {len(results)} kernels:")
            for src_name, (bin_path, hash_val) in results.items():
                print(f"  {src_name} -> {bin_path.name} (SHA-256: {hash_val})")
        except Exception as e:
            print(f"Compilation failed: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
