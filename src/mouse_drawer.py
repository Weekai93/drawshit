import time

import pyautogui


# ---------------------------------------------------------
# Einstellungen
# ---------------------------------------------------------

TEST_DISTANCE = 100
TEST_DURATION = 1.0


# ---------------------------------------------------------
# Mausfunktionen
# ---------------------------------------------------------

def get_mouse_position():
    """Gibt die aktuelle Mausposition zurück."""

    x, y = pyautogui.position()

    return x, y


def print_mouse_position():
    """Zeigt die aktuelle Mausposition an."""

    x, y = get_mouse_position()

    print(f"Mausposition: X={x}, Y={y}")


def test_mouse_movement():
    """
    Bewegt die Maus kontrolliert ein kleines Stück
    nach rechts und anschließend wieder zurück.
    """

    print()
    print("Mausbewegung wird vorbereitet.")
    print("Die Maus bewegt sich gleich 100 Pixel nach rechts.")
    print("")

    # Kurze Sicherheitsverzögerung
    for seconds in range(3, 0, -1):
        print(f"Start in {seconds}...")
        time.sleep(1)

    start_x, start_y = get_mouse_position()

    print(
        f"Startposition: X={start_x}, Y={start_y}"
    )

    target_x = start_x + TEST_DISTANCE

    print(
        f"Zielposition: X={target_x}, Y={start_y}"
    )

    # Langsame, kontrollierte Bewegung
    pyautogui.moveTo(
        target_x,
        start_y,
        duration=TEST_DURATION,
    )

    print("Hinbewegung abgeschlossen.")

    time.sleep(0.5)

    # Wieder zurück
    pyautogui.moveTo(
        start_x,
        start_y,
        duration=TEST_DURATION,
    )

    print("Rückbewegung abgeschlossen.")

    print()
    print("Maus-Test abgeschlossen.")


# ---------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------

def main():
    print("================================")
    print("       MOUSE DRAWING APP")
    print("================================")
    print()

    print("Aktuelle Mausposition:")
    print_mouse_position()

    print()
    print("Hinweis:")
    print("Dieser Test bewegt die Maus nur 100 Pixel")
    print("nach rechts und anschließend zurück.")
    print()

    test_mouse_movement()


if __name__ == "__main__":
    main()