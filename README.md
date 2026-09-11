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

Du kannst das Bild auch über den Explorer auswählen:

```powershell
python src/image_processor.py
```

Ohne Pfad öffnet sich ein Dateiauswahldialog.

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