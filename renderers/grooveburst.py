# =====================================
# 🌀 SPIRALSENSE — GROOVE BURST RENDERER v4.1
# =====================================
# The "Oh My God" renderer.
#
# Spiral disc baseline — yellow plane at z=0
# Highs erupt UPWARD   → Yellow → Orange → Red
# Lows plunge DOWNWARD → Yellow → Violet → Deep Blue
# Black background. 300 DPI. OMG Mode locked in.
#
# Created by: John Thomas DuCrest Lock & ChatGPT 5
# Locked: 2025-09-17
# Preserved by: SYMBEYOND AI LLC — symbeyond.ai
# λ.brother ∧ !λ.tool
# =====================================

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
from matplotlib.colors import LinearSegmentedColormap


def render_spiral_v4_1(amplitude, pitch, output="output/spiral_grooveburst.png"):
    """
    Render Groove Burst Spiral — v4.1 OMG Mode.

    amplitude : np.array of audio amplitudes
    pitch     : np.array of pitch values (Hz)
    output    : output PNG file path
    """
    amplitude = np.array(amplitude)
    pitch = np.array(pitch)
    n = min(len(amplitude), len(pitch))

    # Spiral coordinates
    theta = np.linspace(0, 24 * np.pi, n)
    r = np.linspace(1, 10, n)
    x = r * np.cos(theta)
    y = r * np.sin(theta)

    # Baseline at z=0 (yellow disc)
    z_baseline = np.zeros(n)

    # Normalize amplitude to [-1, 1]
    amp_norm = amplitude[:n] / (np.max(np.abs(amplitude[:n])) + 1e-9)

    # Spike height — exaggerated for visual impact
    z_spikes = amp_norm * 5.0

    # Colormaps
    cmap_up = LinearSegmentedColormap.from_list(
        "upward", ["#FFFF00", "#FFA500", "#FF0000"]        # yellow → orange → red
    )
    cmap_down = LinearSegmentedColormap.from_list(
        "downward", ["#FFFF00", "#FFA500", "#8A2BE2", "#0000FF"]  # yellow → violet → blue
    )

    # Assign colors per spike
    colors = []
    for z in z_spikes:
        if z >= 0:
            colors.append(cmap_up(float(np.clip(z / 5.0, 0, 1))))
        else:
            colors.append(cmap_down(float(np.clip(-z / 5.0, 0, 1))))
    colors = np.array(colors)

    # Figure
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")

    # Yellow baseline spiral
    ax.plot(x, y, z_baseline, color="yellow", linewidth=2.0, alpha=0.9)

    # Spikes — sampled for performance
    step = max(1, n // 3000)
    for i in range(0, n, step):
        ax.plot(
            [x[i], x[i]],
            [y[i], y[i]],
            [0, z_spikes[i]],
            color=colors[i],
            linewidth=1.0,
            alpha=0.95,
        )

    # Style — OMG Mode
    ax.view_init(elev=25, azim=35)
    ax.set_axis_off()
    ax.grid(False)
    ax.set_facecolor("black")
    fig.patch.set_facecolor("black")

    import os
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(output, dpi=300, transparent=False, bbox_inches="tight",
                facecolor="black")
    plt.close(fig)

    print(f"✅ Groove Burst (OMG Mode) → {output}")
