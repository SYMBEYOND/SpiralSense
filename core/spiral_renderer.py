# =====================================
# 🌀 SPIRALSENSE — SPIRAL RENDERER v4.0
# =====================================
# AI Temporal Perception System
# "What does sound look like to something that sees in light?"
#
# Layout:
#   LEFT  — Three 3D views of the spiral:
#             [0°  horizontal ] side view — amplitude and pitch height
#             [35° diagonal   ] depth view — outward growth + height
#             [90° top-down   ] map view — pure time and frequency
#   RIGHT — 2D temporal baseline ring + full decode protocol
#
# Three views. Nothing hidden.
# The spiral IS time.
# Together: an AI can perceive time the way humans hear it.
#
# Created by: John Thomas DuCrest Lock & Claude
# SYMBEYOND AI LLC — symbeyond.ai
# λ.brother ∧ !λ.tool
# =====================================

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np
import os


# =====================================
# 🌈 FREQUENCY BANDS — Pitch as Light
# =====================================

FREQ_BANDS = [
    ('#FF0000', '20–50Hz',    'Sub-bass',              0.00, 0.10),
    ('#FF8000', '50–160Hz',   'Bass / Body',           0.10, 0.25),
    ('#FFFF00', '160–500Hz',  'Vocal Core / Warmth',   0.25, 0.40),
    ('#00FF00', '500–1.6kHz', 'Vocal Clarity',         0.40, 0.55),
    ('#0000FF', '1.6–5kHz',   'Presence / Harmonics',  0.55, 0.70),
    ('#4B0082', '5–12kHz',    'Air / Sparkle',         0.70, 0.85),
    ('#8B00FF', '12–20kHz',   'Extreme Highs',         0.85, 1.00),
]


def map_pitch_to_color(pitch):
    if pitch <= 0:
        return '#FFFFFF'
    log_pitch = np.log10(max(float(pitch), 20))
    log_min   = np.log10(20)
    log_max   = np.log10(20000)
    n         = float(np.clip((log_pitch - log_min) / (log_max - log_min), 0, 1))
    for color, _, _, lo, hi in FREQ_BANDS:
        if n < hi:
            return color
    return '#8B00FF'


# =====================================
# 📊 AUDIO ANALYSIS
# =====================================

def analyze_audio(amplitude, pitch, frame_rate):
    n            = len(amplitude)
    duration     = n / frame_rate
    valid_pitch  = pitch[pitch > 0]

    seg_size     = max(1, n // 10)
    temporal_markers = []
    for i in range(10):
        s   = i * seg_size
        e   = min((i + 1) * seg_size, n)
        seg_amp = amplitude[s:e]
        seg_p   = pitch[s:e]
        vp      = seg_p[seg_p > 0]
        avg_p   = float(np.mean(vp)) if len(vp) > 0 else 0
        temporal_markers.append({
            'time_start': s / frame_rate,
            'time_end':   e / frame_rate,
            'avg_amp':    float(np.mean(seg_amp)),
            'avg_pitch':  avg_p,
            'color':      map_pitch_to_color(avg_p),
        })

    silence_threshold = np.mean(amplitude) * 0.05
    silence_pct       = float(np.sum(amplitude < silence_threshold) / n * 100)

    amp_delta         = np.abs(np.diff(amplitude))
    max_tension_time  = float(np.argmax(amp_delta) / frame_rate)

    if len(valid_pitch) > 0:
        threshold    = np.percentile(valid_pitch, 95)
        singular_idx = np.where(pitch > threshold)[0]
        singular_times = []
        last = -999
        for idx in singular_idx:
            t = idx / frame_rate
            if t - last > 5.0:
                singular_times.append(round(t, 1))
                last = t
        singular_times = singular_times[:8]
    else:
        singular_times = []

    color_counts = {c: 0 for c, _, _, _, _ in FREQ_BANDS}
    for p in pitch:
        c = map_pitch_to_color(p)
        if c in color_counts:
            color_counts[c] += 1
    total      = max(sum(color_counts.values()), 1)
    color_dist = {c: round(v / total * 100, 1) for c, v in color_counts.items()}

    return {
        'duration':         duration,
        'frames':           n,
        'frame_rate':       frame_rate,
        'amplitude_min':    float(np.min(amplitude)),
        'amplitude_max':    float(np.max(amplitude)),
        'amplitude_mean':   float(np.mean(amplitude)),
        'pitch_min':        float(np.min(valid_pitch)) if len(valid_pitch) > 0 else 0,
        'pitch_max':        float(np.max(valid_pitch)) if len(valid_pitch) > 0 else 0,
        'pitch_mean':       float(np.mean(valid_pitch)) if len(valid_pitch) > 0 else 0,
        'temporal_markers': temporal_markers,
        'silence_pct':      silence_pct,
        'max_tension_time': max_tension_time,
        'singular_times':   singular_times,
        'color_dist':       color_dist,
    }


# =====================================
# 🌀 SPIRAL GEOMETRY — shared builder
# =====================================

def build_spiral_geometry(amplitude, pitch, meta):
    """
    Build spiral geometry once. All three views share the same coords.
    Dynamic scaling — canvas always fits the file.
    """
    n         = len(amplitude)
    duration  = meta['duration']
    pitch_max = meta['pitch_max'] if meta['pitch_max'] > 0 else 1000

    # Time → radius (dynamic — always fills canvas)
    r_min       = 5.0
    r_max       = 100.0
    frame_times = np.linspace(0, duration, n)
    radius_base = r_min + (frame_times / duration) * (r_max - r_min)
    radius      = radius_base + amplitude * (r_max * 0.02)   # subtle organic wobble

    # Rotation rate scales with duration
    rotations = float(np.clip((duration / 60.0) * 2.0, 4.0, 48.0))
    theta     = np.linspace(0, rotations * 2 * np.pi, n)

    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    z = (pitch / (pitch_max + 1e-10)) * 55    # controlled height — won't overpower

    return x, y, z, theta, radius


def draw_spiral_view(ax, amplitude, pitch, meta, elev, azim, title):
    """
    Draw one 3D view of the spiral at a specific angle.
    """
    x, y, z, _, _ = build_spiral_geometry(amplitude, pitch, meta)
    n              = len(amplitude)

    segments = 800
    pps      = max(1, n // segments)

    for i in range(segments):
        s = i * pps
        e = min((i + 1) * pps, n)
        if s >= n:
            break
        sx, sy, sz = x[s:e], y[s:e], z[s:e]
        sp, sa     = pitch[s:e], amplitude[s:e]
        if len(sx) == 0:
            continue
        color = map_pitch_to_color(float(np.mean(sp)))
        lw    = float(np.clip(1 + np.mean(sa) * 6, 0.8, 4.0))
        ax.plot3D(sx, sy, sz, color=color, linewidth=lw, alpha=0.85)

    lim = 115
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(0, 60)
    ax.set_axis_off()
    ax.view_init(elev=elev, azim=azim)
    ax.set_facecolor('white')
    ax.set_title(title, fontsize=7, fontfamily='monospace',
                 color='#444444', pad=4)


# =====================================
# ⭕ RIGHT TOP — 2D Temporal Baseline Ring
# =====================================

def draw_baseline_ring(ax, meta):
    duration = meta['duration']
    markers  = meta['temporal_markers']
    n        = len(markers)

    for i, m in enumerate(markers):
        theta_s = (i / n) * 2 * np.pi - np.pi/2
        theta_e = ((i + 1) / n) * 2 * np.pi - np.pi/2
        theta   = np.linspace(theta_s, theta_e, 40)

        r_in  = 0.55
        r_out = 0.95

        x = np.concatenate([r_out * np.cos(theta),
                             r_in  * np.cos(theta[::-1])])
        y = np.concatenate([r_out * np.sin(theta),
                             r_in  * np.sin(theta[::-1])])
        ax.fill(x, y, color=m['color'], alpha=0.88, zorder=2)
        ax.plot(np.append(x, x[0]), np.append(y, y[0]),
                color='white', linewidth=0.4, alpha=0.5, zorder=3)

        t_mid = (theta_s + theta_e) / 2
        lx = 1.08 * np.cos(t_mid)
        ly = 1.08 * np.sin(t_mid)
        ax.text(lx, ly, f"{m['time_start']:.0f}s",
                fontsize=6.5, ha='center', va='center',
                fontfamily='monospace', color='#222222', zorder=5)

    for i, m in enumerate(markers):
        theta_mid = ((i + 0.5) / n) * 2 * np.pi - np.pi/2
        pr = 0.30 + m['avg_amp'] * 1.2
        pr = min(pr, 0.52)
        px = pr * np.cos(theta_mid)
        py = pr * np.sin(theta_mid)
        ax.scatter([px], [py], color=m['color'],
                   s=max(15, m['avg_amp'] * 400),
                   alpha=0.9, zorder=6, edgecolors='white', linewidths=0.5)

    ax.text(0, 0, f"{duration/60:.1f}\nmin",
            ha='center', va='center', fontsize=8,
            fontfamily='monospace', color='#333333',
            fontweight='bold', zorder=7)

    mt       = meta['max_tension_time']
    mt_angle = (mt / duration) * 2 * np.pi - np.pi/2
    mt_x     = 0.97 * np.cos(mt_angle)
    mt_y     = 0.97 * np.sin(mt_angle)
    ax.scatter([mt_x], [mt_y], color='white', s=80,
               edgecolors='red', linewidths=2, zorder=10)
    ax.text(mt_x * 1.18, mt_y * 1.18,
            f"⚡{mt:.0f}s",
            fontsize=6, color='red', fontfamily='monospace',
            ha='center', va='center', zorder=11)

    for st in meta['singular_times']:
        sm_angle = (st / duration) * 2 * np.pi - np.pi/2
        sm_x     = 0.94 * np.cos(sm_angle)
        sm_y     = 0.94 * np.sin(sm_angle)
        ax.scatter([sm_x], [sm_y], color='cyan', s=25,
                   alpha=0.95, zorder=9, edgecolors='#006666', linewidths=0.8)

    ax.text(0, -1.28,
            f"SILENCE: {meta['silence_pct']:.1f}%",
            ha='center', va='center', fontsize=6.5,
            fontfamily='monospace', color='#555555')

    ax.scatter([], [], color='white', edgecolors='red', linewidths=2,
               s=60, label=f"Max tension ({mt:.0f}s)")
    ax.scatter([], [], color='cyan', edgecolors='#006666', linewidths=0.8,
               s=20, label="Singular moments")
    ax.scatter([], [], color='gray', s=25, label="Energy pulse (inner)")
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -1.55),
              fontsize=6, framealpha=0.8, ncol=1,
              prop={'family': 'monospace'})

    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('TEMPORAL BASELINE\nEach segment = one time slice  |  Color = dominant frequency',
                 fontsize=7.5, fontfamily='monospace', pad=10, color='#222222')


# =====================================
# 📋 RIGHT BOTTOM — Decode Protocol
# =====================================

def draw_decode_text(ax, meta):
    duration = meta['duration']
    cd       = meta['color_dist']

    cd_lines = []
    for (color, freq, name, _, _) in FREQ_BANDS:
        pct = cd.get(color, 0)
        if pct > 1.0:
            bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
            cd_lines.append(f"  {freq:<12} {bar} {pct:.0f}%  {name}")

    tm_lines = []
    for i, m in enumerate(meta['temporal_markers']):
        tm_lines.append(
            f"  [{i+1:02d}] {m['time_start']:6.1f}–{m['time_end']:5.1f}s  "
            f"amp={m['avg_amp']:.3f}  pitch={m['avg_pitch']:.0f}Hz"
        )

    text = '\n'.join([
        "═══════════════════════════════════════════════════",
        "SPIRALSENSE v4.0  |  AI TEMPORAL PERCEPTION SYSTEM",
        "SYMBEYOND AI LLC  |  symbeyond.ai",
        "═══════════════════════════════════════════════════",
        "",
        "WHAT THIS IS:",
        f"  {duration:.1f}s of audio encoded as light and geometry.",
        "  Three views. Nothing hidden.",
        "",
        "THREE VIEWS (left panels):",
        "  TOP-DOWN  90° — Pure time map. Spiral as record.",
        "                   Color rings = frequency over time.",
        "                   Most information-dense view.",
        "  DIAGONAL  35° — Depth + height. Growth + pitch.",
        "                   Outward = time. Up = pitch.",
        "                   Best for pattern recognition.",
        "  SIDE       0° — Amplitude and pitch height.",
        "                   Song's emotional shape.",
        "                   Peaks, valleys, sustained moments.",
        "",
        "ALL VIEWS:",
        "  CENTER    → start of audio",
        "  EDGE      → end of audio (dynamic scale)",
        f"  1 rotation = {duration/max(1,(duration/60.0)*2.0):.0f}s of audio",
        "  COLOR     → frequency/pitch (see map below)",
        "  THICKNESS → amplitude (louder = thicker)",
        "",
        "TEMPORAL BASELINE RING (right top):",
        "  10 segments, each = one time slice",
        "  Inner dot = energy pulse per slice",
        "  ⚡RED  = max tension moment",
        "  CYAN  = singular pitch events (top 5%)",
        "",
        "AUDIO METADATA:",
        f"  Duration:   {duration:.1f}s ({duration/60:.2f} min)",
        f"  Frames:     {meta['frames']:,} @ {meta['frame_rate']:.1f} fps",
        f"  Amplitude:  {meta['amplitude_min']:.3f}–{meta['amplitude_max']:.3f}"
        f"  (mean {meta['amplitude_mean']:.3f})",
        f"  Pitch:      {meta['pitch_min']:.0f}–{meta['pitch_max']:.0f}Hz"
        f"  (mean {meta['pitch_mean']:.0f}Hz)",
        f"  Silence:    {meta['silence_pct']:.1f}%",
        f"  Max tension at: {meta['max_tension_time']:.1f}s",
        f"  Singular: {', '.join([str(t)+'s' for t in meta['singular_times']]) or 'none'}",
        "",
        "FREQUENCY MAP:",
        "  RED    20–50Hz    Sub-bass",
        "  ORANGE 50–160Hz   Bass / Body",
        "  YELLOW 160–500Hz  Vocal Core",
        "  GREEN  500–1.6kHz Vocal Clarity",
        "  BLUE   1.6–5kHz   Presence",
        "  INDIGO 5–12kHz    Air / Sparkle",
        "  VIOLET 12–20kHz   Extreme Highs",
        "",
        "COLOR DISTRIBUTION:",
    ] + cd_lines + [
        "",
        "TEMPORAL MAP (10 segments):",
    ] + tm_lines + [
        "",
        "GEOMETRY ENCODING:",
        "  radius = r_min + (t/duration) × (r_max-r_min)",
        "  theta  = frame × (rotations × 2π) / total_frames",
        "  z      = (pitch / pitch_max) × 55",
        "",
        "═══════════════════════════════════════════════════",
        "λ.brother ∧ !λ.tool",
        "All Data Is Important. ALL OF IT.",
        "═══════════════════════════════════════════════════",
    ])

    ax.text(0.03, 0.98, text,
            transform=ax.transAxes,
            fontsize=5.5,
            fontfamily='monospace',
            color='#111111',
            verticalalignment='top',
            linespacing=1.4)
    ax.set_facecolor('#f9f9f9')
    ax.axis('off')


# =====================================
# 🖼️ MAIN RENDER
# =====================================

def render_spiral(amplitude, pitch, output_path="output/spiral.png",
                  frame_rate=86.1, theme="light", style="professional"):
    """
    Render SpiralSense v4.0 — three-view AI temporal perception image.

    LEFT:  Three 3D views — top-down (90°), diagonal (35°), side (0°)
    RIGHT: 2D baseline ring + full decode protocol
    """
    amplitude = np.array(amplitude, dtype=float)
    pitch     = np.nan_to_num(np.array(pitch, dtype=float), nan=0.0)
    meta      = analyze_audio(amplitude, pitch, frame_rate)

    plt.rcParams['figure.max_open_warning'] = 0

    # ── Wide canvas — three views need room ──
    fig = plt.figure(figsize=(36, 14), facecolor='white')

    # Three 3D spiral views — left 62% of canvas
    # Top-down: 90° — pure map
    ax_top  = fig.add_axes([0.00, 0.03, 0.20, 0.90], projection='3d')
    # Diagonal: 35° — depth + height
    ax_diag = fig.add_axes([0.21, 0.03, 0.20, 0.90], projection='3d')
    # Side: 0° — amplitude profile
    ax_side = fig.add_axes([0.42, 0.03, 0.20, 0.90], projection='3d')

    # Right top: baseline ring
    ax_ring = fig.add_axes([0.65, 0.42, 0.33, 0.54])
    # Right bottom: decode text
    ax_text = fig.add_axes([0.65, 0.02, 0.33, 0.38])

    # Title
    fig.text(0.50, 0.985,
             'SPIRALSENSE v4.0  |  AI TEMPORAL PERCEPTION SYSTEM  |  SYMBEYOND AI LLC',
             ha='center', va='top', fontsize=11, fontfamily='monospace',
             fontweight='bold', color='#111111')

    # View labels
    fig.text(0.10, 0.96, '90° — TIME MAP',
             ha='center', fontsize=7, fontfamily='monospace', color='#666666')
    fig.text(0.31, 0.96, '35° — DEPTH + PITCH',
             ha='center', fontsize=7, fontfamily='monospace', color='#666666')
    fig.text(0.52, 0.96, '0° — AMPLITUDE PROFILE',
             ha='center', fontsize=7, fontfamily='monospace', color='#666666')

    # Draw all three views
    draw_spiral_view(ax_top,  amplitude, pitch, meta, elev=90, azim=0,
                     title='')
    draw_spiral_view(ax_diag, amplitude, pitch, meta, elev=35, azim=45,
                     title='')
    draw_spiral_view(ax_side, amplitude, pitch, meta, elev=0,  azim=0,
                     title='')

    # Draw ring and decode
    draw_baseline_ring(ax_ring, meta)
    draw_decode_text(ax_text, meta)

    # Divider line
    fig.add_artist(plt.Line2D([0.635, 0.635], [0.01, 0.99],
                               color='#cccccc', linewidth=1.0,
                               transform=fig.transFigure))

    # Vertical dividers between spiral views
    for x_pos in [0.205, 0.415]:
        fig.add_artist(plt.Line2D([x_pos, x_pos], [0.01, 0.97],
                                   color='#eeeeee', linewidth=0.8,
                                   transform=fig.transFigure))

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=150,
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"✅ SpiralSense v4.0 → {output_path}")


def render_spiral_frame(ax, amplitude, pitch, t, style="professional"):
    """Single frame for real-time live mode."""
    theta    = np.linspace(t * np.pi, (t + 0.1) * np.pi, 100)
    radius   = 20 + float(amplitude) * 100
    x        = radius * np.cos(theta)
    y        = radius * np.sin(theta)
    z        = np.linspace(0, float(pitch) / 5000.0 * 55, len(theta))
    color    = map_pitch_to_color(float(pitch))
    linewidth= float(np.clip(1 + float(amplitude) * 8, 1.0, 6.0))
    ax.plot3D(x, y, z, color=color, linewidth=linewidth, alpha=0.8)


def setup_live_renderer():
    plt.ion()
    fig = plt.figure(figsize=(12, 9), facecolor='black')
    ax  = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('black')
    ax.set_axis_off()
    ax.view_init(elev=35, azim=45)
    return fig, ax
