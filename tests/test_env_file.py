from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE_SH = ROOT / "scripts" / "env_file.sh"
BASH = shutil.which("bash")


@unittest.skipUnless(BASH, "bash is required to exercise the shell parser")
class EnvFileParserTests(unittest.TestCase):
    def load(self, contents: str, key: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(contents, encoding="utf-8", newline="\n")
            script = (
                f'. "{ENV_FILE_SH.as_posix()}"\n'
                f'nighty_load_env_file "{env_path.as_posix()}"\n'
                f'printf "%s" "${{{key}-<<unset>>}}"\n'
            )
            result = subprocess.run(
                [BASH, "-c", script],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout

    def test_dollar_signs_are_kept_literal(self) -> None:
        self.assertEqual(self.load("WEBUI_PASSWORD=p@$$w0rd\n", "WEBUI_PASSWORD"), "p@$$w0rd")

    def test_command_substitution_is_not_executed(self) -> None:
        self.assertEqual(
            self.load("WEBUI_PASSWORD=a$(id -u)b\n", "WEBUI_PASSWORD"),
            "a$(id -u)b",
        )

    def test_backticks_are_not_executed(self) -> None:
        self.assertEqual(
            self.load("WEBUI_PASSWORD=a`id -u`b\n", "WEBUI_PASSWORD"),
            "a`id -u`b",
        )

    def test_unquoted_spaces_are_preserved(self) -> None:
        self.assertEqual(
            self.load("NIGHTY_HOME=/home/my user/.local/share/nighty\n", "NIGHTY_HOME"),
            "/home/my user/.local/share/nighty",
        )

    def test_surrounding_quotes_are_stripped(self) -> None:
        self.assertEqual(self.load('WEBUI_USERNAME="admin"\n', "WEBUI_USERNAME"), "admin")
        self.assertEqual(self.load("WEBUI_USERNAME='admin'\n", "WEBUI_USERNAME"), "admin")

    def test_comments_and_blank_lines_are_skipped(self) -> None:
        contents = "# a comment\n\n   # indented comment\nBRIDGE_PORT=8088\n"
        self.assertEqual(self.load(contents, "BRIDGE_PORT"), "8088")

    def test_export_prefix_is_accepted(self) -> None:
        self.assertEqual(self.load("export BRIDGE_PORT=8088\n", "BRIDGE_PORT"), "8088")

    def test_values_are_exported_to_child_processes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("WEBUI_PASSWORD=p@$$w0rd\n", encoding="utf-8", newline="\n")
            script = (
                f'. "{ENV_FILE_SH.as_posix()}"\n'
                f'nighty_load_env_file "{env_path.as_posix()}"\n'
                "printenv WEBUI_PASSWORD\n"
            )
            result = subprocess.run([BASH, "-c", script], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "p@$$w0rd")

    def test_malformed_lines_are_ignored(self) -> None:
        contents = "not an assignment\nBAD-KEY=x\nBRIDGE_PORT=8088\n"
        self.assertEqual(self.load(contents, "BRIDGE_PORT"), "8088")

    def test_missing_file_is_not_an_error(self) -> None:
        script = (
            f'. "{ENV_FILE_SH.as_posix()}"\n'
            'nighty_load_env_file "/nonexistent/path/.env"\n'
            'printf "ok"\n'
        )
        result = subprocess.run([BASH, "-c", script], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "ok")


class EnvFileCallSiteTests(unittest.TestCase):
    def test_no_entry_point_sources_the_env_file_as_shell(self) -> None:
        names = ("run.sh", "install.sh", "uninstall.sh", "add_account.sh")
        checked = [(n, (ROOT / "scripts" / n).read_text(encoding="utf-8")) for n in names]
        offenders = [n for n, t in checked if "set -a" in t]
        self.assertEqual(offenders, [], f"still evaluate .env as shell: {offenders}")

    def test_every_entry_point_uses_the_literal_parser(self) -> None:
        names = ("run.sh", "install.sh", "uninstall.sh", "add_account.sh")
        missing = [
            n for n in names
            if "nighty_load_env_file" not in (ROOT / "scripts" / n).read_text(encoding="utf-8")
        ]
        self.assertEqual(missing, [], f"do not load .env via the parser: {missing}")


if __name__ == "__main__":
    unittest.main()
