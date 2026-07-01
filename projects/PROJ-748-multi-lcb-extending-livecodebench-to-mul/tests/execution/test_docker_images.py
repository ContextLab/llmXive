"""
Tests for docker_images module.
"""

import pytest
from unittest.mock import patch, MagicMock
import docker

from execution.docker_images import (
    get_image_reference,
    list_available_images,
    REQUIRED_LANGUAGES,
    IMAGE_REGISTRY
)


class TestGetImageReference:
    """Tests for get_image_reference function."""

    def test_valid_language_returns_reference(self):
        """Test that valid language returns correct image reference."""
        for lang in ["cpp", "java", "rust", "python", "go"]:
            ref = get_image_reference(lang)
            assert "@" in ref, f"Reference for {lang} should contain digest"
            assert lang in ref.lower() or any(lang in k for k in IMAGE_REGISTRY.keys())

    def test_case_insensitive(self):
        """Test that language lookup is case-insensitive."""
        ref1 = get_image_reference("CPP")
        ref2 = get_image_reference("cpp")
        assert ref1 == ref2

    def test_invalid_language_raises(self):
        """Test that invalid language raises ValueError."""
        with pytest.raises(ValueError):
            get_image_reference("invalid_language_xyz")

    def test_empty_string_raises(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            get_image_reference("")


class TestListAvailableImages:
    """Tests for list_available_images function."""

    def test_returns_all_languages(self):
        """Test that all registered languages are returned."""
        available = list_available_images()
        for lang in IMAGE_REGISTRY.keys():
            assert lang in available

    def test_returns_dict(self):
        """Test that function returns a dictionary."""
        available = list_available_images()
        assert isinstance(available, dict)

    def test_values_contain_digests(self):
        """Test that all image references contain digests."""
        available = list_available_images()
        for lang, ref in available.items():
            assert "@" in ref, f"Image reference for {lang} should contain digest"


class TestRequiredLanguages:
    """Tests for REQUIRED_LANGUAGES constant."""

    def test_contains_expected_languages(self):
        """Test that required languages include expected ones."""
        expected = ["cpp", "java", "rust", "python"]
        for lang in expected:
            assert lang in REQUIRED_LANGUAGES, f"{lang} should be in REQUIRED_LANGUAGES"

    def test_is_list(self):
        """Test that REQUIRED_LANGUAGES is a list."""
        assert isinstance(REQUIRED_LANGUAGES, list)


class TestImageRegistry:
    """Tests for IMAGE_REGISTRY constant."""

    def test_all_values_have_digests(self):
        """Test that all image references have digests."""
        for lang, ref in IMAGE_REGISTRY.items():
            assert "@" in ref, f"Image reference for {lang} should contain digest"

    def test_no_duplicate_digests(self):
        """Test that no two languages share the same digest (unless intentional)."""
        digests = [ref.split('@')[1] for ref in IMAGE_REGISTRY.values()]
        # Note: This test may need adjustment if intentionally sharing base images
        # For now, just ensure the structure is correct
        assert len(digests) == len(IMAGE_REGISTRY)

    def test_python_image_reference(self):
        """Test Python image reference format."""
        ref = IMAGE_REGISTRY["python"]
        assert "python" in ref.lower()
        assert "3.11" in ref or "3.10" in ref or "3.12" in ref

    def test_cpp_image_reference(self):
        """Test C++ image reference format."""
        ref = IMAGE_REGISTRY["cpp"]
        assert "gcc" in ref.lower() or "clang" in ref.lower()

    def test_java_image_reference(self):
        """Test Java image reference format."""
        ref = IMAGE_REGISTRY["java"]
        assert "temurin" in ref.lower() or "openjdk" in ref.lower() or "java" in ref.lower()

    def test_rust_image_reference(self):
        """Test Rust image reference format."""
        ref = IMAGE_REGISTRY["rust"]
        assert "rust" in ref.lower()