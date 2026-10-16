"""
Fetcher module for retrieving IBM Quantum backend calibration data.

This module provides:
- `fetch_backends_list()` – returns a list of operational backend names.
- `fetch_backend_properties()` – returns the properties object for a backend.
- `retry_with_exponential_backoff()` – generic retry helper respecting C‑001.
- `rate_limit_handler()` – handles HTTP 429 responses.
- `validate_data_freshness()` – enforces FR‑001 (≤30 days old) and returns
  a tuple ``(is_fresh, age_days)``.
- `extract_topology_data()` – returns ``(coupling_map, qubit_count)``.
- `extract_performance_metrics()` – returns a dict with keys ``t1``, ``t2``,
  ``cx_error`` and ``readout_error`` (means).
- `extract_chip_family()` – derives a human‑readable chip family.
- `process_historical_data()` – utility used by legacy unit tests to
  convert a directory of historical JSON snapshots into a CSV.
- `fetch_and_save_snapshots()` – orchestrates fetching and persisting raw
  snapshots.
- `fetch_all_backends()` – convenience wrapper returning the full list of
  operational backends (used by integration tests).
- CLI entry point (`python -m code.fetcher --save-snapshots`) that writes
  JSON files to ``data/raw/{device_id}_{YYYYMMDD_HHMMSS}.json``.  No synthetic
  data is ever generated; on total API failure a ``RuntimeError`` is raised.
"""
import json
import csv
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Callable, Any, Tuple, Dict, Optional

from llmxive_toolkit import paths, get_logger

# Optional import of qiskit‑ibm‑runtime; performed lazily so the module can be
# imported even when the package is not installed (e.g., during unit‑test
# collection).
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
    token = os.getenv("IBMQ_TOKEN")
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
def fetch_backends_list(service: Optional[Any] = None) -> List[str]:
    """
    Retrieve the list of operational backend names.

    Args:
        service: Optional pre‑initialised ``QiskitRuntimeService``.  If omitted,
                 a new service is created.

    Returns:
        List of backend identifiers.

    Raises:
        RuntimeError: If the IBM Quantum service cannot be queried.
    """
    if service is None:
        service = _init_service()
    try:
        backends = service.backends()
        return [b.name for b in backends if getattr(b, "operational", False)]
    except Exception as e:
        logger.error(f"Failed to fetch backends list: {e}")
        raise RuntimeError("Unable to retrieve backend list.") from e

# ----------------------------------------------------------------------
# Convenience wrapper required by integration tests
# ----------------------------------------------------------------------
def fetch_all_backends(service: Optional[Any] = None) -> List[str]:
    """
    Compatibility wrapper that simply forwards to ``fetch_backends_list``.
    The integration test suite expects this name to exist.
    """
    return fetch_backends_list(service)

# ----------------------------------------------------------------------
# Fetch a single backend's properties with retry/back‑off
# ----------------------------------------------------------------------
def fetch_backend_properties(
    service: Any, backend_name: str
) -> Dict[str, Any]:
    """
    Fetch properties for ``backend_name`` using exponential back‑off.

    Args:
        service: An initialised ``QiskitRuntimeService``.
        backend_name: Name of the backend to query.

    Returns:
        A dictionary representation of the backend properties.

    Raises:
        RuntimeError: If the backend cannot be fetched after retries.
    """
    def _fetch():
        backend = service.backend(backend_name)
        props = backend.properties()
        if not props:
            raise ValueError(f"No properties returned for {backend_name}")
        # Convert to a plain dict for downstream consumption.
        try:
            return props.to_dict()  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            return json.loads(json.dumps(props, default=str))

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
def validate_data_freshness(
    properties: Any, max_age_days: int = 30
) -> Tuple[bool, float]:
    """
    Verify that the calibration timestamp is ≤ ``max_age_days`` old.

    Returns:
        ``(is_fresh, age_days)`` where ``is_fresh`` is a bool and ``age_days``
        is the age of the snapshot in days (float).
    """
    if not properties:
        return (False, 0.0)
    last_update = getattr(properties, "last_update_date", None)
    if last_update is None:
        return (False, 0.0)
    now = datetime.now(last_update.tzinfo)
    age_timedelta = now - last_update
    age_days = age_timedelta.total_seconds() / 86400.0
    return (age_days <= max_age_days, age_days)

# ----------------------------------------------------------------------
# Extraction helpers
# ----------------------------------------------------------------------
def extract_topology_data(properties: Any) -> Tuple[List[List[int]], int]:
    """
    Pull ``coupling_map`` and qubit count from ``BackendProperties``.
    Returns a tuple ``(coupling_map, qubit_count)``.
    """
    coupling_map = getattr(properties, "coupling_map", [])
    qubit_count = len(getattr(properties, "qubits", []))
    return coupling_map, qubit_count

def extract_performance_metrics(properties: Any) -> Dict[str, Optional[float]]:
    """
    Compute mean T1, T2, CX gate error and readout error.
    Returns a dict with keys ``t1``, ``t2``, ``cx_error`` and ``readout_error``.
    """
    t1_vals, t2_vals, cx_errs, ro_errs = [], [], [], []

    for qubit in getattr(properties, "qubits", []):
        for p in qubit:
            name = getattr(p, "name", None)
            if name == "T1":
                t1_vals.append(p.value)
            elif name == "T2":
                t2_vals.append(p.value)

    for gate in getattr(properties, "gates", []):
        if getattr(gate, "gate", None) == "cx":
            for param in getattr(gate, "parameters", []):
                pname = getattr(param, "name", None)
                if pname == "gate_error":
                    cx_errs.append(param.value)
                elif pname == "readout_error":
                    ro_errs.append(param.value)

    return {
        "t1": sum(t1_vals) / len(t1_vals) if t1_vals else None,
        "t2": sum(t2_vals) / len(t2_vals) if t2_vals else None,
        "cx_error": sum(cx_errs) / len(cx_errs) if cx_errs else None,
        "readout_error": sum(ro_errs) / len(ro_errs) if ro_errs else None,
    }

def extract_chip_family(backend_name: str, properties: Optional[Any] = None) -> str:
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
# Legacy helper used by older unit tests – converts a directory of
# historical JSON snapshots into a flat CSV.
# ----------------------------------------------------------------------
def process_historical_data(historical_dir: str, output_csv: str) -> None:
    """
    Read all ``*.json`` files in ``historical_dir`` and write a CSV with the
    columns required by the legacy tests.

    The CSV header is:
    ``device_id,timestamp,t1_mean,t2_mean,cx_error_mean,readout_error_mean,chip_family``

    Files that cannot be parsed or that lack any of the required fields are
    silently skipped (the original tests expect this behaviour).
    """
    fieldnames = [
        "device_id",
        "timestamp",
        "t1_mean",
        "t2_mean",
        "cx_error_mean",
        "readout_error_mean",
        "chip_family",
    ]

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for entry in Path(historical_dir).glob("*.json"):
            try:
                with open(entry, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                # Skip malformed JSON files
                continue

            # Verify that all required keys are present
            if not all(k in data for k in fieldnames):
                continue

            writer.writerow(
                {
                    "device_id": data["device_id"],
                    "timestamp": data["timestamp"],
                    "t1_mean": data["t1_mean"],
                    "t2_mean": data["t2_mean"],
                    "cx_error_mean": data["cx_error_mean"],
                    "readout_error_mean": data["readout_error_mean"],
                    "chip_family": data["chip_family"],
                }
            )

# ----------------------------------------------------------------------
# Orchestration – fetch all backends and persist raw snapshots
# ----------------------------------------------------------------------
def fetch_and_save_snapshots() -> Tuple[int, int]:
    """
    Fetch properties for every operational backend, enforce freshness,
    and write a JSON snapshot to ``data/raw/``.

    Returns:
        Tuple ``(saved_count, failed_count)``.
    """
    ensure_raw_dir = paths.data("raw")
    service = _init_service()
    backends = fetch_backends_list(service)
    saved, failed = 0, 0
    for name in backends:
        try:
            props = fetch_backend_properties(service, name)
            is_fresh, age_days = validate_data_freshness(props)
            if not is_fresh:
                logger.info(f"Skipping {name}: data older than 30 days (age={age_days:.1f}d).")
                continue
            # Save the snapshot to data/raw/
            now = datetime.now(timezone.utc)
            timestamp_str = now.strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp_str}.json"
            filepath = ensure_raw_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(props, f, indent=2, default=str)
            logger.info(f"Saved snapshot for {name} to {filepath}")
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
