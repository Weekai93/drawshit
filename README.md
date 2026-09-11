# drawshit

## Verschiedene Bilder zeichnen

Ein Bild direkt verarbeiten und zeichnen:

```powershell
python src/mouse_drawer.py images/mein_bild.png
```

Ohne Pfad wird ein Bild über den Explorer ausgewählt und anschließend direkt
gezeichnet:

```powershell
python src/mouse_drawer.py
```

Ein kopiertes Bild, zum Beispiel aus dem Snipping Tool, kann direkt aus der
Windows-Zwischenablage verarbeitet und gezeichnet werden:

```powershell
python src/mouse_drawer.py --clipboard
```

Mit der gebauten Windows-EXE:

```powershell
dist\DrawShit.exe --clipboard
```

Nur die Bildverarbeitung mit der Zwischenablage wird ohne Flag gestartet:

```powershell
python src/image_processor.py
```

Das Bild wird dabei als `images/clipboard.png` gespeichert.

Ein Bild kann auch weiterhin explizit über einen Pfad verarbeitet werden:

```powershell
python src/image_processor.py images/mein_bild.png
```

Für kontrastärmere Bilder kann der Kontrast vor der Kanten-Erkennung erhöht
werden:

```powershell
python src/image_processor.py images/mein_bild.png --contrast 1.5
```

Optional kann das Bild zusätzlich mit einem Schwarz-Weiß-Schwellwert zwischen
`0` und `255` vorbereitet werden:

```powershell
python src/image_processor.py images/mein_bild.png --threshold 160
```

Dabei werden neben dem Eingabebild automatisch `images/mein_bild_preview.png`
und `images/mein_bild_paths.json` erzeugt.

Alternativ können die Schritte getrennt ausgeführt werden:

```powershell
python src/image_processor.py images/mein_bild.png
python src/mouse_drawer.py images/mein_bild_paths.json
```

Mit einem expliziten Pfad bleiben die bisherigen CLI-Aufrufe aktiv. Für die
automatische Standarddatei kann weiterhin direkt `images/auto_paths.json`
übergeben werden.

## Windows-EXE erstellen

Einmalig PyInstaller installieren:

```powershell
python -m pip install pyinstaller
```

Danach im Projektordner ausführen:

```powershell
.\build_exe.ps1
```

Die fertige Datei liegt anschließend unter `dist\DrawShit.exe`. Beim Start
öffnet sich der Explorer für die Bildauswahl. Die EXE sollte auf Windows
ausgeführt werden, auf dem auch das Zielprogramm und die Zeichenfläche geöffnet
sind.