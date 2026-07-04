#include <iostream>
#include <cstddef>
#include <cstdint>
#include <cstdlib>

// Packed counter struct: expected size 24 bytes (3 * 8 bytes)
struct alignas(1) PackedCounter {
    std::int64_t value;
    std::int64_t padding1;
    std::int64_t padding2;
};

// Padded counter struct: expected size >= 192 bytes (3 * 64 bytes)
struct AlignedCounter {
    alignas(64) std::int64_t value;
    alignas(64) std::int64_t padding1;
    alignas(64) std::int64_t padding2;
};

int main() {
    std::cout << "=== Memory Layout Verification ===" << std::endl;
    
    size_t packed_size = sizeof(PackedCounter);
    size_t padded_size = sizeof(AlignedCounter);

    std::cout << "PackedCounter size: " << packed_size << " bytes" << std::endl;
    std::cout << "AlignedCounter size: " << padded_size << " bytes" << std::endl;

    // Verify packed size is exactly 24 bytes
    if (packed_size != 24) {
        std::cerr << "ERROR: PackedCounter size is " << packed_size 
                  << " bytes, expected 24 bytes." << std::endl;
        return 1;
    }

    // Verify padded size is at least 192 bytes (3 * 64)
    if (padded_size < 192) {
        std::cerr << "ERROR: AlignedCounter size is " << padded_size 
                  << " bytes, expected at least 192 bytes." << std::endl;
        return 1;
    }

    std::cout << "Layout verification PASSED." << std::endl;
    std::cout << "Packed: " << packed_size << " bytes (expected 24)" << std::endl;
    std::cout << "Padded: " << padded_size << " bytes (expected >= 192)" << std::endl;
    
    return 0;
}
