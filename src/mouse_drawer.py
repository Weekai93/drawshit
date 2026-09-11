import argparse
import json
import math
import threading
import time
import traceback
from pathlib import Path

import pyautogui
from pynput import keyboard


# ============================================================
# EINSTELLUNGEN
# ============================================================

PATHS_FILE = Path("images/auto_paths.json")

# Höher = schneller
SPEED_PIXELS_PER_SECOND = 15000

# Mindestdauer einer Mausbewegung
MIN_MOVE_DURATION = 0.001

# Pause zwischen einzelnen Zeichenpfaden
PATH_PAUSE = 0.001

# Anzahl der Pfade beim Cursor-Test
TEST_PATHS = 5

# PyAutoGUI
pyautogui.PAUSE = 0.001
pyautogui.MINIMUM_DURATION = 0.001
pyautogui.MINIMUM_SLEEP = 0.001

# Maus ganz oben links = zusätzlicher Not-Aus
pyautogui.FAILSAFE = True

# Globales Stop-Signal
stop_event = threading.Event()


# ============================================================
# ZEICHENPFADE LADEN
# ============================================================

def load_paths(paths_file=PATHS_FILE):
    if not paths_file.exists():
        raise FileNotFoundError(
            f"Datei nicht gefunden: {paths_file}\n"
            "Bitte zuerst image_processor.py ausführen."
        )

    with open(paths_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    if "paths" not in data:
        raise ValueError(
            "Die JSON-Datei enthält keinen 'paths'-Eintrag."
        )

    raw_paths = data["paths"]

    if not raw_paths:
        raise ValueError(
            "Die JSON-Datei enthält keine Zeichenpfade."
        )

    paths = []

    for raw_path in raw_paths:
        path = []

        for point in raw_path:
            if not isinstance(point, dict):
                continue

            if "x" not in point or "y" not in point:
                continue

            try:
                x = float(point["x"])
                y = float(point["y"])
            except (TypeError, ValueError):
                continue

            path.append((x, y))

        if path:
            paths.append(path)

    if not paths:
        raise ValueError(
            "Es konnten keine gültigen Punkte aus der "
            "JSON-Datei gelesen werden."
        )

    return paths


# ============================================================
# BILD-KOORDINATEN
# ============================================================

def get_image_bounds(paths):
    all_points = []

    for path in paths:
        for x, y in path:
            all_points.append((x, y))

    if not all_points:
        raise ValueError(
            "Keine gültigen Punkte in den Zeichenpfaden gefunden."
        )

    min_x = min(x for x, y in all_points)
    max_x = max(x for x, y in all_points)

    min_y = min(y for x, y in all_points)
    max_y = max(y for x, y in all_points)

    return min_x, min_y, max_x, max_y


# ============================================================
# MAUSPOSITION
# ============================================================

def get_mouse_position():
    position = pyautogui.position()
    return position.x, position.y


def wait_for_enter(message):
    """Wartet global auf ENTER, auch wenn das Terminal nicht aktiv ist."""
    print(message, flush=True)

    enter_event = threading.Event()

    def on_press(key):
        if key == keyboard.Key.enter:
            enter_event.set()
            return False

        return True

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        enter_event.wait()
    finally:
        listener.stop()


# ============================================================
# ZEICHENBEREICH AUSWÄHLEN
# ============================================================

def select_drawing_area():
    print()
    print("=" * 50)
    print("ZEICHENBEREICH AUSWÄHLEN")
    print("=" * 50)
    print()
    print("Du wählst jetzt das Rechteck aus,")
    print("in das das Bild gezeichnet werden soll.")
    print()
    print("1. Maus auf die OBERE LINKE Ecke bewegen.")
    print("2. ENTER im Terminal drücken.")
    print("3. Maus auf die UNTERE RECHTE Ecke bewegen.")
    print("4. ENTER im Terminal drücken.")
    print()

    wait_for_enter(
        "Maus auf OBEN-LINKS bewegen und ENTER drücken..."
    )

    top_left = get_mouse_position()

    print(
        f"Oben links gespeichert: "
        f"X={top_left[0]}, Y={top_left[1]}"
    )

    print()

    wait_for_enter(
        "Maus auf UNTEN-RECHTS bewegen und ENTER drücken..."
    )

    bottom_right = get_mouse_position()

    print(
        f"Unten rechts gespeichert: "
        f"X={bottom_right[0]}, Y={bottom_right[1]}"
    )

    left = min(top_left[0], bottom_right[0])
    right = max(top_left[0], bottom_right[0])

    top = min(top_left[1], bottom_right[1])
    bottom = max(top_left[1], bottom_right[1])

    width = right - left
    height = bottom - top

    if width < 50 or height < 50:
        raise ValueError(
            "Der Zeichenbereich ist zu klein. "
            "Bitte mindestens 50x50 Pixel auswählen."
        )

    print()
    print("Zeichenbereich:")
    print(f"  Links:   {left}")
    print(f"  Oben:    {top}")
    print(f"  Rechts:  {right}")
    print(f"  Unten:   {bottom}")
    print(f"  Größe:   {width} x {height}")

    return left, top, right, bottom


# ============================================================
# KOORDINATEN-MAPPER
# ============================================================

def create_mapper(paths, drawing_area):
    image_min_x, image_min_y, image_max_x, image_max_y = (
        get_image_bounds(paths)
    )

    screen_left, screen_top, screen_right, screen_bottom = (
        drawing_area
    )

    image_width = image_max_x - image_min_x
    image_height = image_max_y - image_min_y

    area_width = screen_right - screen_left
    area_height = screen_bottom - screen_top

    if image_width <= 0:
        raise ValueError(
            f"Ungültige Bildbreite: {image_width}"
        )

    if image_height <= 0:
        raise ValueError(
            f"Ungültige Bildhöhe: {image_height}"
        )

    if area_width <= 0:
        raise ValueError(
            f"Ungültige Zeichenflächenbreite: {area_width}"
        )

    if area_height <= 0:
        raise ValueError(
            f"Ungültige Zeichenflächenhöhe: {area_height}"
        )

    # Seitenverhältnis beibehalten
    scale = min(
        area_width / image_width,
        area_height / image_height
    )

    if scale <= 0:
        raise ValueError(
            f"Ungültiger Skalierungsfaktor: {scale}"
        )

    scaled_width = image_width * scale
    scaled_height = image_height * scale

    # Bild zentrieren
    offset_x = (
        screen_left
        + (area_width - scaled_width) / 2
    )

    offset_y = (
        screen_top
        + (area_height - scaled_height) / 2
    )

    print()
    print("Bild-Koordinaten:")
    print(
        f"  X: {image_min_x:.1f} -> "
        f"{image_max_x:.1f}"
    )
    print(
        f"  Y: {image_min_y:.1f} -> "
        f"{image_max_y:.1f}"
    )

    print()
    print("Skalierung:")
    print(f"  Faktor: {scale:.3f}")
    print(
        f"  Ausgabe: "
        f"{scaled_width:.0f} x "
        f"{scaled_height:.0f}"
    )

    def map_point(point):
        image_x = point[0]
        image_y = point[1]

        normalized_x = image_x - image_min_x
        normalized_y = image_y - image_min_y

        screen_x = (
            offset_x
            + normalized_x * scale
        )

        screen_y = (
            offset_y
            + normalized_y * scale
        )

        return round(screen_x), round(screen_y)

    return map_point


# ============================================================
# ESC-NOT-AUS
# ============================================================

def start_escape_listener():
    def on_press(key):
        if key == keyboard.Key.esc:
            print()
            print()
            print(
                "!!! ESC GEDRÜCKT - "
                "ZEICHNEN WIRD ABGEBROCHEN !!!"
            )

            stop_event.set()

            return False

        return True

    listener = keyboard.Listener(
        on_press=on_press
    )

    listener.start()

    return listener


# ============================================================
# DISTANZ
# ============================================================

def distance(point_a, point_b):
    dx = point_b[0] - point_a[0]
    dy = point_b[1] - point_a[1]

    return math.hypot(dx, dy)


# ============================================================
# SICHERE MAUSBEWEGUNG
# ============================================================

def move_mouse_safely(
    target_x,
    target_y,
    current_position=None
):
    if stop_event.is_set():
        return False

    if current_position is None:
        current_position = get_mouse_position()

    current_x, current_y = current_position

    dist = distance(
        (current_x, current_y),
        (target_x, target_y)
    )

    # WICHTIG:
    # Keine Division durch 0 und keine zu kurze Dauer.
    if SPEED_PIXELS_PER_SECOND <= 0:
        raise ValueError(
            "SPEED_PIXELS_PER_SECOND muss größer als 0 sein."
        )

    if dist <= 0:
        return True

    duration = max(
        MIN_MOVE_DURATION,
        dist / float(SPEED_PIXELS_PER_SECOND)
    )

    pyautogui.moveTo(
        target_x,
        target_y,
        duration=duration
    )

    return not stop_event.is_set()


# ============================================================
# CURSOR-TEST
# ============================================================

def cursor_test(paths, map_point):
    test_count = min(
        TEST_PATHS,
        len(paths)
    )

    print()
    print("=" * 50)
    print("CURSOR-TEST")
    print("=" * 50)
    print()
    print(
        f"Es werden die ersten {test_count} "
        "Pfade abgefahren."
    )
    print()
    print("Die Maustaste wird NICHT gedrückt.")
    print("Es wird also noch NICHT gezeichnet.")
    print()
    print("ESC = sofort abbrechen")
    print()

    wait_for_enter(
        "ENTER drücken, um den Cursor-Test zu starten..."
    )

    stop_event.clear()

    print()
    print("Start in 3...")
    time.sleep(1)

    print("Start in 2...")
    time.sleep(1)

    print("Start in 1...")
    time.sleep(1)

    listener = start_escape_listener()

    try:
        for index, path in enumerate(
            paths[:test_count],
            start=1
        ):
            if stop_event.is_set():
                break

            print(
                f"Cursor-Test: "
                f"Pfad {index}/{test_count}"
            )

            if not path:
                continue

            first_point = map_point(path[0])

            if not move_mouse_safely(
                first_point[0],
                first_point[1]
            ):
                break

            previous_point = first_point

            for point in path[1:]:
                if stop_event.is_set():
                    break

                screen_point = map_point(point)

                if not move_mouse_safely(
                    screen_point[0],
                    screen_point[1],
                    previous_point
                ):
                    break

                previous_point = screen_point

            time.sleep(PATH_PAUSE)

    except pyautogui.FailSafeException:
        print()
        print("PyAutoGUI FAILSAFE ausgelöst.")

    finally:
        stop_event.set()

        try:
            listener.stop()
        except Exception:
            pass

    print()

    if stop_event.is_set():
        print("Cursor-Test beendet/abgebrochen.")
    else:
        print("Cursor-Test abgeschlossen.")


# ============================================================
# EINEN PFAD ZEICHNEN
# ============================================================

def draw_path(path, map_point):
    """
    Zeichnet einen einzelnen Pfad auf dem Bildschirm.

    Identische aufeinanderfolgende Punkte werden übersprungen,
    damit PyAutoGUI niemals eine Bewegung mit 0 Pixeln ausführen muss.
    """

    if not path:
        return False

    mapped_points = []

    # Alle Bildpunkte auf Bildschirmkoordinaten abbilden
    for point in path:
        try:
            screen_point = map_point(point)

            if screen_point is None:
                continue

            x = int(round(screen_point[0]))
            y = int(round(screen_point[1]))

            mapped_points.append((x, y))

        except Exception:
            continue

    if not mapped_points:
        return False

    # Doppelte aufeinanderfolgende Punkte entfernen
    clean_points = [mapped_points[0]]

    for point in mapped_points[1:]:
        if point != clean_points[-1]:
            clean_points.append(point)

    if not clean_points:
        return False

    # Zum ersten Punkt bewegen
    first_point = clean_points[0]

    # Beim Wechsel zwischen Konturen niemals mit gedrückter Maustaste fahren.
    pyautogui.mouseUp()

    current_position = pyautogui.position()

    if (
        current_position.x != first_point[0]
        or current_position.y != first_point[1]
    ):
        pyautogui.moveTo(
            first_point[0],
            first_point[1],
            duration=max(MIN_MOVE_DURATION, 0.001)
        )

    # Zeichnen
    pyautogui.mouseDown()

    try:
        for point in clean_points[1:]:

            # Sicherheitsabbruch
            if stop_event.is_set():
                return False

            current = pyautogui.position()

            dx = point[0] - current.x
            dy = point[1] - current.y

            distance = math.hypot(dx, dy)

            # WICHTIG:
            # Keine Bewegung ausführen, wenn wir bereits dort sind.
            if distance <= 0:
                continue

            duration = distance / SPEED_PIXELS_PER_SECOND

            duration = max(duration, MIN_MOVE_DURATION)

            pyautogui.moveTo(
                point[0],
                point[1],
                duration=duration
            )

    finally:
        pyautogui.mouseUp()

    return True


# ============================================================
# ECHTES ZEICHNEN
# ============================================================

def draw_image(paths, map_point):
    print()
    print("=" * 50)
    print("ECHTES ZEICHNEN")
    print("=" * 50)
    print()
    print(f"Zeichenpfade: {len(paths)}")
    print(
        f"Geschwindigkeit: "
        f"{SPEED_PIXELS_PER_SECOND} "
        "Pixel/Sekunde"
    )
    print()
    print("!!! NOT-AUS !!!")
    print("ESC drücken -> sofort abbrechen")
    print(
        "Maus ganz oben links -> "
        "zusätzlicher Not-Aus"
    )
    print()

    wait_for_enter(
        "ENTER drücken, um das echte "
        "Zeichnen zu starten..."
    )

    stop_event.clear()

    print()
    print("Zeichnen startet jetzt.")

    listener = start_escape_listener()

    completed_paths = 0

    try:
        for index, path in enumerate(
            paths,
            start=1
        ):
            if stop_event.is_set():
                break

            print(
                f"Zeichne Pfad "
                f"{index}/{len(paths)}",
                end="\r",
                flush=True
            )

            success = draw_path(
                path,
                map_point
            )

            if not success:
                break

            completed_paths += 1

            time.sleep(PATH_PAUSE)

    except pyautogui.FailSafeException:
        print()
        print()
        print(
            "PyAutoGUI FAILSAFE ausgelöst."
        )

    except KeyboardInterrupt:
        print()
        print()
        print(
            "Mit STRG+C abgebrochen."
        )

    finally:
        try:
            pyautogui.mouseUp()
        except Exception:
            pass

        stop_event.set()

        try:
            listener.stop()
        except Exception:
            pass

    print()
    print()

    if completed_paths == len(paths):
        print("=" * 50)
        print("ZEICHNEN ABGESCHLOSSEN")
        print("=" * 50)
    else:
        print("=" * 50)
        print("ZEICHNEN ABGEBROCHEN")
        print("=" * 50)

    print(
        f"Abgeschlossene Pfade: "
        f"{completed_paths}/{len(paths)}"
    )


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Verarbeitet ein Bild oder lädt eine JSON-Datei "
            "und zeichnet sie mit der Maus."
        )
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help=(
            "Bilddatei oder JSON-Datei mit Zeichenpfaden "
            "(ohne Angabe öffnet sich ein Dateiauswahldialog)"
        ),
    )

    args = parser.parse_args()

    print()
    print("=" * 50)
    print("       MOUSE DRAWING APP")
    print("=" * 50)
    print()

    try:
        if args.input_file:
            input_path = Path(args.input_file)
        else:
            from image_processor import select_image_file

            input_path = select_image_file()

            if input_path is None:
                print("Keine Datei ausgewählt.")
                return

        if input_path.suffix.lower() == ".json":
            paths_file = input_path
        else:
            from image_processor import process_image

            paths_file = input_path.with_name(
                f"{input_path.stem}_paths.json"
            )
            preview_path = input_path.with_name(
                f"{input_path.stem}_preview.png"
            )

            process_image(
                str(input_path),
                str(preview_path),
                str(paths_file),
            )

        print("Zeichenpfade werden geladen...")

        paths = load_paths(paths_file)

        point_count = sum(
            len(path)
            for path in paths
        )

        print(
            f"{len(paths)} "
            "Zeichenpfade geladen."
        )

        print(
            f"{point_count} "
            "Zeichenpunkte geladen."
        )

        drawing_area = select_drawing_area()

        map_point = create_mapper(
            paths,
            drawing_area
        )

        print()
        print("!!! WARNUNG !!!")
        print()
        print(
            "Jetzt wird die Maustaste tatsächlich "
            "gedrückt und das Bild gezeichnet."
        )
        print()
        print("Stelle sicher, dass:")
        print(
            "- das richtige Zeichenprogramm "
            "geöffnet ist"
        )
        print(
            "- die Zeichenfläche ausgewählt wurde"
        )
        print(
            "- die ausgewählte Fläche korrekt ist"
        )
        print()
        print("ESC = sofortiger Abbruch")
        print(
            "Maus oben links = "
            "zusätzlicher Not-Aus"
        )
        print()

        draw_image(
            paths,
            map_point
        )

    except FileNotFoundError as error:
        print()
        print("FEHLER:")
        print(error)

    except Exception as error:
        print()
        print("=" * 50)
        print("FEHLER")
        print("=" * 50)
        print()
        print(error)
        print()
        print("Details:")
        traceback.print_exc()

    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
