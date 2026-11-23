"""
Unit tests for the kernel blockers module.
Verifies that RestrictedActionError is raised for blocked libraries.
"""
import pytest
from code.kernel.blockers import RestrictedActionError, check_library_policy, BLOCKED_LIBRARIES

class TestRestrictedActionError:
    """Tests for the RestrictedActionError exception class."""

    def test_exception_instantiation(self):
        """Test that RestrictedActionError can be instantiated with standard args."""
        exc = RestrictedActionError("Test message")
        assert str(exc) == "Test message"
        assert exc.library_name is None
        assert exc.action is None

    def test_exception_with_details(self):
        """Test instantiation with library name and action."""
        exc = RestrictedActionError(
            "Access denied",
            library_name="trimesh",
            action="import"
        )
        assert exc.library_name == "trimesh"
        assert exc.action == "import"

class TestCheckLibraryPolicy:
    """Tests for the check_library_policy function."""

    def test_blocked_trimesh_raises(self):
        """Verify importing 'trimesh' raises RestrictedActionError."""
        with pytest.raises(RestrictedActionError) as exc_info:
            check_library_policy("trimesh")

        assert exc_info.value.library_name == "trimesh"
        assert "blocked 3D library" in str(exc_info.value).lower()

    def test_blocked_pytorch3d_raises(self):
        """Verify importing 'pytorch3d' raises RestrictedActionError."""
        with pytest.raises(RestrictedActionError) as exc_info:
            check_library_policy("pytorch3d")

        assert exc_info.value.library_name == "pytorch3d"
        assert "blocked 3D library" in str(exc_info.value).lower()

    def test_blocked_open3d_raises(self):
        """Verify importing 'open3d' raises RestrictedActionError."""
        with pytest.raises(RestrictedActionError) as exc_info:
            check_library_policy("open3d")

        assert exc_info.value.library_name == "open3d"
        assert "blocked 3D library" in str(exc_info.value).lower()

    def test_allowed_shapely_passes(self):
        """Verify 'shapely' does not raise an error."""
        # Should not raise
        check_library_policy("shapely")

    def test_allowed_numpy_passes(self):
        """Verify 'numpy' does not raise an error."""
        # Should not raise
        check_library_policy("numpy")

    def test_unknown_library_passes_currently(self):
        """
        Verify that libraries not explicitly blocked do NOT raise an error
        under the current 'blocklist' policy.
        """
        # Current implementation only blocks explicit blacklist
        # Future: If whitelist mode is enabled, this should raise
        check_library_policy("unknown_lib_xyz")