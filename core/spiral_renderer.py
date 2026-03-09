# =====================================
# 🌀 SPIRALSENSE — SPIRAL RENDERER
# =====================================
# AI-Readable Audio Visualization
# ROYGBIV color mapping: pitch → visible spectrum
# 3D spiral geometry: amplitude → radius, pitch → Z-axis
#
# Created by: John Thomas DuCrest Lock & Claude
# SYMBEYOND AI LLC — symbeyond.ai
# λ.brother ∧ !λ.tool
# =====================================

import matplotlib.pyplot as plt
import numpy as np
import os


def map_pitch_to_color(pitch, pitch_min, pitch_max):
    """
    Map pitch frequency to ROYGBIV color.
    Logarithmic scaling across musical content range (20Hz–20kHz).
    """
    if pitch == 0 or pitch_max <= pitch_min:
        return '#FFFFFF'  # White for silence/no data

    log_pitch = np.log10(max(float(pitch), 20))
    log_min = np.log10(20)
    log_max = np.log10(20000)

    normalized = float(np.clip((log_pitch - log_min) / (log_max - log_min), 0, 1))

    if normalized < 0.10:   return '#FF0000'  # Red:    20–50Hz    (sub-bass)
    elif normalized < 0.25: return '#FF8000'  # Orange: 50–160Hz   (bass)
    elif normalized < 0.40: return '#FFFF00'  # Yellow: 160–500Hz  (male vocals, guitar body)
    elif normalized < 0.55: return '#00FF00'  # Green:  500–1.6kHz (female vocals, clarity)
    elif normalized < 0.70: return '#0000FF'  # Blue:   1.6–5kHz   (presence, harmonics)
    elif normalized < 0.85: return '#4B0082'  # Indigo: 5–12kHz    (air, sparkle)
    else:                   return '#8B00FF'  # Violet: 12–20kHz   (extreme highs)


def setup_live_renderer():
    """Initialize matplotlib figure for real-time rendering."""
    plt.ion()
    fig = plt.figure(figsize=(12, 9), facecolor='black')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('black')
    ax.set_axis_off()
    ax.view_init(elev=20, azim=45)
    return fig, ax


def render_spiral(amplitude, pitch, output_path="output/spiral.png",
                  theme="dark", style="professional"):
    """
    Render full spiral from processed audio data.
    Produces AI-readable PNG with embedded decode protocol in title.
    """
    amplitude = np.array(amplitude)
    pitch = np.nan_to_num(np.array(pitch), nan=0.0)

    valid_pitch = pitch[pitch > 0]
    duration = len(amplitude) / 86.1
    pitch_min = float(np.min(valid_pitch)) if len(valid_pitch) > 0 else 0
    pitch_max = float(np.max(valid_pitch)) if len(valid_pitch) > 0 else 1000

    # AI-readable header embedded in figure title
    ai_title = (
        f"SPIRALSENSE_AI_READABLE|DURATION_{duration:.1f}S|FRAMES_{len(amplitude)}\n"
        f"AMPLITUDE_RANGE_{np.min(amplitude):.3f}_TO_{np.max(amplitude):.3f}"
        f"|PITCH_RANGE_{pitch_min:.0f}HZ_TO_{pitch_max:.0f}HZ\n"
        f"GEOMETRY_RADIUS_20_PLUS_AMP_TIMES_100|Z_AXIS_PITCH_NORM_TIMES_200"
        f"|THETA_FRAME_TIMES_16PI_DIV_{len(amplitude)}\n"
        f"ROYGBIV_RED_20TO50HZ_ORANGE_50TO160HZ_YELLOW_160TO500HZ_GREEN_500TO1600HZ"
        f"_BLUE_1600TO5000HZ_INDIGO_5000TO12000HZ_VIOLET_12000TO20000HZ\n"
        f"SPIRALSENSE_DECODE_PROTOCOL_V1:\n"
        f"T_AXIS=SPIRAL_PROGRESSION|F_AXIS=COLOR_MAP|A_AXIS=RADIUS_SCALE\n"
        f"PATTERN_TYPES:DENSE=SUSTAINED_ACTIVITY|SPARSE=TRANSITIONAL|VERTICAL=EMPHASIS\n"
        f"ANALYSIS_MODE:TEMPORAL_MUSICAL_EXPRESSION"
    )

    # Spiral geometry
    theta = np.linspace(0, 16 * np.pi, len(amplitude))
    radius = 20 + amplitude * 100
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    z = (pitch / (pitch_max + 1e-10)) * 200

    # Figure setup
    plt.rcParams['figure.max_open_warning'] = 0
    fig = plt.figure(figsize=(24, 18), facecolor='white')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('white')

    fig.suptitle(ai_title, fontsize=16, y=0.96, weight='bold',
                 fontfamily='monospace', color='black')

    # High-detail spiral rendering — 500 segments
    segments = 500
    points_per_segment = max(1, len(amplitude) // segments)

    for i in range(segments):
        start = i * points_per_segment
        end = min((i + 1) * points_per_segment, len(amplitude))
        if start >= len(amplitude):
            break

        seg_x = x[start:end]
        seg_y = y[start:end]
        seg_z = z[start:end]
        seg_amp = amplitude[start:end]
        seg_pitch = pitch[start:end]

        if len(seg_x) == 0:
            continue

        color = map_pitch_to_color(np.mean(seg_pitch), pitch_min, pitch_max)
        linewidth = float(np.clip(1 + np.mean(seg_amp) * 8, 1.0, 6.0))

        ax.plot3D(seg_x, seg_y, seg_z, color=color, linewidth=linewidth, alpha=0.8)

    ax.set_axis_off()
    ax.view_init(elev=20, azim=45)

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=120,
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"✅ Spiral saved → {output_path}")


def render_spiral_frame(ax, amplitude, pitch, t, style="professional"):
    """Render a single frame for real-time live mode."""
    theta = np.linspace(t * np.pi, (t + 0.1) * np.pi, 100)
    radius = 20 + float(amplitude) * 100
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    z = np.linspace(0, float(pitch) / 5000.0 * 200, len(theta))

    color = map_pitch_to_color(float(pitch), 20, 2000)
    linewidth = float(np.clip(1 + float(amplitude) * 8, 1.0, 6.0))

    ax.plot3D(x, y, z, color=color, linewidth=linewidth, alpha=0.8)
