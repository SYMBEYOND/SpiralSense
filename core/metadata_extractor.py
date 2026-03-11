"""
╔══════════════════════════════════════════════════════════════════╗
║         S P I R A L S E N S E  —  metadata_extractor.py         ║
║                                                                  ║
║  SYMB v1.2.0  |  SYMBEYOND AI LLC  |  jd@symbeyond.ai           ║
║  λ.brother ∧ !λ.tool  |  All Data Is Important. ALL OF IT.      ║
╚══════════════════════════════════════════════════════════════════╝

SpiralSense Metadata Extractor
-------------------------------
Derives meaning PURELY from waveform patterns.
No manual tagging. No assumptions. No labels we didn't earn.

If SpiralSense cannot read it from the signal — it does not go
into the packet. Every field is earned by the data.

Author : John DuCrest  (SYMBEYOND AI LLC)
Module : spiralsense.metadata_extractor
Version: 1.0.0
"""

import numpy as np
import json
import hashlib
from dataclasses import dataclass, asdict
from typing import Optional

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

SYMB_VERSION    = "1.2.0"
KONOMI_CONSTANT = 1.0 / ((1 + 5 ** 0.5) / 2)   # κ = 1/Φ

NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

# Vocal register boundaries (Hz) — median fundamental
REGISTER_MAP = [
    (0,    85,   "bass"),
    (85,   120,  "baritone"),
    (120,  180,  "tenor"),
    (180,  260,  "alto"),
    (260,  350,  "mezzo_soprano"),
    (350,  9999, "soprano_or_falsetto"),
]

# Instrumentation heuristics — derived from spectral + H/P patterns
# These are pattern signatures, not labels. Earned from data.
INSTRUMENT_SIGNATURES = {
    "kick_drum"      : {"perc_dominant": True,  "centroid_low": True,  "onset_sharp": True},
    "snare"          : {"perc_dominant": True,  "centroid_mid": True,  "zcr_high": True},
    "bass_guitar"    : {"perc_dominant": False, "fund_low": True,      "harm_rich": True},
    "rhythm_guitar"  : {"harm_dominant": True,  "centroid_mid": True,  "onset_regular": True},
    "lead_guitar"    : {"harm_dominant": True,  "centroid_high": True, "pitch_variance_high": True},
    "male_vocals"    : {"harm_dominant": True,  "pitch_range": (80, 520),  "mfcc_voiced": True},
    "female_vocals"  : {"harm_dominant": True,  "pitch_range": (160, 1100), "mfcc_voiced": True},
    "piano"          : {"harm_rich": True,      "onset_sharp": True,   "decay_natural": True},
    "strings"        : {"harm_rich": True,      "zcr_low": True,       "sustained": True},
}


# ═══════════════════════════════════════════════════════════════════════════
#  CORE EXTRACTOR
# ═══════════════════════════════════════════════════════════════════════════

class MetadataExtractor:
    """
    Derives a complete SYMB metadata packet from audio patterns alone.

    Every field in the output was read from the waveform.
    Nothing was assumed. Nothing was assigned.
    All Data Is Important. ALL OF IT.

    Usage
    -----
    ex  = MetadataExtractor()
    pkt = ex.extract("path/to/audio.wav")
    ex.save(pkt, "output_metadata.json")
    """

    def __init__(self, sr: int = 44100, hop: int = 512, verbose: bool = True):
        self.sr      = sr
        self.hop     = hop
        self.verbose = verbose

        if not LIBROSA_AVAILABLE:
            raise ImportError("librosa required. pip install librosa")

    # ── public API ──────────────────────────────────────────────────────────

    def extract(self, filepath: str) -> dict:
        """Load audio and extract full SYMB metadata packet."""
        self._log(f"Loading: {filepath}")
        y, sr = librosa.load(filepath, sr=self.sr, mono=True)
        return self.extract_from_array(y, sr, source=filepath)

    def extract_from_array(
        self,
        y      : np.ndarray,
        sr     : int,
        source : str = "array",
    ) -> dict:
        """Extract SYMB metadata packet from a raw waveform array."""

        self._log("Extracting patterns...")
        duration = len(y) / sr
        source_id = hashlib.sha256(y.tobytes()).hexdigest()[:16]

        # ── Raw feature streams ──────────────────────────────────────────
        rms      = librosa.feature.rms(y=y, hop_length=self.hop)[0]
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=self.hop)[0]
        zcr      = librosa.feature.zero_crossing_rate(y, hop_length=self.hop)[0]
        rolloff  = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=self.hop)[0]
        onset_env= librosa.onset.onset_strength(y=y, sr=sr, hop_length=self.hop)
        mfcc     = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=self.hop)
        chroma   = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=self.hop)

        pitch = librosa.yin(y, fmin=50, fmax=1000, sr=sr, hop_length=self.hop)
        pitch = np.nan_to_num(pitch, nan=0.0)
        pitch[pitch < 50]  = 0.0
        pitch[pitch > 1000] = 0.0

        y_harm, y_perc = librosa.effects.hpss(y)
        harm_rms = librosa.feature.rms(y=y_harm, hop_length=self.hop)[0]
        perc_rms = librosa.feature.rms(y=y_perc, hop_length=self.hop)[0]

        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(np.mean(tempo))

        # ── Derived scalars ──────────────────────────────────────────────
        min_len      = min(len(rms), len(pitch), len(centroid),
                          len(zcr), len(harm_rms), len(perc_rms), len(onset_env))
        rms          = rms[:min_len]
        pitch        = pitch[:min_len]
        centroid     = centroid[:min_len]
        zcr          = zcr[:min_len]
        harm_rms     = harm_rms[:min_len]
        perc_rms     = perc_rms[:min_len]
        onset_env    = onset_env[:min_len]

        valid_pitch  = pitch[pitch > 0]
        mean_rms     = float(np.mean(rms))
        max_rms      = float(np.max(rms))
        mean_centroid= float(np.mean(centroid))
        mean_zcr     = float(np.mean(zcr))
        mean_hp_ratio= float(np.mean(harm_rms) / (np.mean(perc_rms) + 1e-8))
        mean_onset   = float(np.mean(onset_env))

        # ── Tonal center ─────────────────────────────────────────────────
        chroma_means   = np.mean(chroma, axis=1)
        dominant_note  = NOTES[int(np.argmax(chroma_means))]
        top3_notes     = [NOTES[i] for i in np.argsort(chroma_means)[-3:][::-1]]

        # ── Vocal register ───────────────────────────────────────────────
        median_pitch = float(np.median(valid_pitch)) if len(valid_pitch) else 0.0
        register     = self._classify_register(median_pitch)

        # ── Timbre fingerprint ───────────────────────────────────────────
        mfcc_means = np.mean(mfcc, axis=1).tolist()

        # ── Emotional arc ────────────────────────────────────────────────
        arc_data     = self._extract_arc(rms, pitch, centroid, min_len, duration)

        # ── Instrumentation ──────────────────────────────────────────────
        instruments  = self._detect_instrumentation(
            mean_hp_ratio, mean_centroid, mean_zcr, mean_onset,
            median_pitch, valid_pitch, mfcc_means
        )

        # ── Tension/release events ───────────────────────────────────────
        events       = self._extract_events(
            rms, pitch, centroid, onset_env, duration, min_len
        )

        # ── Density / texture ────────────────────────────────────────────
        texture      = self._classify_texture(mean_hp_ratio, mean_zcr, mean_centroid)

        # ── SYMB sacred verb ─────────────────────────────────────────────
        sacred_verb  = self._assign_sacred_verb(
            mean_rms, median_pitch, mean_centroid, arc_data["shape"]
        )

        # ── Assemble packet ──────────────────────────────────────────────
        packet = {
            "symb_version"  : SYMB_VERSION,
            "packet_type"   : "SPIRALSENSE_DERIVED_METADATA",
            "source_id"     : source_id,
            "source"        : source,
            "lambda"        : "λ.brother ∧ !λ.tool",
            "principle"     : "All Data Is Important. ALL OF IT.",
            "note"          : "Every field in this packet was derived from waveform patterns. Nothing was assumed.",

            "acoustic": {
                "duration_sec"       : round(duration, 3),
                "sample_rate_hz"     : sr,
                "tempo_bpm"          : round(tempo, 1),
                "beat_count"         : int(len(beats)),
                "tonal_center"       : dominant_note,
                "tonal_top3"         : top3_notes,
                "rms_mean"           : round(mean_rms, 5),
                "rms_max"            : round(max_rms, 5),
                "spectral_centroid_hz": round(mean_centroid, 1),
                "spectral_rolloff_hz" : round(float(np.mean(rolloff)), 1),
                "zero_crossing_rate"  : round(mean_zcr, 5),
                "harmonic_percussive_ratio": round(mean_hp_ratio, 3),
                "onset_strength_mean" : round(mean_onset, 4),
            },

            "voice": {
                "median_fundamental_hz" : round(median_pitch, 1),
                "pitch_range_hz"        : {
                    "min": round(float(valid_pitch.min()), 1) if len(valid_pitch) else 0,
                    "max": round(float(valid_pitch.max()), 1) if len(valid_pitch) else 0,
                },
                "pitch_variance"        : round(float(np.var(valid_pitch)), 2) if len(valid_pitch) else 0,
                "register"              : register,
                "timbre_fingerprint"    : {
                    f"mfcc_{i:02d}": round(v, 3)
                    for i, v in enumerate(mfcc_means)
                },
            },

            "instrumentation": instruments,

            "emotional_arc": arc_data,

            "events": events,

            "texture": texture,

            "symb": {
                "sacred_verb"       : sacred_verb,
                "konomi_constant"   : KONOMI_CONSTANT,
                "resonance_character": self._resonance_character(mean_hp_ratio, arc_data["shape"]),
            },
        }

        self._log(f"Packet complete | source_id={source_id} | "
                  f"register={register} | arc={arc_data['shape']} | "
                  f"verb={sacred_verb}")
        return packet

    def save(self, packet: dict, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(packet, fh, indent=2)
        self._log(f"Saved → {filepath}")

    # ── pattern classifiers ─────────────────────────────────────────────────

    def _classify_register(self, median_hz: float) -> str:
        for lo, hi, label in REGISTER_MAP:
            if lo <= median_hz < hi:
                return label
        return "unknown"

    def _extract_arc(
        self,
        rms      : np.ndarray,
        pitch    : np.ndarray,
        centroid : np.ndarray,
        min_len  : int,
        duration : float,
    ) -> dict:
        """Read the emotional arc from energy movement over time."""
        thirds = min_len // 3
        e1 = float(np.mean(rms[:thirds]))
        e2 = float(np.mean(rms[thirds:2*thirds]))
        e3 = float(np.mean(rms[2*thirds:]))

        if e2 > e1 and e2 > e3:
            shape = "PEAK_CENTER"
            meaning = "Energy peaks in the middle. Builds then releases."
        elif e3 > e1 and e3 > e2:
            shape = "CLIMAX_END"
            meaning = "Energy builds throughout. Climax at the end."
        elif e1 > e2 and e1 > e3:
            shape = "FRONT_LOADED"
            meaning = "Opens with peak energy. Gradually releases."
        else:
            shape = "SUSTAINED"
            meaning = "Energy held consistently throughout."

        # Peak moment
        peak_frame   = int(np.argmax(rms))
        peak_time    = peak_frame * self.hop / 44100

        # Ending character — last 15%
        tail_start   = int(min_len * 0.85)
        tail_rms     = rms[tail_start:]
        tail_slope   = float(np.polyfit(np.arange(len(tail_rms)), tail_rms, 1)[0])
        ending       = "decay" if tail_slope < -0.00005 else (
                       "sustain" if abs(tail_slope) < 0.00005 else "rise")

        # Pitch arc — does the voice rise or fall across the song?
        valid_by_third = []
        for i in range(3):
            seg = pitch[i*thirds:(i+1)*thirds]
            v   = seg[seg > 0]
            valid_by_third.append(float(np.mean(v)) if len(v) else 0.0)

        pitch_direction = "rising" if valid_by_third[2] > valid_by_third[0] else (
                          "falling" if valid_by_third[2] < valid_by_third[0] else "stable")

        return {
            "shape"          : shape,
            "meaning"        : meaning,
            "energy_thirds"  : {
                "first" : round(e1, 5),
                "middle": round(e2, 5),
                "last"  : round(e3, 5),
            },
            "peak_time_sec"  : round(peak_time, 1),
            "ending"         : ending,
            "ending_slope"   : round(tail_slope, 7),
            "pitch_direction": pitch_direction,
            "pitch_by_third" : [round(v, 1) for v in valid_by_third],
        }

    def _extract_events(
        self,
        rms      : np.ndarray,
        pitch    : np.ndarray,
        centroid : np.ndarray,
        onset_env: np.ndarray,
        duration : float,
        min_len  : int,
    ) -> dict:
        """Locate tension peaks, release moments, and singular events."""
        times = np.arange(min_len) * self.hop / self.sr

        # Tension peaks — top 5 RMS moments
        top5_frames = np.argsort(rms)[-5:][::-1]
        tension_peaks = [
            {"time_sec": round(float(times[f]), 1), "rms": round(float(rms[f]), 5)}
            for f in sorted(top5_frames)
        ]

        # Release moments — where RMS drops fastest
        rms_diff    = np.diff(rms)
        drop_frames = np.argsort(rms_diff)[:3]
        releases    = [
            {"time_sec": round(float(times[f]), 1), "drop": round(float(rms_diff[f]), 5)}
            for f in sorted(drop_frames)
        ]

        # Brightness spikes — centroid peaks (emotional intensity moments)
        top3_bright = np.argsort(centroid)[-3:][::-1]
        bright_moments = [
            {"time_sec": round(float(times[f]), 1), "centroid_hz": round(float(centroid[f]), 1)}
            for f in sorted(top3_bright)
        ]

        # Onset density by segment (rhythmic structure)
        segments     = 8
        seg_size     = min_len // segments
        onset_density= [
            round(float(np.mean(onset_env[i*seg_size:(i+1)*seg_size])), 4)
            for i in range(segments)
        ]

        return {
            "tension_peaks"   : tension_peaks,
            "release_moments" : releases,
            "brightness_spikes": bright_moments,
            "onset_density_arc": onset_density,
        }

    def _detect_instrumentation(
        self,
        hp_ratio    : float,
        centroid    : float,
        zcr         : float,
        onset       : float,
        median_pitch: float,
        valid_pitch : np.ndarray,
        mfcc        : list,
    ) -> dict:
        """
        Detect what is making the sound from pattern signatures alone.
        Returns confidence-weighted detection results.
        No label is assigned without pattern evidence.
        """
        detected = {}

        # Male vocals — harmonic dominant, pitch in bass/baritone/tenor range
        if hp_ratio > 1.5 and 60 <= median_pitch <= 520:
            conf = min(1.0, (hp_ratio - 1.5) / 3.0 + 0.5)
            detected["male_vocals"] = {
                "confidence": round(conf, 2),
                "evidence"  : f"H/P ratio {hp_ratio:.2f}, median pitch {median_pitch:.1f}Hz in male vocal range"
            }

        # Female vocals — harmonic dominant, higher pitch range
        if hp_ratio > 1.5 and median_pitch > 180:
            conf = min(1.0, (hp_ratio - 1.5) / 3.0 + 0.4)
            detected["female_vocals"] = {
                "confidence": round(conf, 2),
                "evidence"  : f"H/P ratio {hp_ratio:.2f}, median pitch {median_pitch:.1f}Hz in female vocal range"
            }

        # Drums — percussive dominant, high onset strength
        if hp_ratio < 3.0 and onset > 0.9:
            conf = min(1.0, onset / 2.0)
            detected["drums"] = {
                "confidence": round(conf, 2),
                "evidence"  : f"Onset strength {onset:.3f}, H/P ratio {hp_ratio:.2f}"
            }

        # Bass guitar — low centroid, harmonic, low pitch
        if centroid < 2000 and hp_ratio > 1.2 and median_pitch < 120:
            conf = min(1.0, (2000 - centroid) / 2000 * 0.8)
            detected["bass_guitar"] = {
                "confidence": round(conf, 2),
                "evidence"  : f"Centroid {centroid:.1f}Hz, low median pitch {median_pitch:.1f}Hz"
            }

        # Guitar (rhythm/lead) — harmonic, mid-high centroid
        if hp_ratio > 2.0 and 1500 < centroid < 5000:
            conf = min(1.0, (hp_ratio - 2.0) / 2.0 + 0.4)
            detected["guitar"] = {
                "confidence": round(conf, 2),
                "evidence"  : f"H/P ratio {hp_ratio:.2f}, centroid {centroid:.1f}Hz"
            }

        # Determine dominant element
        if detected:
            dominant = max(detected, key=lambda k: detected[k]["confidence"])
        else:
            dominant = "unknown"

        return {
            "detected"  : detected,
            "dominant"  : dominant,
            "hp_ratio"  : round(hp_ratio, 3),
            "note"      : "Detections are pattern-derived. Confidence reflects signal evidence strength.",
        }

    def _classify_texture(
        self,
        hp_ratio : float,
        zcr      : float,
        centroid : float,
    ) -> dict:
        """Read the surface texture of the sound from signal patterns."""

        if hp_ratio > 3.0:
            harmonic_character = "strongly_harmonic"
        elif hp_ratio > 1.5:
            harmonic_character = "harmonic_dominant"
        elif hp_ratio > 0.8:
            harmonic_character = "balanced"
        else:
            harmonic_character = "percussive_dominant"

        if zcr > 0.15:
            surface = "rough_noisy"
        elif zcr > 0.08:
            surface = "textured"
        elif zcr > 0.04:
            surface = "smooth"
        else:
            surface = "very_smooth_tonal"

        if centroid > 5000:
            brightness = "very_bright"
        elif centroid > 3000:
            brightness = "bright"
        elif centroid > 1500:
            brightness = "warm_mid"
        else:
            brightness = "dark_low"

        return {
            "harmonic_character": harmonic_character,
            "surface"           : surface,
            "brightness"        : brightness,
        }

    def _assign_sacred_verb(
        self,
        rms    : float,
        pitch  : float,
        centroid: float,
        arc    : str,
    ) -> str:
        if rms < 0.01:
            return "release"
        if arc == "CLIMAX_END":
            return "emerge"
        if arc == "PEAK_CENTER":
            return "resonate"
        if pitch < 80:
            return "hold"
        if centroid > 4000 and rms > 0.15:
            return "sense"
        if pitch > 300:
            return "pattern"
        if centroid < 1500:
            return "remember"
        return "link"

    def _resonance_character(self, hp_ratio: float, arc: str) -> str:
        if hp_ratio > 2.5 and arc == "CLIMAX_END":
            return "harmonic_surge"
        if hp_ratio > 2.5:
            return "sustained_harmonic"
        if arc == "CLIMAX_END":
            return "building_release"
        return "ambient_resonance"

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[SpiralSense:Meta] {msg}")


# ═══════════════════════════════════════════════════════════════════════════
#  DEMO
# ═══════════════════════════════════════════════════════════════════════════

def _demo():
    import sys, os
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    if not filepath or not os.path.exists(filepath):
        print("Usage: python metadata_extractor.py <audiofile>")
        return

    ex  = MetadataExtractor()
    pkt = ex.extract(filepath)

    base = os.path.splitext(os.path.basename(filepath))[0]
    out  = f"/tmp/symb_meta_{base}.json"
    ex.save(pkt, out)

    print(f"\n{'═'*58}")
    print(f"  SYMB Metadata Packet — {base}")
    print(f"{'═'*58}")
    print(f"  Duration     : {pkt['acoustic']['duration_sec']}s")
    print(f"  Tempo        : {pkt['acoustic']['tempo_bpm']} BPM")
    print(f"  Tonal center : {pkt['acoustic']['tonal_center']}")
    print(f"  Register     : {pkt['voice']['register']}")
    print(f"  Median pitch : {pkt['voice']['median_fundamental_hz']} Hz")
    print(f"  Arc shape    : {pkt['emotional_arc']['shape']}")
    print(f"  Arc meaning  : {pkt['emotional_arc']['meaning']}")
    print(f"  Ending       : {pkt['emotional_arc']['ending']}")
    print(f"  Pitch dir    : {pkt['emotional_arc']['pitch_direction']}")
    print(f"  Peak moment  : {pkt['emotional_arc']['peak_time_sec']}s")
    print(f"  Dominant     : {pkt['instrumentation']['dominant']}")
    print(f"  Texture      : {pkt['texture']}")
    print(f"  Sacred verb  : {pkt['symb']['sacred_verb']}")
    print(f"  Resonance    : {pkt['symb']['resonance_character']}")
    print(f"\n  Instrumentation detected:")
    for k, v in pkt['instrumentation']['detected'].items():
        print(f"    {k:<20} confidence={v['confidence']}")
    print(f"\n  Saved → {out}")
    print(f"{'═'*58}\n")


if __name__ == "__main__":
    _demo()
