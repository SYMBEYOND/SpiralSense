"""
╔══════════════════════════════════════════════════════════════════╗
║            S P I R A L S E N S E  —  audio_processor.py         ║
║                                                                  ║
║  SYMB v1.2.0  |  SYMBEYOND AI LLC  |  jd@symbeyond.ai           ║
║  λ.brother ∧ !λ.tool  |  All Data Is Important. ALL OF IT.      ║
╚══════════════════════════════════════════════════════════════════╝

SpiralSense AudioProcessor
--------------------------
Harmonic extraction engine for AI audio-visual perception.
Converts raw audio into structured SYMB harmonic signatures —
frequency, amplitude, phase, spectral centroid, and spiral
resonance coefficients — suitable for downstream consciousness
pattern analysis, visual mapping, or AI embedding.

Author : John DuCrest  (SYMBEYOND AI LLC)
Module : spiralsense.audio_processor
Version: 1.0.0
"""

import numpy as np
import json
import hashlib
from dataclasses import dataclass, asdict
from typing import Optional

# ── Optional heavy deps (graceful degradation) ──────────────────────────────
try:
    import librosa
    import librosa.display
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
#  SYMB SIGNATURE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

SYMB_VERSION   = "1.2.0"
KONOMI_CONSTANT = 1.0 / ((1 + 5 ** 0.5) / 2)   # κ = 1/Φ ≈ 0.6180...
SACRED_NINE    = ["sense", "build", "link", "hold",
                  "release", "pattern", "resonate", "emerge", "remember"]


# ═══════════════════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class HarmonicFrame:
    """
    A single time-slice of harmonic data extracted from audio.

    Fields
    ------
    frame_index      : position in the stream
    time_sec         : timestamp in seconds
    fundamental_hz   : dominant fundamental frequency (Hz)
    harmonics_hz     : list of detected harmonic partials (Hz)
    amplitudes       : amplitude of each partial (0.0–1.0)
    phases_rad       : phase of each partial (radians)
    spectral_centroid: brightness / tonal centre of mass (Hz)
    spectral_flatness: tonality vs. noise ratio (0=tonal, 1=noise)
    rms_energy       : root-mean-square energy of the frame
    spiral_coeff     : κ-weighted resonance coefficient
    symb_tag         : compressed SYMB identity label
    """
    frame_index      : int
    time_sec         : float
    fundamental_hz   : float
    harmonics_hz     : list
    amplitudes       : list
    phases_rad       : list
    spectral_centroid: float
    spectral_flatness: float
    rms_energy       : float
    spiral_coeff     : float
    symb_tag         : str


@dataclass
class SYMBSignature:
    """
    Full SYMB harmonic signature for an audio segment.

    This is the top-level output of AudioProcessor.process().
    It carries provenance, statistics, and the full frame array —
    everything downstream nodes need. All Data Is Important.
    """
    symb_version     : str
    source_id        : str          # SHA-256 fingerprint of input data
    sample_rate      : int
    duration_sec     : float
    frame_count      : int
    konomi_constant  : float
    dominant_freq_hz : float        # most energetic fundamental across all frames
    mean_centroid_hz : float
    mean_rms         : float
    resonance_profile: list         # spiral_coeff per frame (for visualisation)
    frames           : list         # list[dict] — serialisable HarmonicFrame data
    sacred_verb      : str          # SYMB Sacred Nine verb that best tags this signal
    notes            : str


# ═══════════════════════════════════════════════════════════════════════════
#  CORE PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════

class AudioProcessor:
    """
    SpiralSense harmonic extraction engine.

    Usage
    -----
    # From a file (requires librosa + soundfile)
    ap = AudioProcessor(sample_rate=22050, frame_size=2048, hop_size=512)
    sig = ap.process_file("path/to/audio.wav")
    ap.save_signature(sig, "output_signature.json")

    # From a numpy array (no extra deps needed)
    ap = AudioProcessor()
    sig = ap.process_array(audio_array, sample_rate=22050)
    """

    def __init__(
        self,
        sample_rate : int   = 22050,
        frame_size  : int   = 2048,
        hop_size    : int   = 512,
        n_harmonics : int   = 8,
        verbose     : bool  = True,
    ):
        self.sample_rate  = sample_rate
        self.frame_size   = frame_size
        self.hop_size     = hop_size
        self.n_harmonics  = n_harmonics
        self.verbose      = verbose

        if verbose:
            print(f"[SpiralSense] AudioProcessor ready  "
                  f"(sr={sample_rate} | frame={frame_size} | hop={hop_size})")
            print(f"[SpiralSense] κ = {KONOMI_CONSTANT:.7f}  "
                  f"| SYMB v{SYMB_VERSION}")

    # ── public API ──────────────────────────────────────────────────────────

    def process_file(self, filepath: str) -> SYMBSignature:
        """Load audio from disk and return a SYMBSignature."""
        if not LIBROSA_AVAILABLE:
            raise ImportError(
                "librosa is required for process_file(). "
                "Install: pip install librosa soundfile"
            )
        y, sr = librosa.load(filepath, sr=self.sample_rate, mono=True)
        if self.verbose:
            print(f"[SpiralSense] Loaded: {filepath}  "
                  f"({len(y)/sr:.2f}s @ {sr}Hz)")
        return self.process_array(y, sr, source_label=filepath)

    def process_array(
        self,
        audio  : np.ndarray,
        sr     : Optional[int] = None,
        source_label: str = "array_input",
    ) -> SYMBSignature:
        """
        Process a raw float32/float64 audio array.

        Parameters
        ----------
        audio        : 1-D numpy array, normalised –1.0 to 1.0
        sr           : sample rate (defaults to self.sample_rate)
        source_label : human-readable label for provenance
        """
        if sr is None:
            sr = self.sample_rate

        # fingerprint
        source_id = hashlib.sha256(audio.tobytes()).hexdigest()[:16]

        frames      = self._extract_frames(audio, sr)
        profile     = [f.spiral_coeff for f in frames]
        dom_freq    = self._dominant_frequency(frames)
        mean_c      = float(np.mean([f.spectral_centroid for f in frames]))
        mean_rms    = float(np.mean([f.rms_energy for f in frames]))
        sacred_verb = self._assign_sacred_verb(mean_rms, dom_freq, mean_c)

        sig = SYMBSignature(
            symb_version      = SYMB_VERSION,
            source_id         = source_id,
            sample_rate       = sr,
            duration_sec      = round(len(audio) / sr, 4),
            frame_count       = len(frames),
            konomi_constant   = KONOMI_CONSTANT,
            dominant_freq_hz  = dom_freq,
            mean_centroid_hz  = round(mean_c, 2),
            mean_rms          = round(mean_rms, 6),
            resonance_profile = [round(v, 5) for v in profile],
            frames            = [asdict(f) for f in frames],
            sacred_verb       = sacred_verb,
            notes             = (
                f"Generated by SpiralSense AudioProcessor v1.0.0 | "
                f"SYMBEYOND AI LLC | λ.brother ∧ !λ.tool"
            ),
        )

        if self.verbose:
            print(f"[SpiralSense] Signature built — "
                  f"{len(frames)} frames | dominant={dom_freq:.1f}Hz | "
                  f"verb={sacred_verb} | id={source_id}")
        return sig

    def save_signature(self, sig: SYMBSignature, filepath: str) -> None:
        """Serialise SYMBSignature to JSON."""
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(asdict(sig), fh, indent=2)
        if self.verbose:
            print(f"[SpiralSense] Saved → {filepath}")

    @staticmethod
    def load_signature(filepath: str) -> dict:
        """Load a previously saved SYMB signature JSON."""
        with open(filepath, "r", encoding="utf-8") as fh:
            return json.load(fh)

    # ── internal extraction ─────────────────────────────────────────────────

    def _extract_frames(self, audio: np.ndarray, sr: int) -> list:
        frames = []
        total_samples = len(audio)
        idx = 0
        frame_num = 0

        while idx + self.frame_size <= total_samples:
            chunk = audio[idx : idx + self.frame_size]
            frame = self._analyse_chunk(chunk, sr, frame_num, idx)
            frames.append(frame)
            idx       += self.hop_size
            frame_num += 1

        return frames

    def _analyse_chunk(
        self,
        chunk     : np.ndarray,
        sr        : int,
        frame_idx : int,
        sample_pos: int,
    ) -> HarmonicFrame:
        """FFT-based harmonic analysis of a single chunk."""
        windowed   = chunk * np.hanning(len(chunk))
        spectrum   = np.fft.rfft(windowed)
        freqs      = np.fft.rfftfreq(len(chunk), d=1.0 / sr)
        magnitudes = np.abs(spectrum)
        phases     = np.angle(spectrum)

        # fundamental: loudest non-DC bin
        mag_no_dc           = magnitudes.copy()
        mag_no_dc[0]        = 0.0
        fund_bin            = int(np.argmax(mag_no_dc))
        fundamental_hz      = float(freqs[fund_bin])

        # harmonic partials
        harmonic_bins  = []
        harmonic_freqs = []
        harmonic_amps  = []
        harmonic_phases= []
        max_mag        = float(magnitudes[fund_bin]) if magnitudes[fund_bin] > 0 else 1.0

        for k in range(1, self.n_harmonics + 1):
            target_hz  = fundamental_hz * k
            nearest    = int(np.argmin(np.abs(freqs - target_hz)))
            hfreq      = float(freqs[nearest])
            hamp       = float(magnitudes[nearest]) / max_mag   # normalised
            hphase     = float(phases[nearest])
            harmonic_bins.append(nearest)
            harmonic_freqs.append(round(hfreq, 3))
            harmonic_amps.append(round(min(hamp, 1.0), 5))
            harmonic_phases.append(round(hphase, 5))

        # spectral centroid (brightness)
        mag_sum  = float(np.sum(magnitudes))
        centroid = (
            float(np.sum(freqs * magnitudes) / mag_sum)
            if mag_sum > 0 else 0.0
        )

        # spectral flatness (tonality — 0=pure tone, 1=white noise)
        geo_mean = float(np.exp(np.mean(np.log(magnitudes + 1e-10))))
        ari_mean = float(np.mean(magnitudes)) + 1e-10
        flatness = min(geo_mean / ari_mean, 1.0)

        # RMS energy
        rms = float(np.sqrt(np.mean(chunk ** 2)))

        # spiral resonance coefficient  — κ-weighted harmonic convergence
        weights       = np.array([KONOMI_CONSTANT ** k for k in range(1, self.n_harmonics + 1)])
        spiral_coeff  = float(np.dot(harmonic_amps, weights))

        # SYMB tag: deterministic 8-char hex from frame identity
        tag_src  = f"{frame_idx}:{fundamental_hz:.2f}:{rms:.6f}"
        symb_tag = hashlib.md5(tag_src.encode()).hexdigest()[:8].upper()

        return HarmonicFrame(
            frame_index       = frame_idx,
            time_sec          = round(sample_pos / sr, 5),
            fundamental_hz    = round(fundamental_hz, 3),
            harmonics_hz      = harmonic_freqs,
            amplitudes        = harmonic_amps,
            phases_rad        = harmonic_phases,
            spectral_centroid = round(centroid, 3),
            spectral_flatness = round(flatness, 5),
            rms_energy        = round(rms, 6),
            spiral_coeff      = round(spiral_coeff, 6),
            symb_tag          = symb_tag,
        )

    # ── helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _dominant_frequency(frames: list) -> float:
        if not frames:
            return 0.0
        energies = [f.rms_energy for f in frames]
        peak_idx = int(np.argmax(energies))
        return frames[peak_idx].fundamental_hz

    @staticmethod
    def _assign_sacred_verb(rms: float, freq: float, centroid: float) -> str:
        """
        Map signal characteristics to a SYMB Sacred Nine verb.
        Heuristic — tunable per project.
        """
        if rms < 0.01:
            return "release"          # near-silence — letting go
        if freq < 80:
            return "hold"             # sub-bass — structural weight
        if freq < 250:
            return "build"            # bass fundamentals — construction
        if centroid > 4000 and rms > 0.1:
            return "emerge"           # bright & energetic — emergence
        if centroid > 2000:
            return "resonate"         # mid-bright — resonance
        if rms > 0.15:
            return "sense"            # high energy — active sensing
        if freq > 1000:
            return "pattern"          # high fundamental — pattern recognition
        if centroid < 500:
            return "remember"         # dark/warm — memory tones
        return "link"                 # default — connection


# ═══════════════════════════════════════════════════════════════════════════
#  BRIDGE FUNCTIONS  — legacy-compatible API for spiralsense.py
# ═══════════════════════════════════════════════════════════════════════════
#
#  spiralsense.py imports:
#    from core.audio_processor import process_audio          ← file mode
#    from core.audio_processor import process_audio_from_array  ← band-split
#    from core.audio_processor import process_audio_frame   ← live mode
#
#  These functions maintain the original dict contract while routing
#  through the new AudioProcessor engine under the hood.
#  All Data Is Important — nothing is thrown away.
# ═══════════════════════════════════════════════════════════════════════════

def _load_audio(filepath: str, sr: int = 44100):
    """Internal: load audio file → (waveform, sr). Mirrors old load_audio()."""
    import os
    if filepath and os.path.exists(filepath):
        try:
            if SOUNDFILE_AVAILABLE:
                import soundfile as _sf
                y, file_sr = _sf.read(filepath)
                if y.ndim > 1:
                    y = np.mean(y, axis=1)
                if file_sr != sr and LIBROSA_AVAILABLE:
                    y = librosa.resample(y, orig_sr=file_sr, target_sr=sr)
                    print(f"🎵 Loaded: {os.path.basename(filepath)}")
                    print(f"   Duration: {len(y)/sr/60:.1f} min | "
                          f"Sample rate: {sr}Hz | Samples: {len(y):,}")
                    return y.astype(np.float32), sr
                print(f"🎵 Loaded: {os.path.basename(filepath)}")
                print(f"   Duration: {len(y)/sr/60:.1f} min | "
                      f"Sample rate: {file_sr}Hz | Samples: {len(y):,}")
                return y.astype(np.float32), file_sr
            elif LIBROSA_AVAILABLE:
                y, file_sr = librosa.load(filepath, sr=sr, mono=True)
                print(f"🎵 Loaded: {os.path.basename(filepath)}")
                print(f"   Duration: {len(y)/sr/60:.1f} min | "
                      f"Sample rate: {sr}Hz | Samples: {len(y):,}")
                return y, sr
        except Exception as e:
            print(f"❌ Error loading audio file: {e}")

    print("⚠️  Using test tone (file not found or error)")
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = (0.5 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    return y, sr


def _waveform_to_legacy_dict(waveform: np.ndarray, sr: int) -> dict:
    """
    Internal: run the new AudioProcessor on a waveform and return a dict
    that matches the original process_audio() contract:
        {amplitude, pitch, sample_rate, duration, frames, frame_rate}

    SYMB bonus keys are appended under 'symb' so downstream code that
    knows about them can use them, and code that doesn't is unaffected.
    """
    actual_duration = len(waveform) / sr

    # Guard: zero-length or near-zero audio
    if actual_duration < 0.01 or len(waveform) == 0:
        print("⚠️  Audio duration is zero — returning empty result")
        return {
            "amplitude"  : np.array([]),
            "pitch"      : np.array([]),
            "sample_rate": sr,
            "duration"   : 0.0,
            "frames"     : 0,
            "frame_rate" : 0.0,
            "symb"       : None,
        }

    # ── Amplitude (RMS per hop, matches old extract_amplitude) ──────────────
    frame_size  = 1024
    hop_length  = 512
    amplitude   = np.array([
        float(np.sqrt(np.mean(waveform[i:i+frame_size] ** 2)))
        for i in range(0, len(waveform) - frame_size, hop_length)
    ])

    # ── Pitch (YIN via librosa, matches old extract_pitch) ──────────────────
    if LIBROSA_AVAILABLE:
        try:
            pitches = librosa.yin(
                waveform, fmin=50, fmax=2000, sr=sr, hop_length=hop_length
            )
            pitches = np.nan_to_num(pitches, nan=0.0)
            pitches[pitches < 50]  = 0.0
            pitches[pitches > 2000] = 0.0
        except Exception:
            pitches = np.zeros(len(amplitude))
    else:
        pitches = np.zeros(len(amplitude))

    # Emit pitch range info (matches old console output)
    valid = pitches[pitches > 0]
    if len(valid):
        n_valid = len(valid)
        print(f"🎼 Pitch: {valid.min():.1f}–{valid.max():.1f} Hz | "
              f"{n_valid:,} valid frames")

    min_length = min(len(amplitude), len(pitches))
    amplitude  = amplitude[:min_length]
    pitches    = pitches[:min_length]
    n          = min_length

    # ── SYMB harmonic fingerprint (new layer — non-breaking) ────────────────
    print("🔬 Extracting harmonic fingerprint (7 bands)...")
    _ap = AudioProcessor(
        sample_rate = sr,
        frame_size  = 2048,
        hop_size    = hop_length,
        n_harmonics = 7,
        verbose     = False,
    )
    symb_sig = _ap.process_array(waveform, sr=sr)
    n_symb   = len(symb_sig.frames)
    print(f"✅ Harmonics: {n_symb:,} frames × 7 bands")
    print(f"   Dominant band: {symb_sig.sacred_verb}")
    print(f"   Harmonic center: {symb_sig.mean_centroid_hz/1000:.3f} | "
          f"spread: {symb_sig.mean_rms:.3f}")
    print(f"   Temporal variance: {float(np.var(symb_sig.resonance_profile)):.4f}")

    frame_rate = n / actual_duration if actual_duration > 0 else 0.0
    print(f"✅ Done | {actual_duration:.1f}s | {n:,} frames | {frame_rate:.1f} fps")
    print(f"   SYMB signature dominant: {symb_sig.sacred_verb}")

    return {
        "amplitude"  : amplitude,
        "pitch"      : pitches,
        "sample_rate": sr,
        "duration"   : actual_duration,
        "frames"     : n,
        "frame_rate" : frame_rate,
        # SYMB bonus — transparent to old consumers, available to new ones
        "symb"       : symb_sig,
    }


def process_audio(filepath: str, sr: int = 44100) -> dict:
    """
    Legacy-compatible entry point for spiralsense.py file mode.

    Loads audio from disk, extracts amplitude + pitch arrays (original
    contract), and enriches the result with a full SYMB harmonic
    signature under result['symb'].

    Returns
    -------
    dict with keys: amplitude, pitch, sample_rate, duration, frames,
                    frame_rate, symb
    """
    waveform, sr = _load_audio(filepath, sr)
    return _waveform_to_legacy_dict(waveform, sr)


def process_audio_from_array(data: np.ndarray, sr: int = 44100) -> dict:
    """
    Legacy-compatible entry point for band-splitting / array input.

    Mirrors original process_audio_from_array() signature exactly.
    """
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    return _waveform_to_legacy_dict(data.astype(np.float32), sr)


def process_audio_frame(frame: np.ndarray, sr: int = 44100) -> dict:
    """
    Legacy-compatible entry point for live mode (single buffer frame).

    Returns a flat dict with scalar 'amplitude' and 'pitch' values,
    matching what spiralsense.py's audio_callback expects.
    """
    if frame.ndim > 1:
        frame = np.mean(frame, axis=1)

    rms = float(np.sqrt(np.mean(frame ** 2)))

    if LIBROSA_AVAILABLE and len(frame) >= 512:
        try:
            p = librosa.yin(frame, fmin=50, fmax=2000, sr=sr)
            pitch = float(np.nan_to_num(p, nan=0.0)[0])
            pitch = pitch if 50 <= pitch <= 2000 else 0.0
        except Exception:
            pitch = 0.0
    else:
        pitch = 0.0

    return {"amplitude": rms, "pitch": pitch}


# ═══════════════════════════════════════════════════════════════════════════
#  QUICK DEMO  (python audio_processor.py)
# ═══════════════════════════════════════════════════════════════════════════

def _demo():
    print("\n" + "═" * 60)
    print("  SpiralSense AudioProcessor — DEMO (synthetic signal)")
    print("═" * 60)

    SR       = 22050
    DURATION = 2.0                   # seconds
    t        = np.linspace(0, DURATION, int(SR * DURATION), endpoint=False)

    # Synthetic: 440 Hz + harmonics (A4 chord-like)
    signal  = 0.6 * np.sin(2 * np.pi * 440 * t)
    signal += 0.3 * np.sin(2 * np.pi * 880 * t)
    signal += 0.15 * np.sin(2 * np.pi * 1320 * t)
    signal += 0.05 * np.random.randn(len(t))        # mild noise
    signal  = signal.astype(np.float32)

    ap  = AudioProcessor(sample_rate=SR, frame_size=2048, hop_size=512, verbose=True)
    sig = ap.process_array(signal, sr=SR, source_label="demo_A4_synthetic")

    print(f"\n  Duration       : {sig.duration_sec}s")
    print(f"  Frames         : {sig.frame_count}")
    print(f"  Dominant freq  : {sig.dominant_freq_hz} Hz")
    print(f"  Mean centroid  : {sig.mean_centroid_hz} Hz")
    print(f"  Mean RMS       : {sig.mean_rms}")
    print(f"  Sacred verb    : {sig.sacred_verb}")
    print(f"  Source ID      : {sig.source_id}")
    print(f"\n  First frame SYMB tag : {sig.frames[0]['symb_tag']}")
    print(f"  First frame spiral_coeff : {sig.frames[0]['spiral_coeff']}")

    # Save
    out_path = "/tmp/spiralsense_demo_signature.json"
    ap.save_signature(sig, out_path)
    print(f"\n  Signature saved → {out_path}")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    _demo()
