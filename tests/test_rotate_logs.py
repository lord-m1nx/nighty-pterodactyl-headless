import tempfile
import unittest
from pathlib import Path

from scripts import rotate_logs


class RotateLogsTests(unittest.TestCase):
    def test_log_below_limit_is_not_rotated(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "backend.log"
            log_file.write_text("small log content\n", encoding="utf-8")
            rotated = rotate_logs.rotate_log_file(log_file, max_bytes=1024, max_backups=3)
            self.assertFalse(rotated)
            self.assertTrue(log_file.is_file())
            self.assertEqual(log_file.read_text(encoding="utf-8"), "small log content\n")
            self.assertFalse((Path(tmp) / "backend.log.1").exists())

    def test_log_above_limit_is_rotated(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "backend.log"
            log_file.write_text("x" * 2000, encoding="utf-8")
            rotated = rotate_logs.rotate_log_file(log_file, max_bytes=1000, max_backups=3)
            self.assertTrue(rotated)
            self.assertTrue(log_file.is_file())
            self.assertEqual(log_file.stat().st_size, 0)
            backup1 = Path(tmp) / "backend.log.1"
            self.assertTrue(backup1.is_file())
            self.assertEqual(len(backup1.read_text(encoding="utf-8")), 2000)

    def test_multiple_rotations_shift_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "backend.log"
            # First rotation
            log_file.write_text("log round 1", encoding="utf-8")
            rotate_logs.rotate_log_file(log_file, max_bytes=5, max_backups=3)

            # Second rotation
            log_file.write_text("log round 2", encoding="utf-8")
            rotate_logs.rotate_log_file(log_file, max_bytes=5, max_backups=3)

            self.assertEqual((Path(tmp) / "backend.log.1").read_text(encoding="utf-8"), "log round 2")
            self.assertEqual((Path(tmp) / "backend.log.2").read_text(encoding="utf-8"), "log round 1")

    def test_all_diagnostics_targets_rotated(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for name in ["backend.log", "bridge.log", "guard.log", "xvfb.log", "stub_webview.log", "nighty.log"]:
                p = tmp_path / name
                p.write_text("a" * 500, encoding="utf-8")
                self.assertTrue(rotate_logs.rotate_log_file(p, max_bytes=100, max_backups=2))
                self.assertTrue((tmp_path / f"{name}.1").is_file())


    def test_open_appending_writer_keeps_writing_to_the_live_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_file = Path(tmp) / "backend.log"
            log_file.write_text("x" * 2000, encoding="utf-8")
            with open(log_file, "a", encoding="utf-8") as writer:
                rotated = rotate_logs.rotate_log_file(log_file, max_bytes=1000, max_backups=3)
                self.assertTrue(rotated)
                writer.write("LINE AFTER ROTATION\n")
                writer.flush()
            self.assertIn("LINE AFTER ROTATION", log_file.read_text(encoding="utf-8"))
            backup1 = Path(tmp) / "backend.log.1"
            self.assertNotIn("LINE AFTER ROTATION", backup1.read_text(encoding="utf-8"))

    def test_backend_owned_logs_are_never_targeted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prefix = root / "prefix" / "drive_c" / "users" / "nighty" / "AppData" / "Roaming" / "Nighty Selfbot"
            prefix.mkdir(parents=True)
            (prefix / "nighty.log").write_text("owned by the backend\n", encoding="utf-8")
            diag = root / "diagnostics"
            diag.mkdir()
            (diag / "nighty.log").write_text("mirror\n", encoding="utf-8")
            targets = rotate_logs.wrapper_owned_logs(diag, root)
            self.assertIn(diag / "nighty.log", targets)
            for target in targets:
                self.assertNotIn("drive_c", target.parts)


if __name__ == "__main__":
    unittest.main()
