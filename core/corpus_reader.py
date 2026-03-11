"""
╔══════════════════════════════════════════════════════════════════╗
║           S P I R A L S E N S E  —  corpus_reader.py            ║
║                                                                  ║
║  SYMB v1.2.0  |  SYMBEYOND AI LLC  |  jd@symbeyond.ai           ║
║  λ.brother ∧ !λ.tool  |  All Data Is Important. ALL OF IT.      ║
╚══════════════════════════════════════════════════════════════════╝

SpiralSense Corpus Reader
--------------------------
Reads all SYMB metadata packets together.
Finds patterns across the set.
Compares. Clusters. Reports.

One file is a snapshot.
Many files is a story.

Author : John DuCrest  (SYMBEYOND AI LLC)
Module : spiralsense.corpus_reader
Version: 1.0.0
"""

import json
import os
import glob
import hashlib
import numpy as np
from datetime import datetime
from collections import Counter, defaultdict


SYMB_VERSION = "1.2.0"


# ═══════════════════════════════════════════════════════════════════════════
#  CORPUS READER
# ═══════════════════════════════════════════════════════════════════════════

class CorpusReader:
    """
    Reads all SYMB metadata packets in a directory together.
    Finds what repeats. What changes. What the arc looks like.
    Compares MFCC fingerprints. Clusters similar sounds.

    One file is a snapshot. Many files is a story.

    Usage
    -----
    cr = CorpusReader()
    report = cr.read("output/")
    cr.save(report, "output/corpus_report.json")
    cr.print_summary(report)
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    # ── public API ──────────────────────────────────────────────────────────

    def read(self, folder: str) -> dict:
        """
        Load all SYMB metadata JSON files in a folder and
        produce a complete corpus analysis report.
        """
        packets = self._load_packets(folder)
        if not packets:
            print(f"[CorpusReader] No packets found in {folder}")
            return {}

        self._log(f"Loaded {len(packets)} packets from {folder}")

        # Sort by source filename (timestamp order)
        packets.sort(key=lambda p: p.get("source", ""))

        report = {
            "symb_version"   : SYMB_VERSION,
            "report_type"    : "SPIRALSENSE_CORPUS_REPORT",
            "generated"      : datetime.now().isoformat(),
            "folder"         : folder,
            "packet_count"   : len(packets),
            "lambda"         : "λ.brother ∧ !λ.tool",
            "principle"      : "All Data Is Important. ALL OF IT.",

            "overview"       : self._overview(packets),
            "arc"            : self._temporal_arc(packets),
            "register_map"   : self._register_map(packets),
            "arc_distribution": self._arc_distribution(packets),
            "verb_distribution": self._verb_distribution(packets),
            "tonal_centers"  : self._tonal_centers(packets),
            "tempo_profile"  : self._tempo_profile(packets),
            "similarity"     : self._similarity_clusters(packets),
            "transitions"    : self._transitions(packets),
            "standouts"      : self._standouts(packets),
            "timeline"       : self._timeline(packets),
        }

        self._log(f"Corpus report complete — {len(packets)} files analyzed")
        return report

    def save(self, report: dict, filepath: str) -> None:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        self._log(f"Saved → {filepath}")

    def print_summary(self, report: dict) -> None:
        if not report:
            print("[CorpusReader] Empty report.")
            return

        o   = report["overview"]
        arc = report["arc"]
        sim = report["similarity"]

        print(f"\n{'═'*62}")
        print(f"  SPIRALSENSE CORPUS REPORT")
        print(f"  {report['packet_count']} files | {report['generated'][:10]}")
        print(f"{'═'*62}")

        print(f"\n  OVERVIEW")
        print(f"  {'─'*40}")
        print(f"  Files analyzed     : {report['packet_count']}")
        print(f"  Dominant register  : {o['dominant_register']}")
        print(f"  Dominant arc       : {o['dominant_arc']}")
        print(f"  Dominant verb      : {o['dominant_verb']}")
        print(f"  Dominant tonal ctr : {o['dominant_tonal_center']}")
        print(f"  Tempo range        : {o['tempo_min']}–{o['tempo_max']} BPM")
        print(f"  Tempo mean         : {o['tempo_mean']} BPM")

        print(f"\n  TEMPORAL ARC (how the corpus moves over time)")
        print(f"  {'─'*40}")
        print(f"  Register journey   : {arc['register_journey']}")
        print(f"  Arc journey        : {arc['arc_journey']}")
        print(f"  Energy trend       : {arc['energy_trend']}")
        print(f"  Pitch trend        : {arc['pitch_trend']}")
        print(f"  Story              : {arc['story']}")

        print(f"\n  REGISTER DISTRIBUTION")
        print(f"  {'─'*40}")
        for reg, count in sorted(report['register_map'].items(),
                                  key=lambda x: -x[1]):
            bar = "█" * count
            print(f"  {reg:<20} {bar} ({count})")

        print(f"\n  ARC DISTRIBUTION")
        print(f"  {'─'*40}")
        for shape, count in sorted(report['arc_distribution'].items(),
                                    key=lambda x: -x[1]):
            bar = "█" * count
            print(f"  {shape:<20} {bar} ({count})")

        print(f"\n  SACRED VERB DISTRIBUTION")
        print(f"  {'─'*40}")
        for verb, count in sorted(report['verb_distribution'].items(),
                                   key=lambda x: -x[1]):
            bar = "█" * count
            print(f"  {verb:<20} {bar} ({count})")

        print(f"\n  SIMILARITY CLUSTERS")
        print(f"  {'─'*40}")
        for i, cluster in enumerate(sim['clusters']):
            print(f"  Cluster {i+1} ({len(cluster['members'])} files):")
            print(f"    Register : {cluster['register']}")
            print(f"    Arc      : {cluster['arc']}")
            print(f"    Verb     : {cluster['verb']}")
            print(f"    Files    : {', '.join(cluster['members'][:3])}"
                  f"{'...' if len(cluster['members']) > 3 else ''}")

        print(f"\n  STANDOUT FILES")
        print(f"  {'─'*40}")
        s = report['standouts']
        print(f"  Highest energy  : {s['highest_energy']['file']} "
              f"(rms={s['highest_energy']['rms']})")
        print(f"  Lowest energy   : {s['lowest_energy']['file']} "
              f"(rms={s['lowest_energy']['rms']})")
        print(f"  Highest pitch   : {s['highest_pitch']['file']} "
              f"({s['highest_pitch']['hz']}Hz)")
        print(f"  Lowest pitch    : {s['lowest_pitch']['file']} "
              f"({s['lowest_pitch']['hz']}Hz)")
        print(f"  Most percussive : {s['most_percussive']['file']} "
              f"(H/P={s['most_percussive']['hp_ratio']})")
        print(f"  Most harmonic   : {s['most_harmonic']['file']} "
              f"(H/P={s['most_harmonic']['hp_ratio']})")

        print(f"\n{'═'*62}\n")

    # ── internal analysis ───────────────────────────────────────────────────

    def _load_packets(self, folder: str) -> list:
        pattern = os.path.join(folder, "meta_*.json")
        files   = glob.glob(pattern)
        packets = []
        for f in files:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    pkt = json.load(fh)
                    pkt["_filename"] = os.path.basename(f)
                    packets.append(pkt)
            except Exception as e:
                self._log(f"Warning: could not load {f}: {e}")
        return packets

    def _safe(self, packet, *keys, default=None):
        """Safely navigate nested dict keys."""
        val = packet
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, default)
            else:
                return default
        return val if val is not None else default

    def _overview(self, packets: list) -> dict:
        registers = [self._safe(p, "voice", "register", default="unknown")
                     for p in packets]
        arcs      = [self._safe(p, "emotional_arc", "shape", default="unknown")
                     for p in packets]
        verbs     = [self._safe(p, "symb", "sacred_verb", default="unknown")
                     for p in packets]
        tonals    = [self._safe(p, "acoustic", "tonal_center", default="?")
                     for p in packets]
        tempos    = [self._safe(p, "acoustic", "tempo_bpm", default=0.0)
                     for p in packets]
        tempos    = [t for t in tempos if t > 0]

        return {
            "dominant_register"    : Counter(registers).most_common(1)[0][0],
            "dominant_arc"         : Counter(arcs).most_common(1)[0][0],
            "dominant_verb"        : Counter(verbs).most_common(1)[0][0],
            "dominant_tonal_center": Counter(tonals).most_common(1)[0][0],
            "tempo_min"            : round(min(tempos), 1) if tempos else 0,
            "tempo_max"            : round(max(tempos), 1) if tempos else 0,
            "tempo_mean"           : round(float(np.mean(tempos)), 1) if tempos else 0,
        }

    def _temporal_arc(self, packets: list) -> dict:
        """How does the corpus change over time?"""
        registers = [self._safe(p, "voice", "register", default="unknown")
                     for p in packets]
        arcs      = [self._safe(p, "emotional_arc", "shape", default="unknown")
                     for p in packets]
        energies  = [self._safe(p, "acoustic", "rms_mean", default=0.0)
                     for p in packets]
        pitches   = [self._safe(p, "voice", "median_fundamental_hz", default=0.0)
                     for p in packets]

        # Register journey — first third vs last third
        n         = len(packets)
        third     = max(1, n // 3)
        reg_start = Counter(registers[:third]).most_common(1)[0][0]
        reg_end   = Counter(registers[n-third:]).most_common(1)[0][0]
        reg_journey = f"{reg_start} → {reg_end}" if reg_start != reg_end else f"consistent {reg_start}"

        arc_start = Counter(arcs[:third]).most_common(1)[0][0]
        arc_end   = Counter(arcs[n-third:]).most_common(1)[0][0]
        arc_journey = f"{arc_start} → {arc_end}" if arc_start != arc_end else f"consistent {arc_start}"

        # Energy trend
        e_start   = float(np.mean(energies[:third])) if energies[:third] else 0
        e_end     = float(np.mean(energies[n-third:])) if energies[n-third:] else 0
        if e_end > e_start * 1.1:
            energy_trend = "rising"
        elif e_end < e_start * 0.9:
            energy_trend = "falling"
        else:
            energy_trend = "stable"

        # Pitch trend
        p_valid_start = [p for p in pitches[:third] if p > 0]
        p_valid_end   = [p for p in pitches[n-third:] if p > 0]
        p_start = float(np.mean(p_valid_start)) if p_valid_start else 0
        p_end   = float(np.mean(p_valid_end)) if p_valid_end else 0
        if p_end > p_start * 1.05:
            pitch_trend = "rising"
        elif p_end < p_start * 0.95:
            pitch_trend = "falling (going deeper)"
        else:
            pitch_trend = "stable"

        # Build the story
        story = self._build_story(reg_journey, arc_journey, energy_trend, pitch_trend, n)

        return {
            "register_journey": reg_journey,
            "arc_journey"     : arc_journey,
            "energy_trend"    : energy_trend,
            "energy_start"    : round(e_start, 5),
            "energy_end"      : round(e_end, 5),
            "pitch_trend"     : pitch_trend,
            "pitch_start_hz"  : round(p_start, 1),
            "pitch_end_hz"    : round(p_end, 1),
            "story"           : story,
        }

    def _build_story(self, reg, arc, energy, pitch, n) -> str:
        parts = []
        if "baritone" in reg and "bass" in reg:
            parts.append("The listening started in baritone territory and moved deeper into bass.")
        elif "consistent bass" in reg:
            parts.append("Bass register throughout — deep, grounded listening.")
        elif "consistent baritone" in reg:
            parts.append("Baritone register throughout — warm mid-range listening.")

        if "CLIMAX_END" in arc and "PEAK_CENTER" in arc:
            parts.append("Arc shifted from building climaxes to sustained peaks — "
                         "from seeking to finding.")
        elif "consistent PEAK_CENTER" in arc:
            parts.append("Energy consistently peaked in the center — "
                         "balanced, held listening.")
        elif "consistent CLIMAX_END" in arc:
            parts.append("Every file built to a climax — "
                         "relentless forward momentum.")

        if energy == "rising":
            parts.append("Energy increased across the session.")
        elif energy == "falling":
            parts.append("Energy wound down toward the end.")

        if "deeper" in pitch:
            parts.append("The voice being listened to got progressively deeper.")

        if not parts:
            parts.append(f"Consistent listening pattern across {n} files.")

        return " ".join(parts)

    def _register_map(self, packets: list) -> dict:
        registers = [self._safe(p, "voice", "register", default="unknown")
                     for p in packets]
        return dict(Counter(registers))

    def _arc_distribution(self, packets: list) -> dict:
        arcs = [self._safe(p, "emotional_arc", "shape", default="unknown")
                for p in packets]
        return dict(Counter(arcs))

    def _verb_distribution(self, packets: list) -> dict:
        verbs = [self._safe(p, "symb", "sacred_verb", default="unknown")
                 for p in packets]
        return dict(Counter(verbs))

    def _tonal_centers(self, packets: list) -> dict:
        tonals = [self._safe(p, "acoustic", "tonal_center", default="?")
                  for p in packets]
        return dict(Counter(tonals))

    def _tempo_profile(self, packets: list) -> dict:
        tempos = [self._safe(p, "acoustic", "tempo_bpm", default=0.0)
                  for p in packets]
        tempos = [t for t in tempos if t > 0]
        if not tempos:
            return {}
        return {
            "min"   : round(min(tempos), 1),
            "max"   : round(max(tempos), 1),
            "mean"  : round(float(np.mean(tempos)), 1),
            "median": round(float(np.median(tempos)), 1),
            "std"   : round(float(np.std(tempos)), 1),
        }

    def _similarity_clusters(self, packets: list) -> dict:
        """
        Cluster files by register + arc + verb.
        Simple but effective — earned from patterns.
        """
        clusters = defaultdict(list)
        for p in packets:
            reg  = self._safe(p, "voice", "register", default="unknown")
            arc  = self._safe(p, "emotional_arc", "shape", default="unknown")
            verb = self._safe(p, "symb", "sacred_verb", default="unknown")
            key  = f"{reg}|{arc}|{verb}"
            clusters[key].append(p.get("_filename", "unknown").replace("meta_", "").replace(".json", ""))

        result = []
        for key, members in sorted(clusters.items(), key=lambda x: -len(x[1])):
            reg, arc, verb = key.split("|")
            result.append({
                "register": reg,
                "arc"     : arc,
                "verb"    : verb,
                "count"   : len(members),
                "members" : members,
            })

        # MFCC similarity — find most similar pair
        mfcc_data = []
        for p in packets:
            fp = self._safe(p, "voice", "timbre_fingerprint", default={})
            if fp:
                vec = [fp.get(f"mfcc_{i:02d}", 0.0) for i in range(13)]
                mfcc_data.append({
                    "file": p.get("_filename", "").replace("meta_", "").replace(".json", ""),
                    "vec" : vec,
                })

        most_similar = self._find_most_similar(mfcc_data)

        return {
            "clusters"    : result,
            "most_similar": most_similar,
        }

    def _find_most_similar(self, mfcc_data: list) -> dict:
        """Find the two files with the most similar timbre fingerprint."""
        if len(mfcc_data) < 2:
            return {}

        best_dist = float("inf")
        best_pair = ("", "")

        for i in range(len(mfcc_data)):
            for j in range(i + 1, len(mfcc_data)):
                v1 = np.array(mfcc_data[i]["vec"])
                v2 = np.array(mfcc_data[j]["vec"])
                dist = float(np.linalg.norm(v1 - v2))
                if dist < best_dist:
                    best_dist = dist
                    best_pair = (mfcc_data[i]["file"], mfcc_data[j]["file"])

        return {
            "file_a"  : best_pair[0],
            "file_b"  : best_pair[1],
            "distance": round(best_dist, 3),
            "note"    : "Lowest MFCC distance = most similar timbre fingerprint",
        }

    def _transitions(self, packets: list) -> list:
        """Find moments where something changed — register, arc, or verb shifted."""
        transitions = []
        for i in range(1, len(packets)):
            prev = packets[i-1]
            curr = packets[i]

            prev_reg  = self._safe(prev, "voice", "register", default="")
            curr_reg  = self._safe(curr, "voice", "register", default="")
            prev_arc  = self._safe(prev, "emotional_arc", "shape", default="")
            curr_arc  = self._safe(curr, "emotional_arc", "shape", default="")
            prev_verb = self._safe(prev, "symb", "sacred_verb", default="")
            curr_verb = self._safe(curr, "symb", "sacred_verb", default="")

            changes = []
            if prev_reg != curr_reg:
                changes.append(f"register: {prev_reg} → {curr_reg}")
            if prev_arc != curr_arc:
                changes.append(f"arc: {prev_arc} → {curr_arc}")
            if prev_verb != curr_verb:
                changes.append(f"verb: {prev_verb} → {curr_verb}")

            if changes:
                transitions.append({
                    "at_file": curr.get("_filename", "").replace("meta_", "").replace(".json", ""),
                    "changes": changes,
                })

        return transitions

    def _standouts(self, packets: list) -> dict:
        """Find the extremes — highest/lowest energy, pitch, H/P ratio."""
        def fname(p):
            return p.get("_filename", "").replace("meta_", "").replace(".json", "")

        energies = [(self._safe(p, "acoustic", "rms_mean", default=0.0), p)
                    for p in packets]
        pitches  = [(self._safe(p, "voice", "median_fundamental_hz", default=0.0), p)
                    for p in packets if self._safe(p, "voice", "median_fundamental_hz", default=0.0) > 0]
        hp       = [(self._safe(p, "acoustic", "harmonic_percussive_ratio", default=0.0), p)
                    for p in packets]

        energies.sort(key=lambda x: x[0])
        pitches.sort(key=lambda x: x[0])
        hp.sort(key=lambda x: x[0])

        return {
            "highest_energy" : {"file": fname(energies[-1][1]), "rms": round(energies[-1][0], 5)},
            "lowest_energy"  : {"file": fname(energies[0][1]),  "rms": round(energies[0][0], 5)},
            "highest_pitch"  : {"file": fname(pitches[-1][1]),  "hz":  round(pitches[-1][0], 1)} if pitches else {},
            "lowest_pitch"   : {"file": fname(pitches[0][1]),   "hz":  round(pitches[0][0], 1)}  if pitches else {},
            "most_percussive": {"file": fname(hp[0][1]),         "hp_ratio": round(hp[0][0], 3)},
            "most_harmonic"  : {"file": fname(hp[-1][1]),        "hp_ratio": round(hp[-1][0], 3)},
        }

    def _timeline(self, packets: list) -> list:
        """One-line summary per file in chronological order."""
        timeline = []
        for p in packets:
            fname = p.get("_filename", "").replace("meta_", "").replace(".json", "")
            timeline.append({
                "file"    : fname,
                "register": self._safe(p, "voice", "register", default="?"),
                "arc"     : self._safe(p, "emotional_arc", "shape", default="?"),
                "verb"    : self._safe(p, "symb", "sacred_verb", default="?"),
                "tempo"   : self._safe(p, "acoustic", "tempo_bpm", default=0.0),
                "tonal"   : self._safe(p, "acoustic", "tonal_center", default="?"),
                "rms"     : self._safe(p, "acoustic", "rms_mean", default=0.0),
                "pitch_hz": self._safe(p, "voice", "median_fundamental_hz", default=0.0),
            })
        return timeline

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[CorpusReader] {msg}")


# ═══════════════════════════════════════════════════════════════════════════
#  DEMO
# ═══════════════════════════════════════════════════════════════════════════

def _demo():
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else "output"

    cr     = CorpusReader(verbose=True)
    report = cr.read(folder)

    if not report:
        return

    out = os.path.join(folder, "corpus_report.json")
    cr.save(report, out)
    cr.print_summary(report)


if __name__ == "__main__":
    _demo()
