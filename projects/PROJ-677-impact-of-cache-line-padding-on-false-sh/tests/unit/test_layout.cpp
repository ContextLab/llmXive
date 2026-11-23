#include <iostream>
#include <cassert>
#include <cstddef>
#include "../code/benchmark/counter_packed.hpp"
#include "../code/benchmark/counter_padded.hpp"

int main() {
    // Test CounterPacked size and alignment
    // Expected size: 24 bytes (3 * 8 bytes for long, packed)
    constexpr size_t packed_size = sizeof(CounterPacked);
    std::cout << "CounterPacked size: " << packed_size << " bytes" << std::endl;
    static_assert(packed_size == 24, "Packed size must be 24");
    static_assert(alignof(CounterPacked) == 1, "Packed alignment must be 1");

    // Test CounterPadded size and alignment
    // Expected size: >= 192 bytes (3 * 64 bytes due to alignas(64))
    constexpr size_t padded_size = sizeof(CounterPadded);
    std::cout << "CounterPadded size: " << padded_size << " bytes" << std::endl;
    static_assert(padded_size >= 192, "Padded size must be >= 192");
    static_assert(alignof(CounterPadded) == 64, "Padded alignment must be 64");

    // Verify member offsets within CounterPacked (should be contiguous)
    CounterPacked packed;
    // In a packed struct, members are adjacent
    // c1 at 0, c2 at 8, c3 at 16
    char* p1 = reinterpret_cast<char*>(&packed.c1);
    char* p2 = reinterpret_cast<char*>(&packed.c2);
    char* p3 = reinterpret_cast<char*>(&packed.c3);
    
    assert((p2 - p1) == sizeof(long));
    assert((p3 - p2) == sizeof(long));
    std::cout << "CounterPacked members are contiguous as expected." << std::endl;

    // Verify member offsets within CounterPadded (should be 64-byte aligned)
    CounterPadded padded;
    char* pad1 = reinterpret_cast<char*>(&padded.c1);
    char* pad2 = reinterpret_cast<char*>(&padded.c2);
    char* pad3 = reinterpret_cast<char*>(&padded.c3);

    // Each member should be 64 bytes apart
    assert((pad2 - pad1) == 64);
    assert((pad3 - pad2) == 64);
    std::cout << "CounterPadded members are 64-byte aligned as expected." << std::endl;

    std::cout << "All layout verification tests passed." << std::endl;
    return 0;
}