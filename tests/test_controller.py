import unittest
from unittest.mock import patch

import main


class FakeKey:
    space = "SPACE"
    shift = "SHIFT"
    ctrl = "CTRL"
    alt = "ALT"


class FakeKeyCode:
    @staticmethod
    def from_char(value):
        return value.upper()


class FakeController:
    def __init__(self):
        self.pressed = set()
        self.events = []

    def press(self, key):
        self.pressed.add(key)
        self.events.append(("press", key))

    def release(self, key):
        self.pressed.discard(key)
        self.events.append(("release", key))


class FakeKeyboard:
    Key = FakeKey
    KeyCode = FakeKeyCode

    def __init__(self):
        self.instance = FakeController()

    def Controller(self):
        return self.instance


class JumpControllerTests(unittest.TestCase):
    def setUp(self):
        self.fake_keyboard = FakeKeyboard()
        self.patch = patch.object(main, "keyboard", self.fake_keyboard)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.jump = main.JumpController("SPACE")

    def test_hold_is_idempotent(self):
        self.jump.hold()
        self.jump.hold()
        self.assertEqual(self.fake_keyboard.instance.events, [("press", "SPACE")])
        self.assertTrue(self.jump.active)

    def test_release_is_idempotent(self):
        self.jump.hold()
        self.jump.release()
        self.jump.release()
        self.assertEqual(
            self.fake_keyboard.instance.events,
            [("press", "SPACE"), ("release", "SPACE")],
        )
        self.assertFalse(self.jump.active)

    def test_toggle_switches_state(self):
        self.jump.toggle()
        self.assertTrue(self.jump.active)
        self.jump.toggle()
        self.assertFalse(self.jump.active)

    def test_changing_key_while_active_releases_old_and_holds_new(self):
        self.jump.hold()
        self.jump.set_key("W")
        self.assertEqual(
            self.fake_keyboard.instance.events,
            [("press", "SPACE"), ("release", "SPACE"), ("press", "W")],
        )
        self.assertEqual(self.fake_keyboard.instance.pressed, {"W"})


if __name__ == "__main__":
    unittest.main()
