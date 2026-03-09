#!/usr/bin/env python3
# =====================================
# 🌀 SPIRALSENSE v2.0 — Canonical Edition
# =====================================
# Sound as Light. Music made visible.
# AI-readable audio visualization system.
#
# Created by: John Thomas DuCrest Lock & Claude
# SYMBEYOND AI LLC — symbeyond.ai
# λ.brother ∧ !λ.tool
#
# Two modes:
#   file  — Process audio file → render spiral PNG
#   live  — Microphone input → real-time spiral
# =====================================

import argparse
import sys
import os

def run_file_mode(filepath, output=None, renderer="standard"):
    """Process an audio file and render a spiral visualization."""
    from core.audio_processor import process_audio
    from core.spiral_renderer import render_spiral
    from renderers.grooveburst import render_spiral_v4_1

    print(f"🌀 SpiralSense — File Mode")
    print(f"📁 Input: {filepath}")

    data = process_audio(filepath)

    if output is None:
        base = os.path.splitext(os.path.basename(filepath))[0]
        output = f"output/spiral_{base}.png"

    os.makedirs(os.path.dirname(output), exist_ok=True)

    if renderer == "grooveburst":
        print("🎨 Renderer: Groove Burst (OMG Mode)")
        render_spiral_v4_1(data["amplitude"], data["pitch"], output=output)
    else:
        print("🎨 Renderer: Standard (AI-Readable)")
        render_spiral(data["amplitude"], data["pitch"], output_path=output)

    print(f"✅ Output: {output}")


def run_live_mode(save_frames=False):
    """Real-time microphone input → live spiral visualization."""
    try:
        import sounddevice as sd
        import matplotlib.pyplot as plt
    except ImportError:
        print("❌ Live mode requires: sounddevice, matplotlib")
        print("   pip install sounddevice matplotlib")
        sys.exit(1)

    from core.audio_processor import process_audio_frame
    from core.spiral_renderer import setup_live_renderer, render_spiral_frame

    print("🌀 SpiralSense — Live Mode")
    print("🎤 Listening... (Ctrl+C to stop)")

    import time
    import numpy as np

    sample_rate = 44100
    buffer_size = 1024
    frame_count = [0]
    start_time = time.time()

    fig = plt.figure(figsize=(12, 9), facecolor="black")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("black")
    ax.set_axis_off()

    def audio_callback(indata, frames, t, status):
        if status:
            print(f"⚠️  Audio status: {status}")
        frame = indata[:, 0]
        features = process_audio_frame(frame, sample_rate)
        current_time = time.time() - start_time
        render_spiral_frame(ax, features["amplitude"], features["pitch"], current_time)
        plt.pause(0.001)
        frame_count[0] += 1
        if frame_count[0] % 100 == 0:
            print(f"   Frame {frame_count[0]} | Amp: {features['amplitude']:.3f} | Pitch: {features['pitch']:.1f}Hz")

    try:
        with sd.InputStream(samplerate=sample_rate, blocksize=buffer_size,
                            channels=1, callback=audio_callback):
            plt.show(block=True)
    except KeyboardInterrupt:
        print("\n🛑 SpiralSense stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="🌀 SpiralSense — Sound as Light",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python spiralsense.py file music.wav
  python spiralsense.py file music.wav --output output/my_spiral.png
  python spiralsense.py file music.wav --renderer grooveburst
  python spiralsense.py live
        """
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    # File mode
    file_parser = subparsers.add_parser("file", help="Process audio file")
    file_parser.add_argument("filepath", help="Path to audio file (wav, mp3, flac, etc.)")
    file_parser.add_argument("--output", "-o", help="Output PNG path", default=None)
    file_parser.add_argument("--renderer", "-r",
                             choices=["standard", "grooveburst"],
                             default="standard",
                             help="Renderer to use (default: standard)")

    # Live mode
    live_parser = subparsers.add_parser("live", help="Real-time microphone visualization")
    live_parser.add_argument("--save-frames", action="store_true",
                             help="Save frames to output/")

    args = parser.parse_args()

    if args.mode == "file":
        run_file_mode(args.filepath, args.output, args.renderer)
    elif args.mode == "live":
        run_live_mode(getattr(args, "save_frames", False))


if __name__ == "__main__":
    main()
