"""
Contract test for topology schema (US1).

Validates that the topology extraction output CSV conforms to the expected schema:
- Columns: atom_id, coord_num, angle_var, is_valid
- Data types: int, int, float, bool (or string representation)
- Physical constraints: coord_num >= 0, angle_var >= 0, is_valid in {True, False}

This test validates against the schema defined in the Spec (US-1),
not the implementation code. It ensures the output format is correct
for downstream consumption.
"""
import os
import sys
import csv
import pytest
from pathlib import Path

# Add project root to path if running directly
if "code" not in sys.path[0]:
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root / "code"))

from src.lib.utils import FatalError

# Expected schema definition
EXPECTED_COLUMNS = ["atom_id", "coord_num", "angle_var", "is_valid"]
REQUIRED_COLUMNS = ["atom_id", "coord_num", "angle_var", "is_valid"]
OPTIONAL_COLUMNS = []

# Physical constraints
MIN_COORDINATION = 0
MAX_COORDINATION = 12  # Reasonable upper bound for amorphous silicon
MIN_ANGLE_VAR = 0.0


def validate_schema(csv_path: Path) -> None:
    """
    Validate the topology CSV schema against the contract.
    
    Args:
        csv_path: Path to the topology CSV file
        
    Raises:
        FatalError: If schema validation fails
    """
    if not csv_path.exists():
        raise FatalError(f"Topology CSV file not found: {csv_path}")
    
    if csv_path.stat().st_size == 0:
        raise FatalError(f"Topology CSV file is empty: {csv_path}")
    
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Check header columns
        actual_columns = reader.fieldnames
        if actual_columns is None:
            raise FatalError(f"Topology CSV has no header: {csv_path}")
        
        # Verify required columns are present
        missing_required = set(REQUIRED_COLUMNS) - set(actual_columns)
        if missing_required:
            raise FatalError(
                f"Missing required columns in {csv_path}: {missing_required}"
            )
        
        # Check for unexpected columns (optional columns are allowed)
        unexpected = set(actual_columns) - set(REQUIRED_COLUMNS) - set(OPTIONAL_COLUMNS)
        if unexpected:
            raise FatalError(
                f"Unexpected columns in {csv_path}: {unexpected}. "
                f"Expected only: {REQUIRED_COLUMNS + OPTIONAL_COLUMNS}"
            )
        
        # Validate data types and constraints for each row
        row_count = 0
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1-indexed, header is row 1)
            row_count += 1
            
            # Validate atom_id (integer)
            try:
                atom_id = int(row["atom_id"])
                if atom_id < 0:
                    raise FatalError(
                        f"Invalid atom_id at row {row_num}: {atom_id}. Must be non-negative."
                    )
            except ValueError:
                raise FatalError(
                    f"Invalid atom_id at row {row_num}: {row['atom_id']}. Must be integer."
                )
            
            # Validate coord_num (integer)
            try:
                coord_num = int(row["coord_num"])
                if coord_num < MIN_COORDINATION:
                    raise FatalError(
                        f"Invalid coord_num at row {row_num}: {coord_num}. "
                        f"Must be >= {MIN_COORDINATION}."
                    )
                if coord_num > MAX_COORDINATION:
                    raise FatalError(
                        f"Coordination number exceeds physical limit at row {row_num}: {coord_num}. "
                        f"Maximum allowed: {MAX_COORDINATION}. "
                        f"Consider flagging as anomaly rather than halting."
                    )
            except ValueError:
                raise FatalError(
                    f"Invalid coord_num at row {row_num}: {row['coord_num']}. Must be integer."
                )
            
            # Validate angle_var (float)
            try:
                angle_var = float(row["angle_var"])
                if angle_var < MIN_ANGLE_VAR:
                    raise FatalError(
                        f"Invalid angle_var at row {row_num}: {angle_var}. "
                        f"Must be >= {MIN_ANGLE_VAR}."
                    )
            except ValueError:
                raise FatalError(
                    f"Invalid angle_var at row {row_num}: {row['angle_var']}. Must be numeric."
                )
            
            # Validate is_valid (boolean or string representation)
            is_valid_str = row["is_valid"].strip().lower()
            if is_valid_str in ("true", "1", "yes"):
                is_valid = True
            elif is_valid_str in ("false", "0", "no"):
                is_valid = False
            else:
                raise FatalError(
                    f"Invalid is_valid at row {row_num}: {row['is_valid']}. "
                    f"Must be boolean or 'true'/'false'."
                )
        
        if row_count == 0:
            raise FatalError(
                f"Topology CSV has no data rows: {csv_path}. "
                f"Expected at least one atom record."
            )


@pytest.fixture
def sample_topology_csv(tmp_path: Path):
    """Create a sample valid topology CSV for testing."""
    csv_path = tmp_path / "sample_topology.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        writer.writerows([
            {"atom_id": "0", "coord_num": "4", "angle_var": "0.123", "is_valid": "true"},
            {"atom_id": "1", "coord_num": "4", "angle_var": "0.456", "is_valid": "true"},
            {"atom_id": "2", "coord_num": "3", "angle_var": "0.789", "is_valid": "false"},
            {"atom_id": "3", "coord_num": "5", "angle_var": "0.234", "is_valid": "true"},
        ])
    return csv_path


@pytest.fixture
def invalid_columns_csv(tmp_path: Path):
    """Create a topology CSV with missing required columns."""
    csv_path = tmp_path / "invalid_columns.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["atom_id", "coord_num"])  # Missing angle_var, is_valid
        writer.writeheader()
        writer.writerow({"atom_id": "0", "coord_num": "4"})
    return csv_path


@pytest.fixture
def invalid_types_csv(tmp_path: Path):
    """Create a topology CSV with invalid data types."""
    csv_path = tmp_path / "invalid_types.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        writer.writerow({
            "atom_id": "abc",  # Not an integer
            "coord_num": "4",
            "angle_var": "0.123",
            "is_valid": "true"
        })
    return csv_path


@pytest.fixture
def invalid_constraints_csv(tmp_path: Path):
    """Create a topology CSV with values violating physical constraints."""
    csv_path = tmp_path / "invalid_constraints.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        writer.writerow({
            "atom_id": "0",
            "coord_num": "-1",  # Negative coordination
            "angle_var": "0.123",
            "is_valid": "true"
        })
    return csv_path


@pytest.fixture
def empty_csv(tmp_path: Path):
    """Create an empty topology CSV."""
    csv_path = tmp_path / "empty.csv"
    csv_path.touch()
    return csv_path


@pytest.fixture
def header_only_csv(tmp_path: Path):
    """Create a topology CSV with only header, no data."""
    csv_path = tmp_path / "header_only.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
    return csv_path


class TestTopologySchemaContract:
    """Contract tests for topology schema validation."""

    def test_valid_schema(self, sample_topology_csv):
        """Test that a valid topology CSV passes schema validation."""
        validate_schema(sample_topology_csv)

    def test_missing_required_columns(self, invalid_columns_csv):
        """Test that missing required columns raise FatalError."""
        with pytest.raises(FatalError) as exc_info:
            validate_schema(invalid_columns_csv)
        assert "Missing required columns" in str(exc_info.value)

    def test_invalid_atom_id_type(self, invalid_types_csv):
        """Test that non-integer atom_id raises FatalError."""
        with pytest.raises(FatalError) as exc_info:
            validate_schema(invalid_types_csv)
        assert "Invalid atom_id" in str(exc_info.value)

    def test_negative_coordination(self, invalid_constraints_csv):
        """Test that negative coordination number raises FatalError."""
        with pytest.raises(FatalError) as exc_info:
            validate_schema(invalid_constraints_csv)
        assert "Invalid coord_num" in str(exc_info.value)

    def test_empty_file(self, empty_csv):
        """Test that empty file raises FatalError."""
        with pytest.raises(FatalError) as exc_info:
            validate_schema(empty_csv)
        assert "empty" in str(exc_info.value).lower()

    def test_header_only(self, header_only_csv):
        """Test that file with only header raises FatalError."""
        with pytest.raises(FatalError) as exc_info:
            validate_schema(header_only_csv)
        assert "no data rows" in str(exc_info.value).lower()

    def test_file_not_found(self, tmp_path: Path):
        """Test that missing file raises FatalError."""
        non_existent = tmp_path / "non_existent.csv"
        with pytest.raises(FatalError) as exc_info:
            validate_schema(non_existent)
        assert "not found" in str(exc_info.value).lower()

    def test_boolean_is_valid_values(self, tmp_path: Path):
        """Test various boolean representations for is_valid."""
        csv_path = tmp_path / "bool_test.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
            writer.writeheader()
            writer.writerows([
                {"atom_id": "0", "coord_num": "4", "angle_var": "0.1", "is_valid": "true"},
                {"atom_id": "1", "coord_num": "4", "angle_var": "0.1", "is_valid": "false"},
                {"atom_id": "2", "coord_num": "4", "angle_var": "0.1", "is_valid": "True"},
                {"atom_id": "3", "coord_num": "4", "angle_var": "0.1", "is_valid": "False"},
                {"atom_id": "4", "coord_num": "4", "angle_var": "0.1", "is_valid": "1"},
                {"atom_id": "5", "coord_num": "4", "angle_var": "0.1", "is_valid": "0"},
            ])
        validate_schema(csv_path)

    def test_invalid_is_valid_value(self, tmp_path: Path):
        """Test that invalid is_valid value raises FatalError."""
        csv_path = tmp_path / "invalid_bool.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                "atom_id": "0",
                "coord_num": "4",
                "angle_var": "0.1",
                "is_valid": "maybe"
            })
        with pytest.raises(FatalError) as exc_info:
            validate_schema(csv_path)
        assert "Invalid is_valid" in str(exc_info.value)

    def test_negative_angle_var(self, tmp_path: Path):
        """Test that negative angle_var raises FatalError."""
        csv_path = tmp_path / "negative_angle.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                "atom_id": "0",
                "coord_num": "4",
                "angle_var": "-0.1",
                "is_valid": "true"
            })
        with pytest.raises(FatalError) as exc_info:
            validate_schema(csv_path)
        assert "Invalid angle_var" in str(exc_info.value)

    def test_high_coordination_flagging(self, tmp_path: Path):
        """Test that high coordination numbers are detected (but not necessarily halted)."""
        csv_path = tmp_path / "high_coord.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
            writer.writeheader()
            # Coordination 7 is above typical a-Si but below MAX_COORDINATION
            writer.writerow({
                "atom_id": "0",
                "coord_num": "7",
                "angle_var": "0.1",
                "is_valid": "false"  # Should be flagged as invalid
            })
        # This should pass validation but the is_valid flag should be false
        validate_schema(csv_path)