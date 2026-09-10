import json
from pathlib import Path

import cv2
import numpy as np


def load_paths(path: str):
    """Lädt die gespeicherten Zeichenpfade."""

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Pfaddatei nicht gefunden: {path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data["paths"]


def calculate_bounds(paths):
    """Berechnet die Grenzen aller Zeichenpunkte."""

    all_points = [
        point
        for path in paths
        for point in path
    ]

    if not all_points:
        raise ValueError("Keine Zeichenpunkte vorhanden.")

    min_x = min(point["x"] for point in all_points)
    max_x = max(point["x"] for point in all_points)
    min_y = min(point["y"] for point in all_points)
    max_y = max(point["y"] for point in all_points)

    return min_x, max_x, min_y, max_y


def create_simulation(
    paths,
    output_path: str,
    padding: int = 20,
):
    """
    Zeichnet die gespeicherten Mauspfade auf
    eine weiße Fläche.
    """

    min_x, max_x, min_y, max_y = calculate_bounds(paths)

    width = (max_x - min_x) + padding * 2
    height = (max_y - min_y) + padding * 2

    # Mindestgröße
    width = max(width, 100)
    height = max(height, 100)

    canvas = np.ones(
        (height, width, 3),
        dtype=np.uint8,
    ) * 255

    for path in paths:
        if len(path) < 2:
            continue

        points = []

        for point in path:
            x = point["x"] - min_x + padding
            y = point["y"] - min_y + padding

            points.append([x, y])

        points = np.array(
            points,
            dtype=np.int32,
        )

        cv2.polylines(
            canvas,
            [points],
            isClosed=False,
            color=(0, 0, 0),
            thickness=2,
        )

    success = cv2.imwrite(
        output_path,
        canvas,
    )

    if not success:
        raise IOError(
            f"Simulation konnte nicht gespeichert werden: "
            f"{output_path}"
        )


def main():
    paths_file = "images/auto_paths.json"
    output_file = "images/auto_simulation.png"

    print("Zeichenpfade werden geladen...")

    paths = load_paths(paths_file)

    print(
        f"{len(paths)} Zeichenpfade geladen."
    )

    total_points = sum(
        len(path)
        for path in paths
    )

    print(
        f"{total_points} Zeichenpunkte geladen."
    )

    print("Simulation wird erstellt...")

    create_simulation(
        paths,
        output_file,
    )

    print(
        f"Simulation gespeichert: {output_file}"
    )


if __name__ == "__main__":
    main()