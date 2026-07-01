#include <iostream>
#include <cstdlib>
#include <cstddef>
#include <cstdint>
#include <type_traits>
#include "counter_packed.hpp"
#include "counter_padded.hpp"

int main() {
    std::cout << "=== Memory Layout Verification Utility ===" << std::endl;

    // Verify Packed Counter Size
    // Expected: 24 bytes (3 x 8 bytes for long long, no padding)
    constexpr size_t expected_packed_size = 24;
    constexpr size_t actual_packed_size = sizeof(CounterPacked);
    
    std::cout << "CounterPacked size: " << actual_packed_size << " bytes" << std::endl;
    std::cout << "  Expected: " << expected_packed_size << " bytes" << std::endl;
    
    if (actual_packed_size != expected_packed_size) {
        std::cerr << "ERROR: CounterPacked size mismatch!" << std::endl;
        std::cerr << "  The struct is not packed as expected. Check #pragma pack(1) usage." << std::endl;
        return 1;
    }
    std::cout << "  [PASS] CounterPacked size verified." << std::endl;

    // Verify Padded Counter Size
    // Expected: >= 192 bytes (3 x 64 bytes cache line padding)
    constexpr size_t min_padded_size = 192;
    constexpr size_t actual_padded_size = sizeof(CounterPadded);
    
    std::cout << "CounterPadded size: " << actual_padded_size << " bytes" << std::endl;
    std::cout << "  Minimum expected: " << min_padded_size << " bytes (3 x 64)" << std::endl;
    
    if (actual_padded_size < min_padded_size) {
        std::cerr << "ERROR: CounterPadded size too small!" << std::endl;
        std::cerr << "  The struct is not padded to separate cache lines." << std::endl;
        return 1;
    }
    std::cout << "  [PASS] CounterPadded size verified (>= 192 bytes)." << std::endl;

    // Verify alignment of individual members in Padded struct
    // Each counter should start at a 64-byte boundary relative to the struct start
    // This is a compile-time check for the layout logic
    static_assert(offsetof(CounterPadded, c1) % 64 == 0, "c1 must be 64-byte aligned");
    static_assert(offsetof(CounterPadded, c2) % 64 == 0, "c2 must be 64-byte aligned");
    static_assert(offsetof(CounterPadded, c3) % 64 == 0, "c3 must be 64-byte aligned");
    
    std::cout << "  [PASS] Member alignment verified (64-byte boundaries)." << std::endl;

    std::cout << "=== All Layout Verifications Passed ===" << std::endl;
    return 0;
}
