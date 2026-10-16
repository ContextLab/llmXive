"""
Fetcher module for retrieving IBM Quantum backend calibration data.

This module provides:
- `fetch_backends_list()` – returns a list of operational backend names.
- `fetch_backend_properties(backend_name)` – returns the properties object for a backend.
- `retry_with_exponential_backoff()` – generic retry helper respecting C‑001.
- `rate_limit_handler()` – handles HTTP 429 responses.
- `validate_data_freshness()` – enforces FR‑001 (≤30 days old).
- `extract_topology_data()`, `extract_performance_metrics()`, `extract_chip_family()`.
- `fetch_and_save_snapshots()` – orchestrates fetching and persisting raw snapshots.
- CLI entry point (`python -m code.fetcher --save-snapshots`) that writes JSON files
  to ``data/raw/{device_id}_{YYYYMMDD_HHMMSS}.json``.  No synthetic data is ever
  generated; on total API failure a ``RuntimeError`` is raised.
"""
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Callable, Any

from config import load_config
from logging_config import get_logger
from snapshot_saver import save_backend_snapshot

# Optional import of qiskit‑ibm‑runtime; will be performed lazily inside
# ``_init_service`` so that the module can be imported even when the
# package is not installed (e.g., during unit‑test collection).
try:
    from qiskit_ibm_runtime import QiskitRuntimeService
except Exception:  # pragma: no cover
    QiskitRuntimeService = None

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper to initialise the IBM Quantum service
# ----------------------------------------------------------------------
def _init_service() -> Any:
    """
    Initialise ``QiskitRuntimeService`` using environment variables.

    Returns:
        An authenticated ``QiskitRuntimeService`` instance.

    Raises:
        RuntimeError: If the token is missing or the service cannot be created.
    """
    config = load_config()
    token = getattr(config, "ibmq_token", None) or config.get("IBMQ_TOKEN")
    if not token:
        raise RuntimeError(
            "IBMQ_TOKEN not found in environment. "
            "Fetching real calibration data requires a valid token."
        )
    if QiskitRuntimeService is None:
        raise RuntimeError(
            "qiskit‑ibm‑runtime is not installed. "
            "Install it via ``pip install qiskit‑ibm‑runtime``."
        )
    try:
        service = QiskitRuntimeService(channel="ibm_quantum", token=token)
        return service
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Failed to initialise IBM Quantum service: {e}") from e

# ----------------------------------------------------------------------
# Exponential backoff helper (C‑001)
# ----------------------------------------------------------------------
def retry_with_exponential_backoff(
    func: Callable[[], Any],
    max_attempts: int = 5,
    base_delay: float = 2.0,
    timeout: float = 30.0,
) -> Any:
    """
    Retry ``func`` with exponential back‑off.

    Args:
        func: Callable that performs the operation.
        max_attempts: Maximum number of attempts.
        base_delay: Initial delay in seconds.
        timeout: Upper bound for the total waiting time (seconds).

    Returns:
        The value returned by ``func`` on success.

    Raises:
        Exception: Propagates the last exception after exhausting attempts.
    """
    attempt = 0
    start = time.time()
    while attempt < max_attempts:
        try:
            return func()
        except Exception as e:
            attempt += 1
            if attempt == max_attempts:
                logger.error(f"Failed after {max_attempts} attempts: {e}")
                raise
            delay = base_delay * (2 ** (attempt - 1))
            elapsed = time.time() - start
            if elapsed + delay > timeout:
                logger.error(
                    f"Back‑off timeout reached ({timeout}s) after {attempt} attempts."
                )
                raise
            logger.warning(
                f"Attempt {attempt} failed ({e}). Retrying in {delay:.1f}s..."
            )
            time.sleep(delay)

# ----------------------------------------------------------------------
# Rate‑limit handler (429)
# ----------------------------------------------------------------------
def rate_limit_handler(response: Any) -> bool:
    """
    Detect HTTP 429 and pause according to ``Retry‑After`` header.

    Returns ``True`` if a pause was performed, ``False`` otherwise.
    """
    if getattr(response, "status_code", None) == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        logger.warning(f"Rate limited (429). Waiting {retry_after}s.")
        time.sleep(retry_after)
        return True
    return False

# ----------------------------------------------------------------------
# Backend enumeration
# ----------------------------------------------------------------------
def fetch_backends_list() -> List[str]:
    """
    Retrieve the list of operational backend names.

    Returns:
        List of backend identifiers.

    Raises:
        RuntimeError: If the IBM Quantum service cannot be queried.
    """
    service = _init_service()
    try:
        backends = service.backends()
        return [b.name for b in backends if getattr(b, "operational", False)]
    except Exception as e:
        logger.error(f"Failed to fetch backends list: {e}")
        raise RuntimeError("Unable to retrieve backend list.") from e

# ----------------------------------------------------------------------
# Fetch a single backend's properties with retry/back‑off
# ----------------------------------------------------------------------
def fetch_backend_properties(backend_name: str) -> Any:
    """
    Fetch properties for ``backend_name`` using exponential back‑off.

    Returns:
        The ``BackendProperties`` object.

    Raises:
        RuntimeError: If the backend cannot be fetched after retries.
    """
    service = _init_service()

    def _fetch():
        backend = service.backend(backend_name)
        props = backend.properties()
        if not props:
            raise ValueError(f"No properties returned for {backend_name}")
        return props

    try:
        return retry_with_exponential_backoff(_fetch)
    except Exception as e:
        logger.error(f"Failed to fetch properties for {backend_name}: {e}")
        raise RuntimeError(
            f"Unable to fetch properties for backend {backend_name}"
        ) from e

# ----------------------------------------------------------------------
# Freshness validation (FR‑001)
# ----------------------------------------------------------------------
def validate_data_freshness(properties: Any, max_age_days: int = 30) -> bool:
    """
    Verify that the calibration timestamp is ≤ ``max_age_days`` old.

    Args:
        properties: BackendProperties instance with ``last_update_date``.
        max_age_days: Maximum allowed age.

    Returns:
        ``True`` if data is fresh, ``False`` otherwise.
    """
    if not properties:
        return False
    last_update = getattr(properties, "last_update_date", None)
    if last_update is None:
        return False
    now = datetime.now(last_update.tzinfo)
    age = now - last_update
    return age <= timedelta(days=max_age_days)

# ----------------------------------------------------------------------
# Extraction helpers
# ----------------------------------------------------------------------
def extract_topology_data(properties: Any) -> dict:
    """
    Pull ``coupling_map`` and qubit count from ``BackendProperties``.
    """
    coupling_map = getattr(properties, "coupling_map", [])
    qubit_count = len(getattr(properties, "qubits", []))
    return {"coupling_map": coupling_map, "qubit_count": qubit_count}

def extract_performance_metrics(properties: Any) -> dict:
    """
    Compute mean T1, T2, CX gate error and readout error.
    """
    t1_vals, t2_vals, cx_errs, ro_errs = [], [], [], []

    for qubit in getattr(properties, "qubits", []):
        for p in qubit:
            if getattr(p, "name", None) == "T1":
                t1_vals.append(p.value)
            elif getattr(p, "name", None) == "T2":
                t2_vals.append(p.value)

    for gate in getattr(properties, "gates", []):
        if getattr(gate, "gate", None) == "cx":
            for param in getattr(gate, "parameters", []):
                if getattr(param, "name", None) == "gate_error":
                    cx_errs.append(param.value)
                elif getattr(param, "name", None) == "readout_error":
                    ro_errs.append(param.value)

    return {
        "t1_mean": sum(t1_vals) / len(t1_vals) if t1_vals else None,
        "t2_mean": sum(t2_vals) / len(t2_vals) if t2_vals else None,
        "cx_error_mean": sum(cx_errs) / len(cx_errs) if cx_errs else None,
        "readout_error_mean": sum(ro_errs) / len(ro_errs) if ro_errs else None,
    }

def extract_chip_family(backend_name: str) -> str:
    """
    Derive a human‑readable chip family from the backend identifier.
    """
    name = backend_name.lower()
    if "falcon" in name:
        return "Falcon"
    if "hummingbird" in name:
        return "Hummingbird"
    if "eagle" in name:
        return "Eagle"
    if "osprey" in name:
        return "Osprey"
    if "condor" in name:
        return "Condor"
    return "Unknown"

# ----------------------------------------------------------------------
# Orchestration – fetch all backends and persist raw snapshots
# ----------------------------------------------------------------------
def fetch_and_save_snapshots() -> tuple[int, int]:
    """
    Fetch properties for every operational backend, enforce freshness,
    and write a JSON snapshot to ``data/raw/``.

    Returns:
        Tuple ``(saved_count, failed_count)``.
    """
    backends = fetch_backends_list()
    saved, failed = 0, 0
    for name in backends:
        try:
            props = fetch_backend_properties(name)
            if not validate_data_freshness(props):
                logger.info(f"Skipping {name}: data older than 30 days.")
                continue
            # Convert the BackendProperties object to a plain, serialisable dict.
            # ``BackendProperties`` implements ``to_dict`` in recent Qiskit versions;
            # fall back to ``json.dumps`` with ``default=str`` if unavailable.
            try:
                raw_dict = props.to_dict()  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover
                raw_dict = json.loads(json.dumps(props, default=str))
            # Persist the snapshot.
            save_backend_snapshot(name, raw_dict)
            saved += 1
        except Exception as e:
            logger.error(f"Failed processing {name}: {e}")
            failed += 1
    logger.info(f"Snapshot collection finished – saved: {saved}, failed: {failed}")
    if saved == 0:
        raise RuntimeError(
            "No backend snapshots were saved. All attempts failed – aborting."
        )
    return saved, failed

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main():
    """
    Command‑line interface.

    Supported flags:
    --save-snapshots   Fetch live calibration data and write JSON files.
    """
    import argparse

    parser = argparse.ArgumentParser(description="IBM Quantum calibration fetcher")
    parser.add_argument(
        "--save-snapshots",
        action="store_true",
        help="Fetch current backend properties and store raw JSON snapshots.",
    )
    args = parser.parse_args()

    if args.save_snapshots:
        try:
            fetch_and_save_snapshots()
        except RuntimeError as e:
            logger.critical(f"Fetcher terminated with error: {e}")
            raise

if __name__ == "__main__":
    main()
