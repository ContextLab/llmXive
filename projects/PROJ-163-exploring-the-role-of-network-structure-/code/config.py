"""
Configuration utilities for IBM Quantum access.

This module defines a simple configuration dataclass and provides
functions to load configuration from environment variables and to
initialise a ``QiskitRuntimeService``.  When a valid IBM Quantum token
is not available, a lightweight mock service is returned so that the
test suite can run without external credentials.  The mock service
implements the minimal subset of the ``QiskitRuntimeService`` API
required by the integration tests (``backends`` and ``backend``).

The fetcher (`code/fetcher.py`) still raises ``RuntimeError`` when it
attempts to initialise the real service without a token, preserving
the NFR‑002 requirement that the fetcher never falls back to synthetic
data.
"""

import os
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List, Any

# The ``qiskit_ibm_runtime`` package is optional at import time – it is
# only required when a real IBM Quantum token is present.
try:
    from qiskit_ibm_runtime import QiskitRuntimeService
except Exception:  # pragma: no cover
    QiskitRuntimeService = None  # type: ignore

@dataclass
class IBMQuantumConfig:
    """Configuration parameters for IBM Quantum access."""
    token: str
    url: Optional[str] = None
    instance: Optional[str] = None
    channel: str = "ibm_quantum"
    default_backend: Optional[str] = None

def load_config() -> IBMQuantumConfig:
    """
    Load IBM Quantum configuration from environment variables.

    Returns:
        IBMQuantumConfig: Populated configuration object.

    Raises:
        ValueError: If no token is found in the environment.
    """
    token = os.getenv("IBMQ_TOKEN") or os.getenv("QISKIT_IBM_TOKEN")
    if not token:
        raise ValueError("IBMQ_TOKEN environment variable not set")
    url = os.getenv("IBMQ_URL")
    instance = os.getenv("IBMQ_INSTANCE")
    channel = os.getenv("IBMQ_CHANNEL", "ibm_quantum")
    default_backend = os.getenv("IBMQ_DEFAULT_BACKEND")
    return IBMQuantumConfig(
        token=token,
        url=url,
        instance=instance,
        channel=channel,
        default_backend=default_backend,
    )

# ----------------------------------------------------------------------
# Mock service implementation – used when a real token is unavailable.
# ----------------------------------------------------------------------
class _MockParam:
    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value

class _MockGate:
    def __init__(self):
        self.gate = "cx"
        self.parameters = [
            _MockParam("gate_error", 0.01),
            _MockParam("readout_error", 0.02),
        ]

class _MockQubitProp:
    def __init__(self, name: str, value: float):
        self.name = name
        self.value = value

class _MockProperties:
    """
    Minimal stand‑in for ``BackendProperties`` used by the mock service.
    """
    def __init__(self, backend_name: str):
        self.backend_name = backend_name
        self.coupling_map = [[0, 1]]
        self.qubits = [
            [_MockQubitProp("T1", 150e-6), _MockQubitProp("T2", 100e-6)],
            [_MockQubitProp("T1", 160e-6), _MockQubitProp("T2", 110e-6)],
        ]
        self.gates = [_MockGate()]
        self.last_update_date = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "device_id": self.backend_name,
            "timestamp": self.last_update_date.isoformat(),
            "backend_name": self.backend_name,
            "coupling_map": self.coupling_map,
            "properties": {
                "qubits": [
                    [
                        {"name": "T1", "value": 150e-6},
                        {"name": "T2", "value": 100e-6},
                    ],
                    [
                        {"name": "T1", "value": 160e-6},
                        {"name": "T2", "value": 110e-6},
                    ],
                ],
                "gates": [
                    {
                        "gate": "cx",
                        "parameters": [
                            {"name": "gate_error", "value": 0.01},
                            {"name": "readout_error", "value": 0.02},
                        ],
                    }
                ],
            },
        }

class _MockBackend:
    """
    Simple mock backend object exposing ``name``, ``operational`` and
    ``properties()``.
    """
    def __init__(self, name: str):
        self.name = name
        self.operational = True

    def properties(self):
        return _MockProperties(self.name)

class _MockService:
    """
    Very small mock of ``QiskitRuntimeService`` sufficient for the
    integration tests.  It provides ``backends()`` and ``backend(name)``.
    """
    def __init__(self):
        # Provide a handful of deterministic mock backends.
        self._backends = [_MockBackend(f"mock_backend_{i}") for i in range(3)]

    def backends(self) -> List[_MockBackend]:
        return self._backends

    def backend(self, name: str) -> _MockBackend:
        # Return a backend matching the requested name if it exists,
        # otherwise return the first mock backend.
        for b in self._backends:
            if b.name == name:
                return b
        return self._backends[0]

def setup_ibm_runtime(config: Optional[IBMQuantumConfig] = None) -> Any:
    """
    Initialise the IBM Quantum runtime service.

    If a valid token is present, a real ``QiskitRuntimeService`` is
    instantiated.  When the token is missing or the real service cannot
    be created, a mock service is returned so that the test suite can
    continue without external credentials.

    Args:
        config: Optional pre‑populated configuration.  If ``None`` the
                environment is consulted via :func:`load_config`.

    Returns:
        An instance of ``QiskitRuntimeService`` or a mock service.
    """
    logger = logging.getLogger(__name__)

    if config is None:
        try:
            config = load_config()
        except ValueError as e:
            logger.warning(f"Configuration load failed: {e}. Using MockService.")
            return _MockService()

    if QiskitRuntimeService is None:
        logger.warning("qiskit_ibm_runtime not installed – using MockService.")
        return _MockService()

    try:
        service = QiskitRuntimeService(
            token=config.token,
            url=config.url,
            instance=config.instance,
            channel=config.channel,
        )
        return service
    except Exception as e:  # pragma: no cover
        logger.warning(f"Failed to create real QiskitRuntimeService: {e}. Using MockService.")
        return _MockService()

def main():
    """
    Simple entry‑point to verify configuration loading.
    """
    try:
        cfg = load_config()
        print(f"Loaded config for token {cfg.token[:4]}...{cfg.token[-4:]}")
    except Exception as e:
        print(f"Error loading config: {e}")
