#include <iostream>
#include <cstddef>
#include <iomanip>
#include "counter_packed.hpp"
#include "counter_padded.hpp"

int main() {
    // Verify Packed Counter Size
    constexpr size_t packed_size = sizeof(CounterPacked);
    std::cout << "CounterPacked size: " << packed_size << " bytes" << std::endl;

    if (packed_size != 24) {
        std::cerr << "ERROR: CounterPacked size is " << packed_size 
                  << ", expected 24 bytes." << std::endl;
        return 1;
    }

    // Verify Padded Counter Size
    constexpr size_t padded_size = sizeof(CounterPadded);
    std::cout << "CounterPadded size: " << padded_size << " bytes" << std::endl;

    if (padded_size < 192) {
        std::cerr << "ERROR: CounterPadded size is " << padded_size 
                  << ", expected >= 192 bytes (3 * 64 bytes alignment)." << std::endl;
        return 1;
    }

    std::cout << "Layout verification passed." << std::endl;
    return 0;
}