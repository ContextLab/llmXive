#ifndef COUNTER_PACKED_HPP
#define COUNTER_PACKED_HPP

#pragma pack(push, 1)
struct CounterPacked {
    long value;
    int id;
    char extra; // To make size 24 bytes (8+4+1 + padding to 24? No, 13 bytes -> packed to 13)
    // Wait, T005 says 24 bytes packed. 
    // Let's adjust to match T005 requirement: "24 bytes packed".
    // Standard long is 8, int is 4. 8+4 = 12. 
    // To get 24, we might need more fields or specific alignment.
    // However, the task T007 description says: "packed (24 bytes)".
    // Let's create a struct that is exactly 24 bytes when packed.
    // long (8) + int (4) + char (1) + padding (1) -> 14? No.
    // Let's use multiple fields.
    // long (8) + long (8) + int (4) + char (4) = 24.
    // Or simply rely on the fact that T005 verifies it.
    // Let's try: long (8) + int (4) + char (12) = 25? No.
    // Let's assume the user wants a struct that is naturally small but packed to 24.
    // Actually, T005 says "assert struct sizes (24 bytes packed, ≥192 bytes padded)".
    // If I define:
    // struct CounterPacked { long v; int id; char pad[12]; }; // 8+4+12 = 24.
    
    long value;
    int id;
    char padding[12]; // Ensures total size is 24 bytes when packed
};
#pragma pack(pop)

static_assert(sizeof(CounterPacked) == 24, "CounterPacked must be 24 bytes");

inline void CounterPacked::increment() {
    ++value;
}

inline long CounterPacked::get() const {
    return value;
}

#endif // COUNTER_PACKED_HPP
