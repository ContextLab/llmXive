#ifndef COUNTER_PACKED_HPP
#define COUNTER_PACKED_HPP

#pragma pack(1)

/**
 * @struct CounterPacked
 * @brief A struct containing three long integers packed tightly without padding.
 * 
 * This struct is designed to demonstrate false sharing in multi-threaded environments.
 * By using #pragma pack(1), the compiler is instructed to pack the members with 1-byte alignment,
 * resulting in a total size of 24 bytes (3 * 8 bytes on 64-bit systems).
 * This compact layout ensures that multiple counters fit within a single cache line (typically 64 bytes),
 * causing cache coherency traffic (false sharing) when different threads modify adjacent counters.
 */
struct CounterPacked {
    long c1;
    long c2;
    long c3;
};

#pragma pack() // Restore default packing alignment

#endif // COUNTER_PACKED_HPP
