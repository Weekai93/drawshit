import argparse
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import numpy as np
from PIL import ImageGrab


EDGE_BLUR_KERNEL = (3, 3)
EDGE_LOW_THRESHOLD = 30
EDGE_HIGH_THRESHOLD = 100
MIN_CONTOUR_PERIMETER = 10
CONTOUR_EPSILON_FACTOR = 0.0005
CLIPBOARD_IMAGE_PATH = Path("images/clipboard.png")
DEFAULT_CONTRAST_FACTOR = 1.0


def load_image(image_path: str) -> np.ndarray:
    """Lädt ein Bild von der Festplatte."""
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Bild nicht gefunden: {image_path}")

    image = cv2.imread(str(path))

    if image is None:
        raise ValueError(f"Bild konnte nicht geladen werden: {image_path}")

    return image


def create_edge_image(
    image: np.ndarray,
    contrast_factor=DEFAULT_CONTRAST_FACTOR,
    threshold=None,
) -> np.ndarray:
    """Erkennt die Kanten des Bildes."""

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if contrast_factor <= 0:
        raise ValueError("Der Kontrastfaktor muss größer als 0 sein.")

    if contrast_factor != DEFAULT_CONTRAST_FACTOR:
        gray = cv2.convertScaleAbs(
            gray,
            alpha=contrast_factor,
            beta=128 * (1 - contrast_factor),
        )

    if threshold is not None and not 0 <= threshold <= 255:
        raise ValueError("Der Schwellwert muss zwischen 0 und 255 liegen.")

    if threshold is not None:
        _, gray = cv2.threshold(
            gray,
            threshold,
            255,
            cv2.THRESH_BINARY,
        )

    # Leicht glätten, damit Fotorauschen nicht zu Zeichenlinien wird.
    blurred = cv2.GaussianBlur(gray, EDGE_BLUR_KERNEL, 0)

    edges = cv2.Canny(
        blurred,
        EDGE_LOW_THRESHOLD,
        EDGE_HIGH_THRESHOLD,
    )

    return edges


def find_contours(edge_image: np.ndarray):
    """Findet und filtert die Konturen."""

    contours, _ = cv2.findContours(
        edge_image,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_NONE,
    )

    # Kleine Konturen entfernen
    contours = [
        contour
        for contour in contours
        if cv2.arcLength(contour, False) > MIN_CONTOUR_PERIMETER
    ]

    # Größte Konturen zuerst
    contours.sort(
        key=lambda contour: cv2.arcLength(contour, False),
        reverse=True,
    )

    return contours


def simplify_contours(
    contours,
    epsilon_factor=CONTOUR_EPSILON_FACTOR,
):
    """
    Vereinfacht die Konturen.

    Dadurch müssen wir später nicht tausende einzelne
    Mausbewegungen ausführen.
    """

    simplified = []

    for contour in contours:
        perimeter = cv2.arcLength(contour, False)

        epsilon = epsilon_factor * perimeter

        approx = cv2.approxPolyDP(
            contour,
            epsilon,
            False,
        )

        points = []

        for point in approx:
            x, y = point[0]

            points.append(
                {
                    "x": int(x),
                    "y": int(y),
                }
            )

        if len(points) >= 2:
            simplified.append(points)

    return simplified


def save_paths(paths, output_path: str):
    """Speichert die Zeichenpfade als JSON."""

    data = {
        "paths": paths,
        "path_count": len(paths),
    }

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
        )


def create_preview(
    image: np.ndarray,
    contours,
    output_path: str,
):
    """Erstellt eine Vorschau der erkannten Konturen."""

    preview = np.ones_like(image) * 255

    cv2.drawContours(
        preview,
        contours,
        -1,
        (0, 0, 0),
        2,
    )

    success = cv2.imwrite(
        output_path,
        preview,
    )

    if not success:
        raise IOError(
            f"Vorschau konnte nicht gespeichert werden: {output_path}"
        )


def process_image(
    input_path: str,
    preview_path: str,
    paths_path: str,
    contrast_factor=DEFAULT_CONTRAST_FACTOR,
    threshold=None,
):
    """Komplette Bildverarbeitung."""

    print(f"Bild wird geladen: {input_path}")

    image = load_image(input_path)

    print(
        f"Bildgröße: "
        f"{image.shape[1]} x {image.shape[0]}"
    )

    print("Kanten werden erkannt...")

    edges = create_edge_image(
        image,
        contrast_factor=contrast_factor,
        threshold=threshold,
    )

    print("Konturen werden gesucht...")

    contours = find_contours(edges)

    print(
        f"Gefundene Konturen: {len(contours)}"
    )

    print("Konturen werden vereinfacht...")

    paths = simplify_contours(contours)

    total_points = sum(
        len(path)
        for path in paths
    )

    print(
        f"Zeichenpfade: {len(paths)}"
    )

    print(
        f"Zeichenpunkte: {total_points}"
    )

    print("Vorschau wird erstellt...")

    create_preview(
        image,
        contours,
        preview_path,
    )

    print(
        f"Vorschau gespeichert: "
        f"{preview_path}"
    )

    print("Zeichenpfade werden gespeichert...")

    save_paths(
        paths,
        paths_path,
    )

    print(
        f"Zeichenpfade gespeichert: "
        f"{paths_path}"
    )

    return paths


def select_image_file() -> Path | None:
    """Öffnet den Explorer und lässt den Benutzer ein Bild auswählen."""
    root = tk.Tk()
    root.withdraw()

    try:
        selected_file = filedialog.askopenfilename(
            title="Bild zum Verarbeiten auswählen",
            filetypes=[
                (
                    "Bilddateien",
                    "*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff",
                ),
                ("Alle Dateien", "*.*"),
            ],
        )
    finally:
        root.destroy()

    return Path(selected_file) if selected_file else None


def select_image_source() -> Path | None:
    """Lässt zwischen Zwischenablage und Dateiauswahl wählen."""
    root = tk.Tk()
    root.withdraw()

    try:
        use_clipboard = messagebox.askyesnocancel(
            title="Bildquelle auswählen",
            message=(
                "Soll das Bild aus der Zwischenablage verwendet werden?\n\n"
                "Ja = Zwischenablage\n"
                "Nein = Bild aus dem Explorer auswählen\n"
                "Abbrechen = Programm beenden"
            ),
            default="yes",
        )

        if use_clipboard is True:
            return save_clipboard_image()

        if use_clipboard is False:
            return select_image_file()

        return None
    finally:
        root.destroy()


def save_clipboard_image(output_path=CLIPBOARD_IMAGE_PATH) -> Path:
    """Speichert ein Bild aus der Windows-Zwischenablage als PNG."""
    clipboard_image = ImageGrab.grabclipboard()

    if clipboard_image is None or not hasattr(clipboard_image, "save"):
        raise ValueError(
            "Die Zwischenablage enthält kein Bild. "
            "Bitte zuerst ein Bild, zum Beispiel mit dem Snipping Tool, "
            "kopieren."
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clipboard_image.convert("RGB").save(output_path, format="PNG")

    print(f"Bild aus der Zwischenablage gespeichert: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Verarbeitet ein Bild in Zeichenpfade."
    )
    parser.add_argument(
        "image_path",
        nargs="?",
        help=(
            "Pfad zum Eingabebild; ohne Angabe wird die "
            "Zwischenablage verwendet"
        ),
    )
    parser.add_argument(
        "--clipboard",
        action="store_true",
        help="Verwendet das Bild aus der Zwischenablage",
    )
    parser.add_argument(
        "--contrast",
        type=float,
        default=DEFAULT_CONTRAST_FACTOR,
        help=(
            "Kontrastfaktor für die Kanten-Erkennung "
            "(Standard: 1.0)"
        ),
    )
    parser.add_argument(
        "--threshold",
        type=int,
        help=(
            "Optionaler Schwarz-Weiß-Schwellwert zwischen 0 und 255"
        ),
    )

    args = parser.parse_args()
    if args.clipboard and args.image_path:
        parser.error("Bildpfad und --clipboard können nicht kombiniert werden.")

    image_path = (
        save_clipboard_image()
        if args.clipboard or not args.image_path
        else Path(args.image_path)
    )

    if image_path is None:
        print("Dateiauswahl abgebrochen. Programm wird beendet.")
        raise SystemExit(0)

    process_image(
        str(image_path),
        str(image_path.with_name(
            f"{image_path.stem}_preview.png"
        )),
        str(image_path.with_name(
            f"{image_path.stem}_paths.json"
        )),
        contrast_factor=args.contrast,
        threshold=args.threshold,
    )


if __name__ == "__main__":
    main()