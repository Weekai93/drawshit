from pathlib import Path

import cv2


def load_image(image_path: str):
    """Lädt ein Bild mit OpenCV."""
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Bild nicht gefunden: {image_path}")

    image = cv2.imread(str(path))

    if image is None:
        raise ValueError(f"Bild konnte nicht geladen werden: {image_path}")

    return image


def main():
    print("Mouse Drawing App")
    print("-----------------")
    print("Projekt erfolgreich gestartet.")
    print("")


if __name__ == "__main__":
    main()