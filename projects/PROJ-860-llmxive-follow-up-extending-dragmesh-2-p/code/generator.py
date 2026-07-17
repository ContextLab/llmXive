"""
Novel Object Set Generator for Virtual Tactile Adaptation.

Generates articulated geometries with randomized friction coefficients.
Optimized for low memory usage by streaming generation and avoiding
large in-memory data structures.
"""
import os
import math
import random
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from seed_config import set_seeds
import logging

# Configure logger
logger = logging.getLogger(__name__)

class NovelObjectSet:
    """
    Generator class for producing a set of randomized articulated geometries.
    
    Optimized for memory efficiency:
    - Generates objects one-by-one and writes immediately to disk
    - Uses streaming parameters instead of pre-computing large arrays
    - Minimizes intermediate object retention
    """
    
    def __init__(self, output_dir: str, seed: Optional[int] = None):
        """
        Initialize the generator.
        
        Args:
            output_dir: Directory to save generated geometry files
            seed: Random seed for reproducibility (optional)
        """
        self.output_dir = output_dir
        self.seed = seed
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        if seed is not None:
            set_seeds(seed)
            logger.info(f"Generator initialized with seed: {seed}")
        
        # Friction range configuration (FR-003)
        self.friction_min = 0.1
        self.friction_max = 1.5
        
        # Geometry parameters
        self.base_size_range = (0.05, 0.15)  # meters
        self.arm_length_range = (0.1, 0.3)   # meters
        self.joint_count_range = (1, 5)      # number of joints
        
        # Memory optimization: batch size for logging
        self.log_batch_size = 10

    def _generate_single_object(self, object_id: int) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a single articulated object URDF and metadata.
        
        Memory-optimized: creates minimal intermediate structures.
        
        Args:
            object_id: Unique identifier for the object
            
        Returns:
            Tuple of (file_path, metadata_dict)
        """
        # Randomize parameters for this object
        friction = random.uniform(self.friction_min, self.friction_max)
        base_size = random.uniform(*self.base_size_range)
        arm_length = random.uniform(*self.arm_length_range)
        joint_count = random.randint(*self.joint_count_range)
        
        # Create URDF structure
        root = ET.Element("robot", name=f"object_{object_id}")
        
        # Base link
        base_link = ET.SubElement(root, "link", name="base")
        inertial = ET.SubElement(base_link, "inertial")
        ET.SubElement(inertial, "mass", value="1.0")
        ET.SubElement(inertial, "inertia", ixx="0.01", ixy="0.0", ixz="0.0", iyy="0.01", iyz="0.0", izz="0.01")
        
        visual = ET.SubElement(base_link, "visual")
        ET.SubElement(visual, "geometry").set("type", "box")
        ET.SubElement(visual, "size", value=f"{base_size} {base_size} {base_size/2}")
        
        collision = ET.SubElement(base_link, "collision")
        ET.SubElement(collision, "geometry").set("type", "box")
        ET.SubElement(collision, "size", value=f"{base_size} {base_size} {base_size/2}")
        
        # Joint material (friction)
        material = ET.SubElement(base_link, "material", name=f"friction_{friction:.3f}")
        ET.SubElement(material, "color", rgba=f"1.0 0.5 0.0 1.0")
        
        # Generate articulated arms
        prev_link = "base"
        for i in range(joint_count):
            joint_name = f"joint_{i}"
            link_name = f"link_{i}"
            
            # Joint
            joint = ET.SubElement(root, "joint", name=joint_name, type="continuous")
            ET.SubElement(joint, "parent", link=prev_link)
            ET.SubElement(joint, "child", link=link_name)
            ET.SubElement(joint, "axis", xyz="0 0 1")
            ET.SubElement(joint, "limit", effort="100", velocity="10")
            
            # Material for joint (friction)
            joint_material = ET.SubElement(joint, "material", name=f"joint_friction_{friction:.3f}")
            
            # Link
            link = ET.SubElement(root, "link", name=link_name)
            inertial = ET.SubElement(link, "inertial")
            ET.SubElement(inertial, "mass", value="0.5")
            ET.SubElement(inertial, "inertia", ixx="0.005", ixy="0.0", ixz="0.0", iyy="0.005", iyz="0.0", izz="0.005")
            
            visual = ET.SubElement(link, "visual")
            ET.SubElement(visual, "geometry").set("type", "box")
            ET.SubElement(visual, "size", value=f"{base_size/2} {base_size/2} {arm_length}")
            
            collision = ET.SubElement(link, "collision")
            ET.SubElement(collision, "geometry").set("type", "box")
            ET.SubElement(collision, "size", value=f"{base_size/2} {base_size/2} {arm_length}")
            
            # Offset for next joint
            offset = ET.SubElement(joint, "origin", xyz=f"0 0 {arm_length/2}")
            
            prev_link = link_name
        
        # Write URDF to file
        filename = f"object_{object_id:04d}.urdf"
        filepath = os.path.join(self.output_dir, filename)
        
        tree = ET.ElementTree(root)
        # Use short formatting to reduce memory footprint during write
        ET.indent(tree, space="  ", level=0)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)
        
        # Create metadata (minimal in-memory footprint)
        metadata = {
            "object_id": object_id,
            "filename": filename,
            "friction": friction,
            "base_size": base_size,
            "arm_length": arm_length,
            "joint_count": joint_count
        }
        
        return filepath, metadata

    def generate_set(self, count: int, metadata_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate a set of novel objects and optionally save metadata.
        
        Memory-optimized: streams generation, writes immediately,
        only retains minimal metadata for return.
        
        Args:
            count: Number of objects to generate
            metadata_file: Optional path to save metadata JSON
            
        Returns:
            List of metadata dictionaries for generated objects
        """
        logger.info(f"Generating {count} novel objects in {self.output_dir}")
        
        all_metadata = []
        
        for i in range(count):
            filepath, metadata = self._generate_single_object(i)
            all_metadata.append(metadata)
            
            # Log progress in batches to avoid excessive logging overhead
            if (i + 1) % self.log_batch_size == 0:
                logger.info(f"Generated {i + 1}/{count} objects")
        
        # Save metadata to file if requested
        if metadata_file:
            os.makedirs(os.path.dirname(metadata_file) if os.path.dirname(metadata_file) else '.', exist_ok=True)
            import json
            with open(metadata_file, 'w') as f:
                json.dump(all_metadata, f, indent=2)
            logger.info(f"Metadata saved to {metadata_file}")
        
        logger.info(f"Successfully generated {count} objects")
        return all_metadata


def main():
    """Main entry point for generating the novel object set."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate novel articulated object set")
    parser.add_argument("--count", type=int, default=30, help="Number of objects to generate")
    parser.add_argument("--output-dir", type=str, default="data/generated", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--metadata-file", type=str, default="data/generated/metadata.json", help="Metadata output file")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    generator = NovelObjectSet(
        output_dir=args.output_dir,
        seed=args.seed
    )
    
    metadata = generator.generate_set(
        count=args.count,
        metadata_file=args.metadata_file
    )
    
    # Print summary
    logger.info(f"Generation complete. Total objects: {len(metadata)}")
    friction_values = [m['friction'] for m in metadata]
    logger.info(f"Friction range: [{min(friction_values):.3f}, {max(friction_values):.3f}]")
    logger.info(f"Mean friction: {np.mean(friction_values):.3f}")


if __name__ == "__main__":
    main()