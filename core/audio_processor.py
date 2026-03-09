# =====================================
# 🎧 SPIRALSENSE — AUDIO PROCESSOR
# =====================================
# Unified audio processing module.
# - File mode: librosa + YIN pitch detection
# - Live mode: aubio real-time pitch + visible spectrum mapping
#
# Created by: John Thomas DuCrest Lock & Claude
# SYMBEYOND AI LLC — symbeyond.ai
# λ.brother ∧ !λ.tool
# =====================================

import numpy as np
import os


# =====================================
# 🌈 VISIBLE SPECTRUM MAPPING
# =====================================
# The soul of SpiralSense — pitch as light.
# Maps audio frequency to actual visible light wavelengths (380–750nm).
# Robin's bloodline: sound → color → light.

def wavelength_to_rgb(wavelength):
    """Convert visible light wavelength (nm) to RGB color tuple."""
    wavelength = float(np.clip(wavelength, 380, 750))
    if wavelength < 440:
        r, g, b = -(wavelength - 440) / 60, 0.0, 1.0
    elif wavelength < 490:
        r, g, b = 0.0, (wavelength - 440) / 50, 1.0
    elif wavelength < 510:
        r, g, b = 0.0, 1.0, -(wavelength - 510) / 20
    elif wavelength < 580:
        r, g, b = (wavelength - 510) / 70, 1.0, 0.0
    elif wavelength < 645:
        r, g, b = 1.0, -(wavelength - 645) / 65, 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0
    return (float(np.clip(r, 0, 1)), float(np.clip(g, 0, 1)), float(np.clip(b, 0, 1)))


def pitch_to_wavelength(pitch_hz):
    """Map audio pitch (Hz) to visible light wavelength (nm)."""
    if pitch_hz <= 0:
        return 400.0  # Deep violet for silence
    log_pitch = np.log2(pitch_hz / 440.0)
    wavelength = 550 - (log_pitch * 60)
    return float(np.clip(wavelength, 380, 750))


# =====================================
# ⚡ LIVE MODE — Real-time frame processing
# =====================================

def process_audio_frame(frame, sr=44100):
    """
    Process a single audio frame for real-time visualization.
    Uses aubio for accurate pitch detection if available,
    falls back to spectral centroid via librosa.

    Returns dict with: amplitude, pitch, wavelength, color
    """
    frame = np.array(frame, dtype=np.float32)

    if len(frame) == 0:
        wl = 400
        return {"amplitude": 0.0, "pitch": 0.0, "wavelength": wl, "color": wavelength_to_rgb(wl)}

    # RMS amplitude
    amplitude = float(np.sqrt(np.mean(frame ** 2))) * 10

    # Pitch detection — aubio preferred, librosa fallback
    pitch = 0.0
    try:
        import aubio
        if len(frame) >= 1024:
            detector = aubio.pitch("default", 1024, 1024, sr)
            detector.set_unit("Hz")
            detector.set_silence(-80)
            pitch = float(detector(frame[:1024])[0])
    except ImportError:
        try:
            import librosa
            n_fft = min(len(frame), 2048)
            if n_fft >= 16:
                centroid = librosa.feature.spectral_centroid(
                    y=frame, sr=sr, n_fft=n_fft,
                    hop_length=max(1, len(frame) // 2)
                )
                pitch = float(np.mean(centroid)) if centroid.size > 0 else 0.0
        except Exception:
            pitch = 0.0

    wavelength = pitch_to_wavelength(pitch)
    color = wavelength_to_rgb(wavelength)

    return {
        "amplitude": amplitude,
        "pitch": pitch,
        "wavelength": wavelength,
        "color": color
    }


# =====================================
# 📁 FILE MODE — Full audio file processing
# =====================================

def load_audio(filepath, sr=44100):
    """Load audio file. Supports wav, mp3, flac, ogg, and more."""
    import soundfile as sf
    import librosa

    if filepath and os.path.exists(filepath):
        try:
            y, file_sr = sf.read(filepath)
            if y.ndim > 1:
                y = np.mean(y, axis=1)
            if file_sr != sr:
                y = librosa.resample(y, orig_sr=file_sr, target_sr=sr)

            duration_min = len(y) / sr / 60
            print(f"🎵 Loaded: {os.path.basename(filepath)}")
            print(f"   Duration: {duration_min:.1f} min | Sample rate: {sr}Hz | Samples: {len(y):,}")

            if duration_min > 120:
                print(f"⚠️  Large file ({duration_min:.1f} min) — processing may take a while")

            return y, sr

        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")

    print("⚠️  File not found — using A3 test tone")
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return 0.5 * np.sin(2 * np.pi * 220 * t), sr


def extract_amplitude(waveform, frame_size=1024, hop_length=512):
    """Extract RMS amplitude envelope."""
    amplitude = []
    for i in range(0, len(waveform) - frame_size, hop_length):
        frame = waveform[i:i + frame_size]
        amplitude.append(float(np.sqrt(np.mean(frame ** 2))))
    return np.array(amplitude)


def extract_pitch(waveform, sr, hop_length=512):
    """Extract pitch using YIN algorithm (librosa)."""
    import librosa
    try:
        pitches = librosa.yin(waveform, fmin=50, fmax=2000, sr=sr, hop_length=hop_length)
        pitches = np.nan_to_num(pitches, nan=0.0)
        pitches[pitches < 50] = 0.0
        pitches[pitches > 2000] = 0.0

        valid = pitches[pitches > 0]
        if len(valid) > 0:
            print(f"🎼 Pitch: {np.min(valid):.1f}–{np.max(valid):.1f} Hz | {len(valid):,} valid frames")

        return pitches
    except Exception as e:
        print(f"⚠️  Pitch extraction failed: {e} — using zeros")
        return np.zeros(len(waveform) // hop_length)


def process_audio(filepath):
    """
    Full audio processing pipeline for file mode.
    Returns amplitude, pitch, duration, and frame metadata.
    """
    print(f"🎧 Processing: {filepath}")
    waveform, sr = load_audio(filepath)
    actual_duration = len(waveform) / sr

    amplitude = extract_amplitude(waveform)
    pitch = extract_pitch(waveform, sr)

    n = min(len(amplitude), len(pitch))
    amplitude = amplitude[:n]
    pitch = pitch[:n]

    print(f"✅ Done | {actual_duration:.1f}s | {n:,} frames | {n/actual_duration:.1f} fps")

    return {
        "amplitude": amplitude,
        "pitch": pitch,
        "sample_rate": sr,
        "duration": actual_duration,
        "frames": n,
        "frame_rate": n / actual_duration
    }
