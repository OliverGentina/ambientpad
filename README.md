# AmbientPad Live – Web-App

Pad-Sounds in allen 12 Tonarten für Worship. Läuft offline als Web-App auf iPhone und iPad
(Safari → Teilen → „Zum Home-Bildschirm“): https://olivergentina.github.io/ambientpad/

- 2 Sets mit je 12 Tonarten, vorbelegt mit den Standard-Pads **Warm** und **Shimmer**
- Eigene MP3/WAV/M4A-Dateien ersetzen einzelne Tasten – per Dateiauswahl oder Drag & Drop auf eine Tonart (gespeichert nur im jeweiligen Browser)
- Weiche Überblendungen, nahtlose Schleifen
- Steuerung per Bluetooth-Umblätter-Pedal (2 Tasten): links kurz = nächste Tonart, lang = zurück;
  rechts kurz = Start/Stopp, lang = alles ausblenden

## Meine Pads (privat)

Eigene, gekaufte Pads liegen in einem separaten **privaten** Repository (Standard: `meine-pads`, Ordner `Meine Pads/<Set-Name>/`).
Jeder Unterordner erscheint in der App als eigenes Set; die Tonart wird aus dem Dateinamen gelesen (z. B. „01 - Key of A Pads.mp3“).
Zugriff per fein abgestuftem GitHub-Token (nur Lesen, nur dieses Repository), einmal pro Gerät in ⚙︎ eintragen.

## Standard-Pads

`pads/` enthält 24 selbst synthetisierte Loops (60 s, 160 kbit/s MP3, exakt periodisch).
Tonartneutral (Grundton, Quinte, Oktave, None – keine Terz), passen also zu Dur und Moll.
Neu erzeugen: `python3 tools/padgen.py pads` (benötigt numpy und ffmpeg).

## Neue Version veröffentlichen

Dateien ersetzen und in `sw.js` die `VERSION` erhöhen – die App lädt die Änderung beim nächsten Start.
