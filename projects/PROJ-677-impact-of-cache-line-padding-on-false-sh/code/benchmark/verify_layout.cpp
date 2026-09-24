#include <iostream>
#include <iomanip>
#include <cstdlib>
#include "counter_packed.hpp"
#include "counter_padded.hpp"

int main() {
    std::cout << "=== Memory Layout Verification Utility ===" << std::endl;
    std::cout << std::endl;

    // Verify CounterPacked
    std::cout << "CounterPacked:" << std::endl;
    std::cout << "  Size: " << sizeof(CounterPacked) << " bytes" << std::endl;
    std::cout << "  Alignment: " << alignof(CounterPacked) << " bytes" << std::endl;
    std::cout << "  value1 offset: " << offsetof(CounterPacked, value1) << " bytes" << std::endl;
    std::cout << "  value2 offset: " << offsetof(CounterPacked, value2) << " bytes" << std::endl;
    std::cout << "  value3 offset: " << offsetof(CounterPacked, value3) << " bytes" << std::endl;
    
    bool packed_valid = (sizeof(CounterPacked) == 24);
    std::cout << "  Valid (24 bytes): " << (packed_valid ? "YES" : "NO") << std::endl;
    std::cout << std::endl;

    // Verify CounterPadded
    std::cout << "CounterPadded:" << std::endl;
    std::cout << "  Size: " << sizeof(CounterPadded) << " bytes" << std::endl;
    std::cout << "  Alignment: " << alignof(CounterPadded) << " bytes" << std::endl;
    std::cout << "  value1 offset: " << offsetof(CounterPadded, value1) << " bytes" << std::endl;
    std::cout << "  value2 offset: " << offsetof(CounterPadded, value2) << " bytes" << std::endl;
    std::cout << "  value3 offset: " << offsetof(CounterPadded, value3) << " bytes" << std::endl;
    
    bool padded_valid = (sizeof(CounterPadded) >= 192) && (alignof(CounterPadded) >= 64);
    std::cout << "  Valid (>= 192 bytes, aligned to 64): " << (padded_valid ? "YES" : "NO") << std::endl;
    std::cout << std::endl;

    // Summary
    std::cout << "=== Summary ===" << std::endl;
    if (packed_valid && padded_valid) {
        std::cout << "SUCCESS: Both layouts verified correctly." << std::endl;
        return 0;
    } else {
        std::cout << "FAILURE: Layout verification failed." << std::endl;
        if (!packed_valid) {
            std::cout << "  - CounterPacked size is not 24 bytes" << std::endl;
        }
        if (!padded_valid) {
            std::cout << "  - CounterPadded size < 192 bytes or alignment < 64" << std::endl;
        }
        return 1;
    }
}
