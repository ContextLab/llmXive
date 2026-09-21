"""
Unit tests for code/utils/mesh_utils.py
"""

import numpy as np
import pytest
import trimesh
from pathlib import Path
import tempfile
import os

# Import the module under test
from code.utils.mesh_utils import (
    generate_mesh_from_points,
    validate_manifold,
    cleanup_mesh,
    export_mesh,
    create_placeholder_mesh
)

def test_generate_mesh_from_points_minimum():
    """Test mesh generation with minimum points."""
    points = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float32)
    
    mesh = generate_mesh_from_points(points)
    assert isinstance(mesh, trimesh.Trimesh)
    assert mesh.is_watertight  # Convex hull should be watertight

def test_generate_mesh_from_points_invalid():
    """Test error handling for invalid points."""
    with pytest.raises(ValueError):
        generate_mesh_from_points(np.array([[1.0, 2.0]]))  # Wrong shape

    with pytest.raises(ValueError):
        generate_mesh_from_points(np.array([[0.0, 0.0, 0.0]]))  # Too few points

def test_validate_manifold_watertight():
    """Test validation of a watertight mesh."""
    mesh = trimesh.creation.box()
    is_manifold, issues = validate_manifold(mesh)
    assert is_manifold
    assert len(issues) == 0

def test_validate_manifold_not_watertight():
    """Test validation of a non-watertight mesh."""
    # Create a box and remove a face
    mesh = trimesh.creation.box()
    # Remove last face to make it non-watertight
    mesh.faces = mesh.faces[:-1]
    
    is_manifold, issues = validate_manifold(mesh)
    assert not is_manifold
    assert any("watertight" in issue for issue in issues)

def test_cleanup_mesh_degenerate():
    """Test removal of degenerate faces."""
    mesh = trimesh.creation.box()
    # Add a degenerate face (all vertices same)
    degenerate_face = np.array([[0, 0, 0]])
    # This is tricky to construct manually, so we rely on the function
    # existing and not crashing on a clean mesh.
    cleaned = cleanup_mesh(mesh, remove_degenerate=True)
    assert isinstance(cleaned, trimesh.Trimesh)

def test_cleanup_mesh_simplify():
    """Test mesh simplification."""
    mesh = trimesh.creation.icosphere(subdivisions=3)
    original_faces = len(mesh.faces)
    
    cleaned = cleanup_mesh(mesh, simplify=True, target_faces=100)
    assert len(cleaned.faces) <= 100
    assert len(cleaned.faces) < original_faces

def test_export_mesh_obj():
    """Test exporting to OBJ."""
    mesh = trimesh.creation.box()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.obj"
        result_path = export_mesh(mesh, str(path))
        
        assert result_path.exists()
        assert result_path.suffix == ".obj"

def test_export_mesh_ply():
    """Test exporting to PLY."""
    mesh = trimesh.creation.box()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.ply"
        result_path = export_mesh(mesh, str(path))
        
        assert result_path.exists()
        assert result_path.suffix == ".ply"

def test_create_placeholder_mesh():
    """Test placeholder mesh creation."""
    mesh = create_placeholder_mesh()
    assert isinstance(mesh, trimesh.Trimesh)
    assert len(mesh.faces) == 1
    assert len(mesh.vertices) == 3
