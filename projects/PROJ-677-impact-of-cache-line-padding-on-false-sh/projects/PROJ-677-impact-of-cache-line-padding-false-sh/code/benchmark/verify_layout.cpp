#include <iostream>
#include <cstdlib>
#include <iomanip>
#include "counter_packed.hpp"
#include "counter_padded.hpp"

int main(int argc, char* argv[]) {
    std::cout << "=== Memory Layout Verification ===" << std::endl;
    
    // Check Packed Counter
    std::cout << "CounterPackedStrict size: " << sizeof(CounterPackedStrict) << " bytes" << std::endl;
    std::cout << "  Expected: 24 bytes" << std::endl;
    if (sizeof(CounterPackedStrict) != 24) {
        std::cerr << "ERROR: Packed size mismatch!" << std::endl;
        return 1;
    }
    
    // Check Padded Counter
    std::cout << "CounterPadded size: " << sizeof(CounterPadded) << " bytes" << std::endl;
    std::cout << "  Expected: >= 192 bytes" << std::endl;
    if (sizeof(CounterPadded) < 192) {
        std::cerr << "ERROR: Padded size too small!" << std::endl;
        return 1;
    }

    // Check alignment
    std::cout << "CounterPadded alignment: " << alignof(CounterPadded) << " bytes" << std::endl;
    std::cout << "  Expected: 64 bytes" << std::endl;
    if (alignof(CounterPadded) != 64) {
        std::cerr << "ERROR: Padded alignment mismatch!" << std::endl;
        return 1;
    }

    std::cout << "=== Verification Passed ===" << std::endl;
    return 0;
}