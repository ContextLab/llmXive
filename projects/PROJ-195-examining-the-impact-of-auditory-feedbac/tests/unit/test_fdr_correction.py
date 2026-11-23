import os
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import nibabel as nib
from scipy import stats

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from glm_fdr_correction import apply_fdr_correction, extract_clusters, save_thresholded_map, save_cluster_metadata

class TestFDRCorrection(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Create a mock 3D t-map with known properties
        self.shape = (10, 10, 10)
        self.t_data = np.zeros(self.shape)
        
        # Inject some significant t-values in a cluster
        # T-values around 2.5-3.0 with large DOF are significant
        self.t_data[4:7, 4:7, 4:7] = 3.5
        # Inject some noise
        self.t_data[0:2, 0:2, 0:2] = 1.0
        
        # Create a mock affine
        self.affine = np.eye(4)
        self.img = nib.Nifti1Image(self.t_data, self.affine)
        
    def test_apply_fdr_correction_significant_cluster(self):
        """Test that FDR correctly identifies a cluster of high t-values."""
        # With a dense cluster of 3.5, FDR should pick it up
        mask = apply_fdr_correction(self.t_data, q=0.05)
        
        # The cluster at 4:7, 4:7, 4:7 should be significant
        # Check if the center of the cluster is masked
        self.assertTrue(mask[5, 5, 5], "Center of high t-value cluster should be significant")
        
        # Check if noise area is NOT significant
        self.assertFalse(mask[1, 1, 1], "Low t-value noise should not be significant")
        
    def test_apply_fdr_correction_empty_map(self):
        """Test FDR on a map with no significant values."""
        zero_data = np.zeros(self.shape)
        mask = apply_fdr_correction(zero_data, q=0.05)
        self.assertFalse(np.any(mask), "Empty map should yield no significant voxels")
        
    def test_extract_clusters(self):
        """Test cluster extraction logic."""
        # Create a mask with two separate blobs
        mask_data = np.zeros(self.shape, dtype=bool)
        mask_data[2:4, 2:4, 2:4] = True
        mask_data[6:8, 6:8, 6:8] = True
        
        clusters = extract_clusters(mask_data, self.affine, self.shape)
        
        self.assertEqual(len(clusters), 2, "Should detect 2 separate clusters")
        
        # Check cluster properties
        for cluster in clusters:
            self.assertIn("cluster_id", cluster)
            self.assertIn("size_voxels", cluster)
            self.assertIn("centroid_mni", cluster)
            self.assertGreater(cluster["size_voxels"], 0)
            
    def test_save_thresholded_map(self):
        """Test saving the mask to disk."""
        mask_data = np.zeros(self.shape, dtype=bool)
        mask_data[5, 5, 5] = True
        
        output_path = Path(self.test_dir) / "test_mask.nii.gz"
        save_thresholded_map(mask_data, self.img, output_path)
        
        self.assertTrue(output_path.exists(), "Output mask file should exist")
        
        # Verify contents
        loaded_img = nib.load(output_path)
        loaded_data = loaded_img.get_fdata()
        self.assertTrue(loaded_data[5, 5, 5] > 0, "Saved mask should contain the voxel")
        
    def test_save_cluster_metadata(self):
        """Test saving cluster metadata to CSV."""
        clusters = [
            {
                "cluster_id": 1,
                "size_voxels": 10,
                "centroid_mni": [10.0, 20.0, 30.0],
                "description": "Test Cluster"
            }
        ]
        
        output_path = Path(self.test_dir) / "test_clusters.csv"
        save_cluster_metadata(clusters, output_path)
        
        self.assertTrue(output_path.exists(), "Output CSV should exist")
        
        with open(output_path, 'r') as f:
            content = f.read()
            self.assertIn("cluster_id", content)
            self.assertIn("10", content)

if __name__ == '__main__':
    unittest.main()