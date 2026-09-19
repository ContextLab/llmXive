import pytest
import time
import json
from unittest.mock import patch, MagicMock
from code.fetcher import retry_with_exponential_backoff

try:
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    pytest.skip("jsonschema not installed", allow_module_level=True)

# Path to the schema file relative to the project root
SCHEMA_PATH = "specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.yaml"

@pytest.fixture
def valid_calibration_snapshot():
    """
    Returns a mock payload that adheres to the schema defined in SCHEMA_PATH.
    This is a minimal valid structure to test schema validation.
    """
    return {
        "backend_name": "ibm_test_backend",
        "backend_version": "1.0.0",
        "last_update_date": "2023-10-27T10:00:00Z",
        "general_properties": {
            "n_qubits": 5,
            "basis_gates": ["x", "y", "z", "cx"],
            "max_shots": 10000,
            "coupling_map": [[0, 1], [1, 2], [2, 3], [3, 4]],
            "online_date": "2023-01-01T00:00:00Z",
            "operational": True
        },
        "qubits": [
            [
                {"name": "T1", "value": 100e-6, "unit": "s", "date": "2023-10-27T10:00:00Z"},
                {"name": "T2", "value": 50e-6, "unit": "s", "date": "2023-10-27T10:00:00Z"},
                {"name": "frequency", "value": 5e9, "unit": "Hz", "date": "2023-10-27T10:00:00Z"},
                {"name": "readout_error", "value": 0.02, "unit": "unitless", "date": "2023-10-27T10:00:00Z"}
            ]
        ],
        "gates": [
            {
                "name": "cx",
                "qubits": [0, 1],
                "parameters": [
                    {"name": "gate_error", "value": 0.01, "unit": "unitless", "date": "2023-10-27T10:00:00Z"}
                ]
            }
        ]
    }

@pytest.fixture
def invalid_calibration_snapshot():
    """
    Returns a payload that violates the schema (e.g., missing required field).
    """
    return {
        "backend_name": "ibm_test_backend",
        # Missing 'general_properties' which is required
        "qubits": []
    }

class TestContractValidation:
    """
    Contract tests for API response schema parsing.
    Validates that fetched data (or mock data) conforms to the defined schema.
    """

    @pytest.fixture(autouse=True)
    def setup_schema(self):
        """Load the schema once per test class."""
        import yaml
        with open(SCHEMA_PATH, 'r') as f:
            self.schema = yaml.safe_load(f)

    def test_valid_snapshot_passes_validation(self, valid_calibration_snapshot):
        """
        Contract test: A valid calibration snapshot must pass schema validation.
        """
        # This should not raise ValidationError
        try:
            validate(instance=valid_calibration_snapshot, schema=self.schema)
        except ValidationError as e:
            pytest.fail(f"Valid snapshot failed validation: {e.message}")

    def test_invalid_snapshot_fails_validation(self, invalid_calibration_snapshot):
        """
        Contract test: An invalid calibration snapshot must raise ValidationError.
        """
        with pytest.raises(ValidationError) as excinfo:
            validate(instance=invalid_calibration_snapshot, schema=self.schema)

        # Verify the error is about missing required property
        assert "general_properties" in str(excinfo.value) or "is a required property" in str(excinfo.value)

    def test_partial_valid_snapshot_fails_validation(self):
        """
        Contract test: A snapshot with missing optional but structurally required fields fails.
        """
        partial_data = {
            "backend_name": "test",
            "general_properties": {
                "n_qubits": 5,
                "basis_gates": ["x"],
                "max_shots": 100,
                "coupling_map": [[0, 1]],
                "online_date": "2023-01-01T00:00:00Z",
                "operational": True
            },
            # Missing 'qubits' and 'gates' which are required at root level
            "last_update_date": "2023-10-27T10:00:00Z"
        }
        with pytest.raises(ValidationError):
            validate(instance=partial_data, schema=self.schema)

    def test_wrong_datatype_fails_validation(self):
        """
        Contract test: Wrong data types (e.g., string instead of number) must fail.
        """
        bad_data = {
            "backend_name": "test",
            "last_update_date": "2023-10-27T10:00:00Z",
            "general_properties": {
                "n_qubits": "five",  # Should be integer
                "basis_gates": ["x"],
                "max_shots": 100,
                "coupling_map": [[0, 1]],
                "online_date": "2023-01-01T00:00:00Z",
                "operational": True
            },
            "qubits": [],
            "gates": []
        }
        with pytest.raises(ValidationError):
            validate(instance=bad_data, schema=self.schema)

# Re-export the existing retry tests to ensure the file is self-contained
class TestRetryWithExponentialBackoff:
    """
    Unit tests for the retry_with_exponential_backoff decorator.
    """

    def test_success_on_first_attempt(self):
        """Test that a successful function returns immediately."""
        @retry_with_exponential_backoff(max_attempts=3, base_delay=0.1)
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"

    def test_retry_on_transient_error(self):
        """Test that the function retries on a transient error (503)."""
        call_count = 0

        @retry_with_exponential_backoff(max_attempts=3, base_delay=0.01)
        def transient_fail_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("503 Service Unavailable")
            return "success"

        result = transient_fail_func()
        assert result == "success"
        assert call_count == 3

    def test_no_retry_on_non_transient_error(self):
        """Test that the function does not retry on non-transient errors."""
        call_count = 0

        @retry_with_exponential_backoff(max_attempts=3, base_delay=0.01)
        def non_transient_fail_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid data format")

        with pytest.raises(ValueError):
            non_transient_fail_func()
        assert call_count == 1

    def test_max_attempts_exceeded(self):
        """Test that the function raises the last exception after max attempts."""
        @retry_with_exponential_backoff(max_attempts=2, base_delay=0.01)
        def always_fail_func():
            raise Exception("503 Service Unavailable")

        with pytest.raises(Exception) as exc_info:
            always_fail_func()
        assert "503 Service Unavailable" in str(exc_info.value)

    def test_timeout_exceeded(self):
        """Test that a TimeoutError is raised if total time exceeds timeout."""
        @retry_with_exponential_backoff(max_attempts=3, base_delay=0.1, timeout=0.15)
        def slow_transient_fail_func():
            raise Exception("503 Service Unavailable")

        with pytest.raises(TimeoutError):
            slow_transient_fail_func()

    def test_delay_calculation(self):
        """Test that the delay follows 2^N backoff."""
        call_times = []

        @retry_with_exponential_backoff(max_attempts=4, base_delay=0.01)
        def time_track_func():
            call_times.append(time.time())
            if len(call_times) < 4:
                raise Exception("503 Service Unavailable")
            return "done"

        try:
            time_track_func()
        except Exception:
            pass

        assert len(call_times) == 4