#ifndef COLOR_H
#define COLOR_H

#include <cstdint>

class Color {
public:
    // Constructors
    Color();
    Color(uint8_t r, uint8_t g, uint8_t b);

    // Getters and Setters
    uint8_t GetRed() const;
    uint8_t GetGreen() const;
    uint8_t GetBlue() const;

    void SetRed(uint8_t r);
    void SetGreen(uint8_t g);
    void SetBlue(uint8_t b);

    // Operator overloads for color manipulation
    Color operator+(const Color& other) const;
    Color operator-(const Color& other) const;
    Color operator*(float factor) const;

    // Additional utility methods
    bool operator==(const Color& other) const;
    bool operator!=(const Color& other) const;

private:
    uint8_t red;
    uint8_t green;
    uint8_t blue;
};

#endif // COLOR_H
