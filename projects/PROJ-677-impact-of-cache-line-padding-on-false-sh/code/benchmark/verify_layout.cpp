#include <iostream>
#include <iomanip>
#include <fstream>
#include <string>
#include <cstdlib>
#include "counter_packed.hpp"
#include "counter_padded.hpp"

int main() {
    std::cout << "=== Memory Layout Verification Utility ===" << std::endl;
    std::cout << "Cache Line Size Constant: " << CACHE_LINE_SIZE << " bytes" << std::endl;
    std::cout << std::endl;

    // Verify Packed Structure
    std::cout << "--- CounterPacked ---" << std::endl;
    std::cout << "Size: " << sizeof(CounterPacked) << " bytes" << std::endl;
    std::cout << "Alignment: " << alignof(CounterPacked) << " bytes" << std::endl;
    std::cout << "Offset of 'value': " << offsetof(CounterPacked, value) << std::endl;
    std::cout << "Offset of 'extra1': " << offsetof(CounterPacked, extra1) << std::endl;
    std::cout << "Offset of 'extra2': " << offsetof(CounterPacked, extra2) << std::endl;
    
    bool packed_ok = (sizeof(CounterPacked) == 24);
    std::cout << "Validation (Size == 24): " << (packed_ok ? "PASS" : "FAIL") << std::endl;
    std::cout << std::endl;

    // Verify Padded Structure
    std::cout << "--- CounterPadded ---" << std::endl;
    std::cout << "Size: " << sizeof(CounterPadded) << " bytes" << std::endl;
    std::cout << "Alignment: " << alignof(CounterPadded) << " bytes" << std::endl;
    std::cout << "Offset of 'value': " << offsetof(CounterPadded, value) << std::endl;
    std::cout << "Offset of 'padding': " << offsetof(CounterPadded, padding) << std::endl;
    
    bool padded_ok = (sizeof(CounterPadded) >= CACHE_LINE_SIZE);
    std::cout << "Validation (Size >= " << CACHE_LINE_SIZE << "): " << (padded_ok ? "PASS" : "FAIL") << std::endl;
    std::cout << std::endl;

    // Summary
    std::cout << "=== Summary ===" << std::endl;
    if (packed_ok && padded_ok) {
        std::cout << "All layout verifications PASSED." << std::endl;
        return 0;
    } else {
        std::cerr << "Layout verification FAILED." << std::endl;
        if (!packed_ok) std::cerr << "  - CounterPacked size mismatch." << std::endl;
        if (!padded_ok) std::cerr << "  - CounterPadded size insufficient for cache line." << std::endl;
        return 1;
    }
}