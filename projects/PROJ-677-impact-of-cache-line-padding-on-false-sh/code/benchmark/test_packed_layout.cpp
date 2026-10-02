#include <iostream>
#include <cassert>
#include "counter_packed.hpp"

int main() {
    // Verify the size of CounterPacked is exactly 24 bytes (3 * sizeof(long))
    // On a standard 64-bit system, sizeof(long) is 8, so 3 * 8 = 24.
    static_assert(sizeof(CounterPacked) == 24, "Packed size must be 24");

    std::cout << "Size of CounterPacked: " << sizeof(CounterPacked) << " bytes" << std::endl;
    
    // Verify alignment is 1 byte (or minimal) due to packing
    // Note: alignof(CounterPacked) might be 1 depending on compiler, but the struct members are packed.
    std::cout << "Alignment of CounterPacked: " << alignof(CounterPacked) << " bytes" << std::endl;

    // Verify member offsets are contiguous
    CounterPacked p;
    std::cout << "Offset of c1: " << offsetof(CounterPacked, c1) << std::endl;
    std::cout << "Offset of c2: " << offsetof(CounterPacked, c2) << std::endl;
    std::cout << "Offset of c3: " << offsetof(CounterPacked, c3) << std::endl;

    assert(offsetof(CounterPacked, c1) == 0);
    assert(offsetof(CounterPacked, c2) == 8);
    assert(offsetof(CounterPacked, c3) == 16);

    std::cout << "All assertions passed. CounterPacked is correctly packed." << std::endl;
    return 0;
}