import json
import math
import threading
import time
from pathlib import Path

import pyautogui
from pynput import keyboard


# ============================================================
# EINSTELLUNGEN
# ============================================================

PATHS_FILE = Path("images/auto_paths.json")

SPEED_PIXELS_PER_SECOND = 800
PATH_PAUSE = 0.02
TEST_PATHS = 5

pyautogui.PAUSE = 0.01
pyautogui.MINIMUM_DURATION = 0.0

# Maus ganz oben links = zusätzlicher Not-Aus
pyautogui.FAILSAFE = True

stop_event = threading.Event()


# ============================================================
# ZEICHENPFADE LADEN
# ============================================================

def load_paths():
    if not PATHS_FILE.exists():
        raise FileNotFoundError(
            f"Datei nicht gefunden: {PATHS_FILE}\n"
            "Bitte zuerst image_processor.py ausführen."
        )

    with open(PATHS_FILE, "r", encoding="utf-8") as file:
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

    # Das vorhandene JSON-Format:
    #
    # {
    #   "paths": [
    #       [
    #           {"x": 283, "y": 185},
    #           {"x": 283, "y": 296}
    #       ]
    #   ]
    # }

    paths = []

    for raw_path in raw_paths:
        path = []

        for point in raw_path:
            if not isinstance(point, dict):
                continue

            if "x" not in point or "y" not in point:
                continue

            x = float(point["x"])
            y = float(point["y"])

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


def print_mouse_position():
    x, y = get_mouse_position()
    print(f"Mausposition: X={x}, Y={y}")


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
    print("1. Bewege die Maus auf die OBERE LINKE Ecke.")
    print("2. Drücke ENTER im Terminal.")
    print("3. Bewege die Maus auf die UNTERE RECHTE Ecke.")
    print("4. Drücke wieder ENTER.")
    print()

    input(
        "Maus auf OBEN-LINKS bewegen und ENTER drücken..."
    )

    top_left = get_mouse_position()

    print(
        f"Oben links gespeichert: "
        f"X={top_left[0]}, Y={top_left[1]}"
    )

    print()

    input(
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

    if image_width <= 0 or image_height <= 0:
        raise ValueError(
            "Ungültige Bildabmessungen."
        )

    # Seitenverhältnis erhalten.
    scale = min(
        area_width / image_width,
        area_height / image_height
    )

    scaled_width = image_width * scale
    scaled_height = image_height * scale

    # Bild im Zeichenbereich zentrieren.
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

    return math.sqrt(
        dx * dx + dy * dy
    )


# ============================================================
# MAUS BEWEGEN
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

    duration = max(
        0.001,
        dist / SPEED_PIXELS_PER_SECOND
    )

    pyautogui.moveTo(
        target_x,
        target_y,
        duration=duration
    )

    return True


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
    print("WICHTIG:")
    print("Die Maustaste wird NICHT gedrückt.")
    print("Es wird also noch NICHT gezeichnet.")
    print()
    print("ESC = sofort abbrechen")
    print()

    input(
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
            paths[:TEST_PATHS],
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

            first_point = map_point(
                path[0]
            )

            if not move_mouse_safely(
                first_point[0],
                first_point[1]
            ):
                break

            for point in path[1:]:
                if stop_event.is_set():
                    break

                screen_point = map_point(
                    point
                )

                if not move_mouse_safely(
                    screen_point[0],
                    screen_point[1]
                ):
                    break

            time.sleep(PATH_PAUSE)

    except pyautogui.FailSafeException:
        print()
        print(
            "PyAutoGUI FAILSAFE ausgelöst."
        )

    finally:
        stop_event.set()

        try:
            listener.stop()
        except Exception:
            pass

    print()

    if stop_event.is_set():
        print(
            "Cursor-Test beendet/abgebrochen."
        )
    else:
        print(
            "Cursor-Test abgeschlossen."
        )


# ============================================================
# ECHTES ZEICHNEN
# ============================================================

def draw_path(path, map_point):
    if stop_event.is_set():
        return False

    if not path:
        return True

    first_screen_point = map_point(
        path[0]
    )

    # Zum Anfang des Pfades bewegen.
    if not move_mouse_safely(
        first_screen_point[0],
        first_screen_point[1]
    ):
        return False

    if stop_event.is_set():
        return False

    # Maustaste drücken.
    pyautogui.mouseDown()

    try:
        previous_point = first_screen_point

        for point in path[1:]:
            if stop_event.is_set():
                return False

            screen_point = map_point(
                point
            )

            dist = distance(
                previous_point,
                screen_point
            )

            duration = max(
                0.001,
                dist / SPEED_PIXELS_PER_SECOND
            )

            pyautogui.moveTo(
                screen_point[0],
                screen_point[1],
                duration=duration
            )

            previous_point = screen_point

    finally:
        # Sicherheitshalber immer loslassen.
        pyautogui.mouseUp()

    return not stop_event.is_set()


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

    input(
        "ENTER drücken, um das echte "
        "Zeichnen zu starten..."
    )

    stop_event.clear()

    print()
    print(
        "ACHTUNG: Zeichnen startet in 5 Sekunden."
    )
    print()

    for countdown in range(5, 0, -1):
        if stop_event.is_set():
            return

        print(f"{countdown}...")
        time.sleep(1)

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
    print()
    print("=" * 50)
    print("       MOUSE DRAWING APP")
    print("=" * 50)
    print()

    try:
        # ----------------------------------------------------
        # Pfade laden
        # ----------------------------------------------------

        print(
            "Zeichenpfade werden geladen..."
        )

        paths = load_paths()

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

        # ----------------------------------------------------
        # Zeichenbereich
        # ----------------------------------------------------

        drawing_area = select_drawing_area()

        # ----------------------------------------------------
        # Mapper
        # ----------------------------------------------------

        map_point = create_mapper(
            paths,
            drawing_area
        )

        # ----------------------------------------------------
        # Menü
        # ----------------------------------------------------

        print()
        print("=" * 50)
        print("AUSWAHL")
        print("=" * 50)
        print()
        print("1 = Cursor-Test")
        print("2 = Echtes Zeichnen")
        print("3 = Beenden")
        print()

        choice = input(
            "Auswahl: "
        ).strip()

        if choice == "1":
            stop_event.clear()

            cursor_test(
                paths,
                map_point
            )

        elif choice == "2":
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

            confirmation = input(
                "Zum Bestätigen exakt JA eingeben: "
            ).strip()

            if confirmation != "JA":
                print()
                print("Abgebrochen.")
                return

            draw_image(
                paths,
                map_point
            )

        elif choice == "3":
            print()
            print("Programm beendet.")

        else:
            print()
            print("Ungültige Auswahl.")

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


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()