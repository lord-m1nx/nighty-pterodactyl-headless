from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = ROOT / "scripts" / "install.sh"
UNINSTALL_SH = ROOT / "scripts" / "uninstall.sh"
RUN_SH = ROOT / "scripts" / "run.sh"
BASH = shutil.which("bash")
SED = shutil.which("sed")

BLACKHOLE_IP = "192.0.2.1"
RP_HOSTS = ("lrclib.net", "api.lrclib.net", "api.spotify.com")

LEGACY_HOSTS = """127.0.0.1 localhost
127.0.1.1 examplehost

# nighty-linux-headless: RP-fetch blackhole (lyrics/now-playing fetches freeze the bot under emulation)
0.0.0.0 lrclib.net
0.0.0.0 api.lrclib.net
0.0.0.0 api.spotify.com
"""


class BlackholeAddressTests(unittest.TestCase):
    def test_installer_no_longer_maps_rp_hosts_to_a_local_address(self) -> None:
        text = INSTALL_SH.read_text(encoding="utf-8")
        self.assertIn(f'RP_BLACKHOLE_IP="{BLACKHOLE_IP}"', text)
        self.assertNotIn("printf '0.0.0.0 %s\\n'", text)

    def test_installer_adds_an_unreachable_route(self) -> None:
        text = INSTALL_SH.read_text(encoding="utf-8")
        self.assertIn("ip route replace unreachable", text)

    def test_runtime_warning_checks_the_new_address(self) -> None:
        text = RUN_SH.read_text(encoding="utf-8")
        self.assertIn("192\\.0\\.2\\.1", text)
        self.assertNotIn(
            "0\\.0\\.0\\.0[[:space:]]+(api\\.)?lrclib\\.net",
            text,
            "run.sh still warns based on the old blackhole address",
        )

    def test_uninstaller_removes_every_blackhole_address(self) -> None:
        text = UNINSTALL_SH.read_text(encoding="utf-8")
        for token in ("0\\.0\\.0\\.0", "127\\.0\\.0\\.1", "192\\.0\\.2\\.1"):
            self.assertIn(token, text)
        self.assertIn("nighty-rp-blackhole.service", text)


@unittest.skipUnless(BASH and SED, "bash and sed are required")
class LegacyEntryMigrationTests(unittest.TestCase):
    def migrate(self, hosts_text: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            hosts = Path(tmp) / "hosts"
            hosts.write_text(hosts_text, encoding="utf-8", newline="\n")
            script = f'''
set -eu
hosts_file="{hosts.as_posix()}"
RP_BLACKHOLE_IP="{BLACKHOLE_IP}"
RP_BLACKHOLE_IP_RE="192\\\\.0\\\\.2\\\\.1"
for host in {" ".join(RP_HOSTS)}; do
  host_re="$(printf '%s' "$host" | sed 's/\\./\\\\./g')"
  if grep -Eq "^[[:space:]]*(0\\.0\\.0\\.0|127\\.0\\.0\\.1)[[:space:]]+$host_re([[:space:]]|$)" "$hosts_file" 2>/dev/null; then
    sed -i -E "/^[[:space:]]*(0\\.0\\.0\\.0|127\\.0\\.0\\.1)[[:space:]]+$host_re([[:space:]]|\\$)/d" "$hosts_file"
  fi
  if ! grep -Eq "^[[:space:]]*$RP_BLACKHOLE_IP_RE[[:space:]]+$host_re([[:space:]]|$)" "$hosts_file" 2>/dev/null; then
    printf '%s %s\\n' "$RP_BLACKHOLE_IP" "$host" >> "$hosts_file"
  fi
done
'''
            result = subprocess.run([BASH, "-c", script], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            return hosts.read_text(encoding="utf-8")

    def first_mapping_for(self, hosts_text: str, host: str) -> str:
        pattern = re.compile(r"^\s*(\S+)\s+" + re.escape(host) + r"\s*$", re.MULTILINE)
        match = pattern.search(hosts_text)
        self.assertIsNotNone(match, f"no mapping found for {host}")
        return match.group(1)

    def test_legacy_zero_address_entries_are_replaced_not_duplicated(self) -> None:
        migrated = self.migrate(LEGACY_HOSTS)
        for host in RP_HOSTS:
            occurrences = re.findall(r"^\s*\S+\s+" + re.escape(host) + r"\s*$", migrated, re.MULTILINE)
            self.assertEqual(len(occurrences), 1, f"{host} has {len(occurrences)} mappings: {occurrences}")
            self.assertEqual(self.first_mapping_for(migrated, host), BLACKHOLE_IP)
        self.assertNotIn("0.0.0.0 lrclib.net", migrated)

    def test_unrelated_entries_are_left_alone(self) -> None:
        migrated = self.migrate(LEGACY_HOSTS)
        self.assertIn("127.0.0.1 localhost", migrated)
        self.assertIn("127.0.1.1 examplehost", migrated)

    def test_migration_is_idempotent(self) -> None:
        once = self.migrate(LEGACY_HOSTS)
        twice = self.migrate(once)
        self.assertEqual(once, twice)

    def test_a_clean_hosts_file_gains_the_mappings(self) -> None:
        migrated = self.migrate("127.0.0.1 localhost\n")
        for host in RP_HOSTS:
            self.assertEqual(self.first_mapping_for(migrated, host), BLACKHOLE_IP)


if __name__ == "__main__":
    unittest.main()
