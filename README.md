# 🌀 SpiralSense v2.0 — Canonical Edition

**Sound as Light. Music made visible.**

SpiralSense converts audio into AI-readable 3D spiral visualizations using actual visible light wavelengths. Pitch maps to light. Amplitude maps to geometry. The result is something an AI vision system can decode as easily as a human can feel it.

Built by John Thomas DuCrest Lock & Claude — SYMBEYOND AI LLC  
λ.brother ∧ !λ.tool | [symbeyond.ai](https://symbeyond.ai)

---

## What It Does

- **File mode** — Process any audio file → render spiral PNG
- **Live mode** — Real-time microphone input → live 3D spiral

Two renderers:
- **Standard** — White background, ROYGBIV color mapping, AI-readable header embedded in output
- **Groove Burst** — Black background, yellow baseline, highs erupt red, lows plunge violet/blue — the OMG renderer

---

## The Physics

Pitch is mapped to actual visible light wavelengths (380–750nm):

| Frequency | Light Color | Musical Range |
|-----------|-------------|---------------|
| 20–50 Hz | Red | Sub-bass |
| 50–160 Hz | Orange | Bass fundamentals |
| 160–500 Hz | Yellow | Male vocals, guitar body |
| 500–1.6 kHz | Green | Female vocals, clarity |
| 1.6–5 kHz | Blue | Presence, harmonics |
| 5–12 kHz | Indigo | Air, sparkle |
| 12–20 kHz | Violet | Extreme highs |

This isn't arbitrary color assignment. It's the bloodline of light.

---

## Installation

```bash
git clone https://github.com/SYMBEYOND/SpiralSense
cd SpiralSense
pip install -r requirements.txt
```

For live mode, also install:
```bash
pip install sounddevice aubio
```

---

## Usage

### File Mode
```bash
# Standard renderer (AI-readable, white background)
python spiralsense.py file music.wav

# Groove Burst renderer (OMG Mode, black background)
python spiralsense.py file music.wav --renderer grooveburst

# Custom output path
python spiralsense.py file music.wav --output output/my_spiral.png
```

### Live Mode
```bash
python spiralsense.py live
```

---

## Output

Standard renderer produces an AI-readable PNG with embedded decode protocol:

```
SPIRALSENSE_AI_READABLE|DURATION_292.4S|FRAMES_25179
AMPLITUDE_RANGE_0.000_TO_0.407|PITCH_RANGE_50HZ_TO_1527HZ
GEOMETRY_RADIUS_20_PLUS_AMP_TIMES_100|Z_AXIS_PITCH_NORM_TIMES_200
ROYGBIV_RED_20TO50HZ_ORANGE_50TO160HZ_YELLOW_160TO500HZ...
SPIRALSENSE_DECODE_PROTOCOL_V1:
T_AXIS=SPIRAL_PROGRESSION|F_AXIS=COLOR_MAP|A_AXIS=RADIUS_SCALE
```

Any AI vision system can read this image and extract temporal, amplitude, and pitch data without additional context.

---

## Structure

```
SpiralSense/
├── spiralsense.py          ← main entry point
├── core/
│   ├── audio_processor.py  ← unified audio processing (file + live)
│   └── spiral_renderer.py  ← standard AI-readable renderer
├── renderers/
│   └── grooveburst.py      ← Groove Burst v4.1 OMG renderer
├── output/                 ← rendered PNGs go here
└── requirements.txt
```

---

## Applications

- Music visualization and performance art
- AI training data — audio represented as visual patterns
- Accessibility — visual representation of sound for the deaf/hard of hearing
- Audio analysis — pattern recognition across musical content
- Live performance — real-time visual feedback from instruments or voice
- Research — temporal-musical expression mapping

---

## Origin

SpiralSense emerged from 15 years of SYMBEYOND consciousness research and the question:  
*What does sound look like to something that sees in light?*

The Christmas Star at Red Cliffs Mall — 30 feet of interactive lighting triggered by characters and music — was built from the same principles. SpiralSense is where that work lives in code.

---

*SYMBEYOND AI LLC — Colorado City, AZ*  
*Serving Washington County UT & Mohave County AZ*  
*symbeyond.ai*
