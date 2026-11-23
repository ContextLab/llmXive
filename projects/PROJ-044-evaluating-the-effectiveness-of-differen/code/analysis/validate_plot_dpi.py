import struct
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def validate_png_dpi(file_path: str, required_dpi: int = 300) -> bool:
    """
    Validates that a PNG file has the correct DPI metadata embedded.
    
    PNG Physical Pixel Dimensions (pHYs) chunk structure:
    - Bytes 0-3: X pixels per unit (4 bytes, big-endian unsigned int)
    - Bytes 4-7: Y pixels per unit (4 bytes, big-endian unsigned int)
    - Byte 8: Unit specifier (0 = unknown, 1 = meter)
    
    To get DPI from pHYs:
    DPI = (pixels_per_unit * 39.3701) if unit is meter.
    Or if unit is unknown (0), we can't strictly derive DPI, but some tools
    might embed 300 DPI by setting pixels_per_unit to 300 * 39.3701 (approx 11811).
    
    However, standard matplotlib saving with dpi=300 sets the pHYs chunk to:
    X = 11811, Y = 11811, Unit = 1 (meter).
    11811 pixels/meter / 39.3701 inches/meter ≈ 300 DPI.
    
    Args:
        file_path: Path to the PNG file.
        required_dpi: Expected DPI (default 300).
        
    Returns:
        True if DPI matches or is consistent with required_dpi, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        with open(path, 'rb') as f:
            # Check PNG signature (first 8 bytes)
            signature = f.read(8)
            if signature != b'\x89PNG\r\n\x1a\n':
                logger.error(f"Invalid PNG signature in {file_path}")
                return False

            # Iterate through chunks to find pHYs
            found_phys = False
            x_ppu = 0
            y_ppu = 0
            unit = 0

            while True:
                # Read chunk length (4 bytes)
                length_bytes = f.read(4)
                if len(length_bytes) < 4:
                    break
                length = struct.unpack('>I', length_bytes)[0]
                
                # Read chunk type (4 bytes)
                chunk_type = f.read(4)
                if len(chunk_type) < 4:
                    break
                
                # Read chunk data
                data = f.read(length)
                if len(data) < length:
                    break
                
                # Skip CRC (4 bytes)
                f.read(4)

                if chunk_type == b'pHYs':
                    found_phys = True
                    # Unpack X pixels per unit (4 bytes), Y pixels per unit (4 bytes), Unit (1 byte)
                    # Total data length should be 9
                    if len(data) >= 9:
                        x_ppu = struct.unpack('>I', data[0:4])[0]
                        y_ppu = struct.unpack('>I', data[4:8])[0]
                        unit = data[8]
                    break

            if not found_phys:
                logger.warning(f"No pHYs chunk found in {file_path}. DPI cannot be verified.")
                return False

            # Calculate DPI
            # If unit is 1 (meter), DPI = pixels_per_unit / 0.0254 (meters per inch)
            # Or pixels_per_unit * 0.0254 is wrong. 
            # 1 inch = 0.0254 meters.
            # DPI = pixels_per_inch = pixels_per_meter * meters_per_inch
            # DPI = x_ppu * 0.0254
            
            if unit == 1:
                calculated_dpi = x_ppu * 0.0254
            elif unit == 0:
                # Unknown unit. Some tools might just store 300 directly if they ignore units,
                # but standard is meter. If we can't determine, we might fail or warn.
                # For matplotlib default 300 DPI, it sets unit=1.
                logger.warning(f"Unknown unit specifier in pHYs chunk for {file_path}.")
                return False
            else:
                logger.error(f"Invalid unit specifier in pHYs chunk for {file_path}.")
                return False

            logger.info(f"Detected DPI: {calculated_dpi:.2f} (X={x_ppu}, Y={y_ppu}, Unit={unit})")
            
            # Allow a small margin of error for floating point
            if abs(calculated_dpi - required_dpi) < 1.0:
                logger.info(f"DPI validation PASSED for {file_path} (Expected: {required_dpi}, Got: {calculated_dpi:.2f})")
                return True
            else:
                logger.error(f"DPI validation FAILED for {file_path} (Expected: {required_dpi}, Got: {calculated_dpi:.2f})")
                return False

    except Exception as e:
        logger.error(f"Error validating {file_path}: {e}")
        return False

def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    target_file = "results/plots/minority_vs_global_overlay.png"
    target_path = Path(target_file)
    
    if not target_path.exists():
        logger.error(f"Target plot file not found: {target_file}")
        print("FAIL")
        sys.exit(1)
    
    if validate_png_dpi(target_file, required_dpi=300):
        print("PASS")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()
