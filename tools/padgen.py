"""Synthetisiert die Standard-Pad-Sets „Warm“ und „Shimmer“ für AmbientPad Live.

Alle Frequenzen und Modulationen sind auf ganze Schwingungen pro Loop-Länge gerundet,
dadurch ist jede Datei exakt periodisch und loopt ohne Bruch. Der Hall wird zirkulär
gefaltet, damit auch die Hallfahne über den Loop-Punkt hinweg weiterläuft.
Tonartneutral (Grundton, Quinte, Oktave, None – keine Terz) → passt zu Dur und Moll.
"""
import sys, os, subprocess
import numpy as np
from multiprocessing import Pool

SR = 44100
DUR = 60.0
N = int(SR * DUR)
T = np.arange(N, dtype=np.float64) / SR
NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]


def q(f):
    """Frequenz auf ganze Zyklen pro Loop runden (max. 0,008 Hz Abweichung)."""
    return max(round(f * DUR), 1) / DUR


def osc(f, phase=0.0):
    return np.sin(2 * np.pi * q(f) * T + phase)


def slow(rate, phase=0.0):
    """Langsame Modulation 0…1, periodisch über den Loop."""
    return 0.5 + 0.5 * np.sin(2 * np.pi * q(rate) * T + phase)


def root_freq(k):
    # Register A2 … G#3, damit alle Tonarten ähnlich tief klingen
    return 110.0 * 2 ** (((k - 9) % 12) / 12)


def reverb(x, seconds, mix, brightness, seed):
    """Zirkuläre Faltung mit synthetischer, dekorrelierter Stereo-Hallfahne."""
    rng = np.random.default_rng(seed)
    n_ir = int(SR * seconds)
    t = np.arange(n_ir) / SR
    out = np.empty_like(x)
    for ch in range(2):
        noise = rng.standard_normal(n_ir)
        # Fahne wird mit der Zeit dunkler (einfacher Tiefpass mit wachsender Glättung)
        spec = np.fft.rfft(noise)
        freqs = np.fft.rfftfreq(n_ir, 1 / SR)
        spec *= 1 / (1 + (freqs / brightness) ** 2)
        noise = np.fft.irfft(spec, n_ir)
        ir = noise * np.exp(-6.9 * t / seconds)            # -60 dB nach `seconds`
        ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
        ir /= np.sqrt(np.sum(ir ** 2))
        wet = np.fft.irfft(np.fft.rfft(x[ch]) * np.fft.rfft(ir, N), N)
        out[ch] = (1 - mix) * x[ch] + mix * wet * 1.6
    return out


PH = np.random.default_rng(7).uniform(0, 2 * np.pi, (8, 8, 16))   # feste Zufallsphasen


def warm(k):
    r = root_freq(k)
    L = np.zeros(N); R = np.zeros(N)
    notes = [(r * 0.5, 0.45, 1), (r, 1.0, 9), (r * 1.5, 0.75, 7), (r * 2, 0.55, 6), (r * 3, 0.22, 4)]
    cutoff = 520 + 650 * slow(1 / 30, 0.3)                  # Filter öffnet und schließt alle 30 s
    for ni, (f0, amp, harmonics) in enumerate(notes):
        # 5 fein verstimmte Stimmen statt 3 → gleichmäßigere Schwebung, auch in Mono
        for vi, (cents, pan) in enumerate([(-5, 0.1), (-2, 0.3), (0, 0.5), (2.5, 0.7), (5.5, 0.9)]):
            f = f0 * 2 ** (cents / 1200)
            voice = np.zeros(N)
            for h in range(1, harmonics + 1):
                fh = f * h
                if fh > 5000: break
                lp = 1 / (1 + (fh / cutoff) ** 4)
                voice += np.sin(2 * np.pi * q(fh) * T + PH[ni, vi, h]) * lp / h
            breath = 0.85 + 0.15 * slow(1 / 20 + ni / 60, ni + vi)
            voice *= amp * breath * 0.75
            L += voice * np.cos(pan * np.pi / 2)
            R += voice * np.sin(pan * np.pi / 2)
    x = np.stack([L, R])
    return reverb(x, seconds=3.8, mix=0.38, brightness=2500, seed=100 + k)


def shimmer(k):
    r = root_freq(k)
    L = np.zeros(N); R = np.zeros(N)
    # (Frequenz, Lautstärke, Tremolo-Tiefe)
    partials = [(r, 0.30, 0.0), (r * 2, 0.60, 0.0), (r * 3, 0.55, 0.03), (r * 4, 0.42, 0.05),
                (r * 4.5, 0.18, 0.08), (r * 6, 0.30, 0.08), (r * 8, 0.20, 0.10), (r * 12, 0.10, 0.12),
                (r * 16, 0.05, 0.12)]
    for pi_, (f0, amp, trem) in enumerate(partials):
        for vi, (cents, pan) in enumerate([(-5, 0.1), (0, 0.5), (5, 0.9)]):
            f = f0 * 2 ** (cents / 1200)
            # weiche Mischung aus Sinus und etwas 2. Harmonischer (glockiger)
            s = np.sin(2 * np.pi * q(f) * T + pi_ * 1.3 + vi) + 0.18 * np.sin(2 * np.pi * q(2 * f) * T + vi)
            # unabhängiges, langsames Anschwellen pro Teilton → „Schimmern“
            swell = (0.35 + 0.65 * slow((2 + pi_ + vi) / 60, pi_ * 0.9 + vi * 2.1)
                     * (0.6 + 0.4 * slow((3 + 2 * pi_) / 60, vi)))
            shimmer_mod = 1 - trem + trem * slow(5 + pi_ * 0.7 + vi * 0.31, vi)
            v = s * amp * swell * shimmer_mod
            L += v * np.cos(pan * np.pi / 2)
            R += v * np.sin(pan * np.pi / 2)
    x = np.stack([L, R])
    x = reverb(x, seconds=6.5, mix=0.55, brightness=7000, seed=200 + k)
    return x


def finish(x):
    # sanftes Hochpass-Filter gegen Brummen (zirkulär, damit der Loop erhalten bleibt)
    spec = np.fft.rfft(x, axis=1)
    freqs = np.fft.rfftfreq(N, 1 / SR)
    spec *= (freqs / 40) ** 2 / (1 + (freqs / 40) ** 2)
    x = np.fft.irfft(spec, N, axis=1)
    rms = np.sqrt(np.mean(x ** 2))
    x *= 10 ** (-17 / 20) / rms                              # ca. -17 dBFS RMS
    x = np.tanh(x * 1.1) / 1.1                               # weiche Spitzenbegrenzung
    peak = np.abs(x).max()
    if peak > 0.89: x *= 0.89 / peak                         # max. -1 dBFS
    return x.astype(np.float32)


def render(job):
    kind, k, outdir = job
    x = finish(warm(k) if kind == "warm" else shimmer(k))
    name = f"{'Warm' if kind == 'warm' else 'Shimmer'}-{NAMES[k]}"
    raw = os.path.join(outdir, name + ".f32")
    x.T.tofile(raw)
    mp3 = os.path.join(outdir, name + ".mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", raw,
                    "-c:a", "libmp3lame", "-b:a", "160k", "-metadata", f"title=AmbientPad {name}",
                    "-metadata", "artist=AmbientPad Live", mp3], check=True)
    os.remove(raw)
    return mp3


if __name__ == "__main__":
    outdir = sys.argv[1]
    kinds = sys.argv[2].split(",") if len(sys.argv) > 2 else ["warm", "shimmer"]
    keys = [int(a) for a in sys.argv[3].split(",")] if len(sys.argv) > 3 else range(12)
    os.makedirs(outdir, exist_ok=True)
    jobs = [(kd, k, outdir) for kd in kinds for k in keys]
    with Pool(2) as p:
        for f in p.imap_unordered(render, jobs):
            print("fertig:", os.path.basename(f), flush=True)
