from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nighty_preflight_triage", ROOT / "scripts" / "preflight.py")
assert SPEC and SPEC.loader
PREFLIGHT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREFLIGHT)

RUN_SH = ROOT / "scripts" / "run.sh"
BACKOFF_SH = ROOT / "scripts" / "backoff.sh"
BASH = shutil.which("bash")

ISSUE_13_LOG = """[STUBWV] control server on 127.0.0.1:8765
DLL load failed while importing QtWidgets: Module not found.
DLL load failed while importing QtWidgets: Module not found.
cannot import name '_imaging' from 'PIL' (C:\\users\\nighty\\AppData\\Local\\Temp\\_MEI322\\PIL\\__init__.py)
"""


class KnownFailureScanTests(unittest.TestCase):
    def test_issue_13_signatures_are_both_recognised(self) -> None:
        found = {f["id"] for f in PREFLIGHT.scan_known_failures(ISSUE_13_LOG)}
        self.assertIn("bundled-extension-dll", found)
        self.assertIn("pillow-imaging", found)

    def test_advice_states_the_cause_is_not_wrapper_configuration(self) -> None:
        findings = PREFLIGHT.scan_known_failures(ISSUE_13_LOG)
        advice = " ".join(f["advice"] for f in findings)
        self.assertIn("#13", advice)
        self.assertIn("frozen binary", advice)

    def test_a_healthy_log_matches_nothing(self) -> None:
        healthy = "[STUBWV] control server on 127.0.0.1:8765\nLogged in successfully\nCommands synced\n"
        self.assertEqual(PREFLIGHT.scan_known_failures(healthy), [])

    def test_empty_input_is_safe(self) -> None:
        self.assertEqual(PREFLIGHT.scan_known_failures(""), [])

    def test_other_known_signatures(self) -> None:
        cases = {
            "bad-exe-format": "wine: Bad EXE format for Z:\\app\\Nighty_stub.exe.",
            "bad-marshal-data": "ValueError: bad marshal data (unknown type code)",
            "missing-license": "KeyError('motd')",
            "wine-module-import": "err:module:import_dll Library VCRUNTIME140.dll not found",
        }
        for expected, line in cases.items():
            found = {f["id"] for f in PREFLIGHT.scan_known_failures(line)}
            self.assertIn(expected, found, f"{expected} not matched by: {line}")


class TriageCommandTests(unittest.TestCase):
    def test_triage_reports_findings_from_a_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "backend.log"
            log.write_text(ISSUE_13_LOG, encoding="utf-8")
            self.assertEqual(PREFLIGHT.main(["triage", "--log", str(log)]), 0)

    def test_triage_on_a_missing_log_is_not_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent.log"
            self.assertEqual(PREFLIGHT.main(["triage", "--log", str(missing)]), 0)

    def test_triage_redacts_a_token_inside_a_matched_line(self) -> None:
        raw = "KeyError('motd') token: MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.ABCDEF.GHIJKLMNOPQRSTUVWXYZ12345"
        findings = PREFLIGHT.scan_known_failures(raw)
        for item in findings:
            self.assertNotIn("GHIJKLMNOPQRSTUVWXYZ12345", PREFLIGHT.redact_secrets(item["match"]))


@unittest.skipUnless(BASH, "bash is required to evaluate the backoff arithmetic")
class BackendBackoffTests(unittest.TestCase):
    def backoff_for(self, failures, cap=300):
        script = (
            '. "' + BACKOFF_SH.as_posix() + '"' + chr(10)
            + 'nighty_relaunch_delay ' + str(failures) + ' ' + str(cap) + chr(10)
        )
        result = subprocess.run([BASH, "-c", script], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return int(result.stdout)

    def test_first_exit_keeps_the_original_three_second_delay(self) -> None:
        self.assertEqual(self.backoff_for(0), 3)
        self.assertEqual(self.backoff_for(1), 3)

    def test_repeated_fast_exits_back_off(self) -> None:
        self.assertEqual(self.backoff_for(2), 6)
        self.assertEqual(self.backoff_for(3), 12)
        self.assertEqual(self.backoff_for(4), 24)

    def test_backoff_is_capped(self) -> None:
        self.assertEqual(self.backoff_for(20), 300)
        self.assertEqual(self.backoff_for(64), 300)

    def test_backoff_never_goes_negative_on_a_long_outage(self) -> None:
        for failures in (62, 63, 64, 65, 200, 4096):
            delay = self.backoff_for(failures)
            self.assertGreater(delay, 0, f"{failures} consecutive failures produced {delay}")
            self.assertLessEqual(delay, 300)

    def test_run_sh_wires_the_backoff_and_triage(self) -> None:
        text = RUN_SH.read_text(encoding="utf-8")
        self.assertIn("BACKEND_FAST_FAIL_SECONDS", text)
        self.assertIn("nighty_relaunch_delay", text)
        self.assertIn('preflight.py" triage', text)
        self.assertNotIn("relaunching in 3s (persistence)", text)


if __name__ == "__main__":
    unittest.main()
