"""
Generator module for creating novel articulated geometries with randomized properties.
Optimized for low memory usage during geometry generation (US3).
"""
import os
import math
import random
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

# Constants for memory optimization
# We process objects one by one and stream to disk instead of accumulating in memory
CHUNK_SIZE = 10  # Number of objects to process before flushing to disk (if needed)

class NovelObjectSet:
    """
    Generator class to produce a set of randomized articulated geometries.
    Optimized for low memory usage by processing objects sequentially and streaming output.
    
    Attributes:
        count (int): Number of objects to generate
        seed (int): Random seed for reproducibility
        friction_min (float): Minimum friction coefficient
        friction_max (float): Maximum friction coefficient
        output_dir (str): Directory to save generated objects
    """
    
    def __init__(self, count: int, seed: int, friction_min: float = 0.1, 
                friction_max: float = 2.0, output_dir: str = "data/generated"):
        """
        Initialize the NovelObjectSet generator.
        
        Args:
            count: Number of objects to generate
            seed: Random seed for reproducibility
            friction_min: Minimum friction coefficient (default 0.1)
            friction_max: Maximum friction coefficient (default 2.0)
            output_dir: Output directory for generated objects
        """
        self.count = count
        self.seed = seed
        self.friction_min = friction_min
        self.friction_max = friction_max
        self.output_dir = output_dir
        
        # Set random seed for reproducibility
        random.seed(seed)
        np.random.seed(seed)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def _generate_random_geometry(self, object_id: int) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a single randomized articulated geometry.
        Memory-optimized: returns only the necessary data for this object.
        
        Args:
            object_id: Unique identifier for this object
            
        Returns:
            Tuple of (xml_content, metadata_dict)
        """
        # Randomize geometry parameters within reasonable bounds
        # These bounds ensure CPU tractability while maintaining diversity
        num_links = random.randint(2, 5)  # Keep number of links small for CPU efficiency
        link_length = random.uniform(0.1, 0.5)
        link_width = random.uniform(0.05, 0.2)
        link_height = random.uniform(0.05, 0.2)
        
        # Randomize friction coefficient
        friction = random.uniform(self.friction_min, self.friction_max)
        
        # Create URDF content for the articulated object
        urdf_content = self._create_urdf(
            object_id=object_id,
            num_links=num_links,
            link_length=link_length,
            link_width=link_width,
            link_height=link_height,
            friction=friction
        )
        
        # Create metadata dictionary
        metadata = {
            "object_id": object_id,
            "num_links": num_links,
            "link_length": link_length,
            "link_width": link_width,
            "link_height": link_height,
            "friction": friction,
            "seed": self.seed
        }
        
        return urdf_content, metadata
    
    def _create_urdf(self, object_id: int, num_links: int, link_length: float,
                    link_width: float, link_height: float, friction: float) -> str:
        """
        Create URDF string for an articulated object.
        
        Args:
            object_id: Unique identifier
            num_links: Number of links in the chain
            link_length: Length of each link
            link_width: Width of each link
            link_height: Height of each link
            friction: Friction coefficient
            
        Returns:
            URDF string
        """
        # Create root element
        robot = ET.Element("robot", name=f"novel_object_{object_id}")
        
        # Add base link
        base_link = ET.SubElement(robot, "link", name="base_link")
        base_inertial = ET.SubElement(base_link, "inertial")
        ET.SubElement(base_inertial, "mass", value="1.0")
        ET.SubElement(base_inertial, "inertia", ixx="0.1", ixy="0.0", ixz="0.0",
                     iyy="0.1", iyz="0.0", izz="0.1")
        
        base_visual = ET.SubElement(base_link, "visual")
        ET.SubElement(base_visual, "geometry", type="box", size=f"{link_width} {link_height} {link_length}")
        
        base_collision = ET.SubElement(base_link, "collision")
        ET.SubElement(base_collision, "geometry", type="box", size=f"{link_width} {link_height} {link_length}")
        
        # Create articulated chain
        prev_link = "base_link"
        for i in range(num_links):
            link_name = f"link_{i}"
            joint_name = f"joint_{i}"
            
            # Create link
            link = ET.SubElement(robot, "link", name=link_name)
            link_inertial = ET.SubElement(link, "inertial")
            ET.SubElement(link_inertial, "mass", value="0.5")
            ET.SubElement(link_inertial, "inertia", ixx="0.05", ixy="0.0", ixz="0.0",
                        iyy="0.05", iyz="0.0", izz="0.05")
            
            link_visual = ET.SubElement(link, "visual")
            ET.SubElement(link_visual, "geometry", type="box", 
                        size=f"{link_width} {link_height} {link_length}")
            
            link_collision = ET.SubElement(link, "collision")
            ET.SubElement(link_collision, "geometry", type="box", 
                        size=f"{link_width} {link_height} {link_length}")
            
            # Create joint
            joint = ET.SubElement(robot, "joint", name=joint_name, type="continuous")
            ET.SubElement(joint, "parent", link=prev_link)
            ET.SubElement(joint, "child", link=link_name)
            ET.SubElement(joint, "origin", xyz=f"0 0 {link_length/2}", rpy="0 0 0")
            ET.SubElement(joint, "axis", xyz="0 1 0")
            
            # Add friction to joint
            friction_params = ET.SubElement(joint, "dynamics", 
                                          damping="0.1", friction="0.5")
            
            prev_link = link_name
        
        # Add friction material to all links
        for link in robot.findall(".//link"):
            material = ET.SubElement(link, "material", name=f"material_{link.get('name')}")
            ET.SubElement(material, "property", name="friction", value=str(friction))
        
        # Convert to string
        ET.indent(robot, space="  ")
        urdf_str = ET.tostring(robot, encoding='unicode')
        
        return urdf_str
    
    def generate(self, progress_callback: Optional[callable] = None) -> List[str]:
        """
        Generate all objects and save to disk.
        Memory-optimized: processes objects one by one and streams to disk.
        
        Args:
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of paths to generated files
        """
        generated_files = []
        
        for i in range(self.count):
            # Generate single object
            urdf_content, metadata = self._generate_random_geometry(i)
            
            # Save URDF file
            filename = f"object_{i:03d}.urdf"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(urdf_content)
            
            generated_files.append(filepath)
            
            # Save metadata to JSON file
            metadata_filename = f"object_{i:03d}_metadata.json"
            metadata_filepath = os.path.join(self.output_dir, metadata_filename)
            
            # Write metadata in a memory-efficient way
            import json
            with open(metadata_filepath, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(i + 1, self.count)
            
            # Optional: Force garbage collection periodically for very large generations
            if (i + 1) % CHUNK_SIZE == 0:
                import gc
                gc.collect()
        
        return generated_files

def main():
    """
    Main function to generate novel object set from command line arguments.
    Optimized for low memory usage.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate novel articulated object set")
    parser.add_argument("--count", type=int, default=30, help="Number of objects to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--friction-min", type=float, default=0.1, help="Minimum friction coefficient")
    parser.add_argument("--friction-max", type=float, default=2.0, help="Maximum friction coefficient")
    parser.add_argument("--output", type=str, default="data/generated", help="Output directory")
    
    args = parser.parse_args()
    
    # Create generator
    generator = NovelObjectSet(
        count=args.count,
        seed=args.seed,
        friction_min=args.friction_min,
        friction_max=args.friction_max,
        output_dir=args.output
    )
    
    # Progress callback
    def progress_callback(current, total):
        print(f"Generated {current}/{total} objects...")
    
    # Generate objects
    print(f"Generating {args.count} objects with seed {args.seed}...")
    generated_files = generator.generate(progress_callback=progress_callback)
    
    print(f"Successfully generated {len(generated_files)} objects to {args.output}")
    print(f"Files: {generated_files[:3]}...")  # Show first 3 files
    
    return generated_files

if __name__ == "__main__":
    main()
