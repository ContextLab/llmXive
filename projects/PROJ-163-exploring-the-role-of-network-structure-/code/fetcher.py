"""
Fetcher module for retrieving IBM Quantum backend calibration data.

This module provides:
- `fetch_backends_list()` – returns a list of operational backend names.
- `fetch_backend_properties()` – returns the properties object for a backend.
- `retry_with_exponential_backoff()` – generic retry helper respecting C‑001.
- `rate_limit_handler()` – handles HTTP 429 responses.
- `validate_data_freshness()` – enforces FR‑001 (≤30 days old).
- `extract_performance_metrics()` – returns t1_mean, t2_mean, cx_error_mean, 
  readout_error_mean, and chip_family.
- `fetch_and_save_snapshots()` – orchestrates fetching and persisting raw snapshots.
"""
import json
import csv
import logging
import os
import time
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Callable, Any, Tuple, Dict, Optional

import pandas as pd
import numpy as np
from scipy.stats import spearmanr

from llmxive_toolkit import paths, get_logger

try:
    from qiskit_ibm_runtime import QiskitRuntimeService
except Exception:
    QiskitRuntimeService = None

logger = get_logger(__name__)

def _init_service() -> Any:
    """Initialise QiskitRuntimeService using environment variables."""
    token = os.getenv("IBMQ_TOKEN") or os.getenv("QISKIT_IBM_TOKEN")
    if not token:
        raise RuntimeError(
            "IBMQ_TOKEN not found in environment. "
            "Fetching real calibration data requires a valid token."
        )
    if QiskitRuntimeService is None:
        raise RuntimeError("qiskit-ibm-runtime is not installed.")
    try:
        return QiskitRuntimeService(channel="ibm_quantum", token=token)
    except Exception as e:
        raise RuntimeError(f"Failed to initialise IBM Quantum service: {e}") from e

def retry_with_exponential_backoff(
    func: Callable[[], Any],
    max_attempts: int = 5,
    base_delay: float = 2.0,
    timeout: float = 30.0,
) -> Any:
    """Retry func with exponential back-off (C-001)."""
    attempt = 0
    start = time.time()
    while attempt < max_attempts:
        try:
            return func()
        except Exception as e:
            attempt += 1
            if attempt == max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            if (time.time() - start) + delay > timeout:
                raise TimeoutError("Back-off timeout reached.")
            time.sleep(delay)

def rate_limit_handler(response: Any) -> bool:
    """Detect HTTP 429 and pause according to Retry-After header."""
    if getattr(response, "status_code", None) == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        time.sleep(retry_after)
        return True
    return False

def fetch_backends_list(service: Optional[Any] = None) -> List[str]:
    """Retrieve the list of operational backend names."""
    if service is None:
        service = _init_service()
    try:
        backends = service.backends()
        return [b.name for b in backends if getattr(b, "operational", False)]
    except Exception as e:
        raise RuntimeError("Unable to retrieve backend list.") from e

def fetch_all_backends(service: Optional[Any] = None) -> List[str]:
    """Compatibility wrapper for fetch_backends_list."""
    return fetch_backends_list(service)

def fetch_backend_properties(service: Any, backend_name: str) -> Dict[str, Any]:
    """Fetch properties for backend_name using exponential back-off."""
    def _fetch():
        backend = service.backend(backend_name)
        props = backend.properties()
        if not props:
            raise ValueError(f"No properties returned for {backend_name}")
        try:
            return props.to_dict()
        except Exception:
            return json.loads(json.dumps(props, default=str))
    return retry_with_exponential_backoff(_fetch)

def validate_data_freshness(properties: Any, max_age_days: int = 30) -> Tuple[bool, float]:
    """Verify that the calibration timestamp is <= max_age_days old (FR-001)."""
    if not properties:
        return (False, 0.0)
    
    # Handle both dict and object
    last_update = None
    if isinstance(properties, dict):
        last_update_str = properties.get("timestamp")
        if last_update_str:
            try:
                last_update = datetime.fromisoformat(last_update_str)
            except Exception: pass
    else:
        last_update = getattr(properties, "last_update_date", None)
        if last_update is None:
            ts = getattr(properties, "timestamp", None)
            if ts:
                try:
                    last_update = datetime.fromisoformat(ts)
                except Exception: pass

    if last_update is None:
        return (False, 0.0)

    if last_update.tzinfo is None:
        last_update = last_update.replace(tzinfo=timezone.utc)

    now = datetime.now(last_update.tzinfo)
    age_days = (now - last_update).total_seconds() / 86400.0
    return (age_days <= max_age_days, age_days)

def extract_chip_family(backend_name: str, properties: Optional[Any] = None) -> str:
    """Derive a human-readable chip family from the backend identifier."""
    name = backend_name.lower()
    for family in ["Falcon", "Hummingbird", "Eagle", "Osprey", "Condor"]:
        if family.lower() in name:
            return family
    return "Unknown"

def extract_performance_metrics(properties: Any, backend_name: str) -> Dict[str, Any]:
    """
    Extract performance metrics and chip family.
    Returns dict with t1_mean, t2_mean, cx_error_mean, readout_error_mean, chip_family.
    """
    t1_vals, t2_vals, cx_errs, ro_errs = [], [], [], []

    # Normalize properties to dict for easier access
    props_dict = properties if isinstance(properties, dict) else getattr(properties, "__dict__", {})
    if not props_dict and not isinstance(properties, dict):
        # Handle qiskit BackendProperties object specifically
        qubits = getattr(properties, "qubits", [])
        gates = getattr(properties, "gates", [])
    else:
        qubits = props_dict.get("qubits", [])
        gates = props_dict.get("gates", [])

    # Extract Qubit metrics
    for q_data in qubits:
        # q_data is usually a list of property objects/dicts
        for p in q_data:
            p_name = p.get("name") if isinstance(p, dict) else getattr(p, "name", None)
            p_val = p.get("value") if isinstance(p, dict) else getattr(p, "value", None)
            if p_name == "T1": t1_vals.append(p_val)
            elif p_name == "T2": t2_vals.append(p_val)

    # Extract Gate metrics
    for g_data in gates:
        g_type = g_data.get("gate") if isinstance(g_data, dict) else getattr(g_data, "gate", None)
        if g_type == "cx":
            params = g_data.get("parameters", []) if isinstance(g_data, dict) else getattr(g_data, "parameters", [])
            for param in params:
                p_name = param.get("name") if isinstance(param, dict) else getattr(param, "name", None)
                p_val = param.get("value") if isinstance(param, dict) else getattr(param, "value", None)
                if p_name == "gate_error": cx_errs.append(p_val)
                elif p_name == "readout_error": ro_errs.append(p_val)

    return {
        "t1_mean": sum(t1_vals) / len(t1_vals) if t1_vals else None,
        "t2_mean": sum(t2_vals) / len(t2_vals) if t2_vals else None,
        "cx_error_mean": sum(cx_errs) / len(cx_errs) if cx_errs else None,
        "readout_error_mean": sum(ro_errs) / len(ro_errs) if ro_errs else None,
        "chip_family": extract_chip_family(backend_name, properties),
    }

def fetch_and_save_snapshots() -> Tuple[int, int]:
    """Fetch properties for every operational backend and save JSON snapshots."""
    raw_dir = paths.data("raw")
    service = _init_service()
    backends = fetch_backends_list(service)
    saved, failed = 0, 0
    
    for name in backends:
        try:
            props = fetch_backend_properties(service, name)
            is_fresh, age_days = validate_data_freshness(props)
            if not is_fresh:
                logger.info(f"Skipping {name}: stale data ({age_days:.1f}d).")
                continue

            # Enrich with metrics and metadata
            metrics = extract_performance_metrics(props, name)
            enriched = dict(props) if isinstance(props, dict) else props.__dict__ if hasattr(props, "__dict__") else {}
            enriched.update(metrics)
            enriched["device_id"] = name
            
            now = datetime.now(timezone.utc)
            enriched["timestamp"] = now.isoformat()
            
            filename = f"{name}_{now.strftime('%Y%m%d_%H%M%S')}.json"
            with open(raw_dir / filename, "w", encoding="utf-8") as f:
                json.dump(enriched, f, indent=2, default=str)
            
            saved += 1
        except Exception as e:
            logger.error(f"Failed {name}: {e}")
            failed += 1
    
    if saved == 0:
        raise RuntimeError("No backend snapshots were saved. Aborting.")
    return saved, failed

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-snapshots", action="store_true")
    args = parser.parse_args()

    # Enforce token presence for real data (NFR-002)
    if not (os.getenv("IBMQ_TOKEN") or os.getenv("QISKIT_IBM_TOKEN")):
        raise RuntimeError("IBMQ token missing; fetching real data is required.")

    try:
        saved, failed = fetch_and_save_snapshots()
        logger.info(f"Completed: saved={saved}, failed={failed}")
    except Exception as e:
        logger.critical(f"Fetcher failed: {e}")
        raise

if __name__ == "__main__":
    main()
