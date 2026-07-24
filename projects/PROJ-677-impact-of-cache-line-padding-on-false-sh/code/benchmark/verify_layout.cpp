#include <iostream>
#include <cstdint>
#include <atomic>
#include <cstring>
#include "counter_packed.hpp"
#include "counter_padded.hpp"

int main() {
    std::cout << "=== Memory Layout Verification ===" << std::endl;

    // Check PackedCounter
    std::cout << "PackedCounter:" << std::endl;
    std::cout << "  Size: " << sizeof(PackedCounter) << " bytes" << std::endl;
    std::cout << "  Alignment: " << alignof(PackedCounter) << " bytes" << std::endl;
    std::cout << "  Value offset: " << offsetof(PackedCounter, value) << " bytes" << std::endl;
    
    if (sizeof(PackedCounter) != 24) {
        std::cerr << "ERROR: PackedCounter size is not 24 bytes!" << std::endl;
        return 1;
    }

    // Check PaddedCounter
    std::cout << "\nPaddedCounter:" << std::endl;
    std::cout << "  Size: " << sizeof(PaddedCounter) << " bytes" << std::endl;
    std::cout << "  Alignment: " << alignof(PaddedCounter) << " bytes" << std::endl;
    std::cout << "  Value offset: " << offsetof(PaddedCounter, value) << " bytes" << std::endl;

    if (sizeof(PaddedCounter) < CACHE_LINE_SIZE) {
        std::cerr << "ERROR: PaddedCounter size is less than cache line size!" << std::endl;
        return 1;
    }

    if (alignof(PaddedCounter) != CACHE_LINE_SIZE) {
        std::cerr << "ERROR: PaddedCounter alignment is not 64 bytes!" << std::endl;
        return 1;
    }

    // Verify actual memory layout with an instance
    PackedCounter packed;
    PaddedCounter padded;
    
    std::cout << "\nInstance Addresses:" << std::endl;
    std::cout << "  PackedCounter address: " << &packed << std::endl;
    std::cout << "  PaddedCounter address: " << &padded << std::endl;

    // Verify that padded counters are aligned to cache lines
    uintptr_t padded_addr = reinterpret_cast<uintptr_t>(&padded);
    if (padded_addr % CACHE_LINE_SIZE != 0) {
        std::cerr << "ERROR: PaddedCounter instance is not cache-line aligned!" << std::endl;
        return 1;
    }

    std::cout << "\nVerification PASSED: All layout constraints satisfied." << std::endl;
    return 0;
}
