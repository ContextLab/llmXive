"""
Robust error handling wrapper for xtb subprocess calls.

This module provides a wrapper for calling the xtb executable with retry logic,
timeout enforcement, and comprehensive logging. It is designed to handle the
GFN2-xTB geometry optimization and energy calculation steps required for
conformer ranking.

Per task T002, xtb is installed via conda-forge/system package manager and
is NOT a pip dependency. The wrapper assumes 'xtb' is available in the PATH
or via the XTB_BINARY environment variable.
"""

import os
import subprocess
import time
import signal
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass

from config import get_config, get_paths, get_resources
from utils.logging import get_project_logger
from utils.seeds import set_global_seed


# Constants
DEFAULT_TIMEOUT_SECONDS = 600  # 10 minutes per calculation
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
XTB_TIMEOUT_EXIT_CODE = 124  # Standard timeout exit code if killed by timeout

# Logger instance
logger = get_project_logger("energy_calc")


@dataclass
class XtbResult:
    """Container for xtb calculation results."""
    success: bool
    energy: Optional[float] = None
    gradient_norm: Optional[float] = None
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error_message: Optional[str] = None
    calculation_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


def _find_xtb_binary() -> str:
    """
    Locate the xtb binary in the system PATH or via environment variable.

    Returns:
        str: Path to the xtb binary.

    Raises:
        FileNotFoundError: If xtb is not found.
    """
    env_path = os.environ.get("XTB_BINARY")
    if env_path and os.path.isfile(env_path):
        logger.info(f"XTB binary found via environment variable: {env_path}")
        return env_path

    # Try to find in PATH
    result = shutil.which("xtb")
    if result:
        logger.info(f"XTB binary found in PATH: {result}")
        return result

    raise FileNotFoundError(
        "xtb binary not found. Please install xtb via conda-forge or set "
        "XTB_BINARY environment variable to the full path of the xtb executable."
    )


def _prepare_xtb_input(
    coordinates: List[Tuple[str, float, float, float]],
    charge: int = 0,
    mult: int = 1,
) -> Path:
    """
    Prepare an xtb input file (xyz format) for a single calculation.

    Args:
        coordinates: List of tuples (element, x, y, z).
        charge: Total charge of the system.
        mult: Multiplicity of the system.

    Returns:
        Path: Path to the temporary input file.
    """
    fd, input_path = tempfile.mkstemp(suffix=".xyz", prefix="xtb_input_")
    with os.fdopen(fd, 'w') as f:
        f.write(f"{len(coordinates)}\n")
        f.write(f"xtb calculation charge={charge} mult={mult}\n")
        for element, x, y, z in coordinates:
            f.write(f"{element:2s} {x:18.10f} {y:18.10f} {z:18.10f}\n")

    logger.debug(f"Created xtb input file: {input_path}")
    return Path(input_path)


def _parse_xtb_output(output_path: Path) -> Tuple[Optional[float], Optional[float], str]:
    """
    Parse the xtb output file to extract energy and gradient norm.

    Args:
        output_path: Path to the xtb output file (usually 'xtb.out').

    Returns:
        Tuple of (energy, gradient_norm, full_output_text).
    """
    energy = None
    gradient_norm = None
    output_text = ""

    if not output_path.exists():
        return None, None, ""

    output_text = output_path.read_text()

    # Parse energy (look for "TOTAL ENERGY")
    for line in output_text.splitlines():
        if "TOTAL ENERGY" in line:
            try:
                # Format: "TOTAL ENERGY ... = -123.456789 a.u."
                parts = line.split("=")
                if len(parts) > 1:
                    energy_str = parts[-1].strip().split()[0]
                    energy = float(energy_str)
            except (ValueError, IndexError):
                logger.warning(f"Failed to parse energy from line: {line}")

        if "GRADIENT NORM" in line:
            try:
                parts = line.split("=")
                if len(parts) > 1:
                    grad_str = parts[-1].strip().split()[0]
                    gradient_norm = float(grad_str)
            except (ValueError, IndexError):
                logger.warning(f"Failed to parse gradient norm from line: {line}")

    return energy, gradient_norm, output_text


def run_xtb_optimization(
    coordinates: List[Tuple[str, float, float, float]],
    charge: int = 0,
    mult: int = 1,
    max_iterations: int = 500,
    timeout_seconds: Optional[int] = None,
    retry_count: int = 0,
) -> XtbResult:
    """
    Run a GFN2-xTB geometry optimization with robust error handling.

    This function:
    1. Locates the xtb binary.
    2. Prepares a temporary input file.
    3. Executes xtb with a timeout.
    4. Parses the output for energy and gradient norm.
    5. Implements retry logic on failure (up to MAX_RETRIES).
    6. Logs all events and results.

    Args:
        coordinates: List of (element, x, y, z) tuples for the molecule.
        charge: Total molecular charge.
        mult: Spin multiplicity.
        max_iterations: Maximum number of optimization steps.
        timeout_seconds: Timeout for the calculation (defaults to config value).
        retry_count: Current retry attempt (internal use).

    Returns:
        XtbResult: Structured result containing success status, energy, etc.
    """
    config = get_config()
    paths = get_paths()
    resources = get_resources()

    # Use config timeout if not specified
    if timeout_seconds is None:
        timeout_seconds = DEFAULT_TIMEOUT_SECONDS

    # Ensure xtb is available
    try:
        xtb_binary = _find_xtb_binary()
    except FileNotFoundError as e:
        logger.error(f"xtb binary not found: {e}")
        return XtbResult(
            success=False,
            error_message=f"xtb binary not found: {e}",
            exit_code=-1,
        )

    # Prepare input
    input_path = _prepare_xtb_input(coordinates, charge, mult)
    output_path = input_path.with_name(input_path.stem + ".out")
    work_dir = input_path.parent

    start_time = time.time()
    attempt = retry_count + 1

    logger.info(
        f"Starting xtb optimization (attempt {attempt}/{MAX_RETRIES}) "
        f"for {len(coordinates)} atoms. Timeout: {timeout_seconds}s"
    )

    try:
        # Build command
        # xtb input.xyz --opt --gfn 2 --maxiter N --charge C --uhf U --threads T
        cmd = [
            xtb_binary,
            str(input_path),
            "--opt",
            "--gfn", "2",
            "--maxiter", str(max_iterations),
            "--charge", str(charge),
            "--uhf", str(mult - 1),  # xtb uses 'uhf' for multiplicity-1
            "--threads", str(resources.cpu_threads),
        ]

        # Execute with timeout
        proc = subprocess.run(
            cmd,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )

        calc_time = time.time() - start_time

        # Check for timeout
        if proc.returncode == XTB_TIMEOUT_EXIT_CODE or proc.returncode == -signal.SIGKILL:
            logger.warning(
                f"xtb calculation timed out after {timeout_seconds}s (attempt {attempt})"
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
                return run_xtb_optimization(
                    coordinates, charge, mult, max_iterations,
                    timeout_seconds, retry_count=attempt
                )
            else:
                return XtbResult(
                    success=False,
                    exit_code=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    error_message="Calculation timed out after all retries",
                    calculation_time=calc_time,
                )

        # Parse output
        energy, grad_norm, output_text = _parse_xtb_output(output_path)

        # Determine success
        # xtb returns 0 on success, but we also check if energy was parsed
        success = proc.returncode == 0 and energy is not None

        if not success:
            logger.warning(
                f"xtb calculation failed (attempt {attempt}). "
                f"Return code: {proc.returncode}, Energy parsed: {energy is not None}"
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
                return run_xtb_optimization(
                    coordinates, charge, mult, max_iterations,
                    timeout_seconds, retry_count=attempt
                )
            else:
                return XtbResult(
                    success=False,
                    exit_code=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    error_message=f"Calculation failed. Return code: {proc.returncode}",
                    calculation_time=calc_time,
                )

        logger.info(
            f"xtb optimization successful (attempt {attempt}). "
            f"Energy: {energy:.6f} Ha, Gradient Norm: {grad_norm:.6f}"
        )

        return XtbResult(
            success=True,
            energy=energy,
            gradient_norm=grad_norm,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            calculation_time=calc_time,
            metadata={
                "xtb_binary": xtb_binary,
                "max_iterations": max_iterations,
                "charge": charge,
                "mult": mult,
                "atoms": len(coordinates),
            }
        )

    except subprocess.TimeoutExpired:
        logger.error(f"xtb calculation timed out after {timeout_seconds}s")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)
            return run_xtb_optimization(
                coordinates, charge, mult, max_iterations,
                timeout_seconds, retry_count=attempt
            )
        else:
            return XtbResult(
                success=False,
                exit_code=124,
                error_message="Calculation timed out after all retries",
                calculation_time=time.time() - start_time,
            )

    except Exception as e:
        logger.error(f"xtb calculation failed with exception: {e}")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)
            return run_xtb_optimization(
                coordinates, charge, mult, max_iterations,
                timeout_seconds, retry_count=attempt
            )
        else:
            return XtbResult(
                success=False,
                error_message=str(e),
                exit_code=-1,
                calculation_time=time.time() - start_time,
            )

    finally:
        # Cleanup temporary files
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()


def run_xtb_single_point(
    coordinates: List[Tuple[str, float, float, float]],
    charge: int = 0,
    mult: int = 1,
    timeout_seconds: Optional[int] = None,
) -> XtbResult:
    """
    Run a GFN2-xTB single-point energy calculation.

    Similar to run_xtb_optimization but without geometry optimization.

    Args:
        coordinates: List of (element, x, y, z) tuples.
        charge: Total charge.
        mult: Multiplicity.
        timeout_seconds: Timeout in seconds.

    Returns:
        XtbResult: Calculation result.
    """
    config = get_config()
    resources = get_resources()

    if timeout_seconds is None:
        timeout_seconds = DEFAULT_TIMEOUT_SECONDS

    try:
        xtb_binary = _find_xtb_binary()
    except FileNotFoundError as e:
        logger.error(f"xtb binary not found: {e}")
        return XtbResult(
            success=False,
            error_message=f"xtb binary not found: {e}",
            exit_code=-1,
        )

    input_path = _prepare_xtb_input(coordinates, charge, mult)
    output_path = input_path.with_name(input_path.stem + ".out")
    work_dir = input_path.parent

    start_time = time.time()

    try:
        cmd = [
            xtb_binary,
            str(input_path),
            "--gfn", "2",
            "--charge", str(charge),
            "--uhf", str(mult - 1),
            "--threads", str(resources.cpu_threads),
        ]

        proc = subprocess.run(
            cmd,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )

        calc_time = time.time() - start_time

        if proc.returncode == XTB_TIMEOUT_EXIT_CODE:
            return XtbResult(
                success=False,
                exit_code=124,
                error_message="Single-point calculation timed out",
                calculation_time=calc_time,
            )

        energy, _, output_text = _parse_xtb_output(output_path)

        success = proc.returncode == 0 and energy is not None

        if not success:
            return XtbResult(
                success=False,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                error_message=f"Single-point calculation failed. Return code: {proc.returncode}",
                calculation_time=calc_time,
            )

        return XtbResult(
            success=True,
            energy=energy,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            calculation_time=calc_time,
            metadata={
                "xtb_binary": xtb_binary,
                "charge": charge,
                "mult": mult,
                "atoms": len(coordinates),
            }
        )

    except subprocess.TimeoutExpired:
        return XtbResult(
            success=False,
            exit_code=124,
            error_message="Single-point calculation timed out",
            calculation_time=time.time() - start_time,
        )

    except Exception as e:
        return XtbResult(
            success=False,
            error_message=str(e),
            exit_code=-1,
            calculation_time=time.time() - start_time,
        )

    finally:
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()