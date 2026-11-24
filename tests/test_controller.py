import unittest
from unittest.mock import patch

import main


class AutoJumpSettingsTests(unittest.TestCase):
    def test_interval_is_clamped_to_supported_range(self):
        with patch.object(main.keyboard, "Controller", return_value=object()):
            jump = main.AutoJump(20)
            self.assertEqual(jump.interval_ms, main.MIN_INTERVAL_MS)
            jump.close()

    def test_interval_can_be_updated(self):
        with patch.object(main.keyboard, "Controller", return_value=object()):
            jump = main.AutoJump(450)
            jump.set_interval(700)
            self.assertEqual(jump.interval_ms, 700)
            jump.close()

    def test_enabled_state_can_be_toggled(self):
        with patch.object(main.keyboard, "Controller", return_value=object()):
            jump = main.AutoJump()
            jump.set_enabled(True)
            self.assertTrue(jump.enabled)
            jump.set_enabled(False)
            self.assertFalse(jump.enabled)
            jump.close()


if __name__ == "__main__":
    unittest.main()
