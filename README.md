# Intelligent 3D LED Smart Alarm Clock

**ECE 5725 — Fall 2023 Final Project**

[Live demo & full report](https://courses.ece.cornell.edu/ece5990/ECE5725_Fall2023_Projects/4%20Friday%20December%208/9%203D%20LED%20Display/M_dy297_sw2327_kg535/ECE5725%20website/index.html)

---

### What it is

A portable, triangular alarm clock built from **three 16 × 32 RGB LED panels** driven by a Raspberry Pi 4. An onboard IMU senses orientation so the display re‑arranges itself in real time, blending practical time‑keeping with playful LED art.

### Key Modes

* **Clock** – digits always face the viewer, regardless of the side that’s up.
* **Sand** – tilt the clock and the digits collapse like falling sand; level it to “rewind.”
* **Alarm** – two buttons set hour/minute; a buzzer sounds at wake‑up time.
* **Zen / Snow** – pose‑aware image scroll or interactive snow‑flake simulation.

### Hardware at a Glance

Raspberry Pi 4 • 3 × 16 × 32 RGB matrices • MPU‑6050 IMU • 4 momentary buttons • 3‑D‑printed PLA case with magnets • 5 V / 4 A power brick
*(≈ US \$76 in parts)*

### Team

| Name           | NetID  | Focus                                    |
| -------------- | ------ | ---------------------------------------- |
| **Ding Yang**  | dy297  | Mechanical design, sand‑mode animation   |
| **Keyun Gao**  | kg535  | IMU integration, snow simulation         |
| **Steve Wang** | sw2327 | Core software architecture & integration |

### Acknowledgements

Built with the open‑source [`rpi-rgb-led-matrix`](https://github.com/hzeller/rpi-rgb-led-matrix) library and support from Cornell ECE 5725 staff.

Released under the **MIT License**.
