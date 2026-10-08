import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("judge_entry", ROOT / "track_2b/src/judge_entry.py")
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


class JudgePackageTests(unittest.TestCase):
    def test_official_environment_reaches_existing_client(self):
        env = {"LLM_NAME": "swiss-ai/Apertus-v1.5-70B", "LLM_BASE_URL": "http://localhost:9000/v1", "LLM_API_KEY": "synthetic-test-value"}
        entry.configure(env)
        self.assertEqual(env["APERTUS_MODEL"], env["LLM_NAME"])
        self.assertEqual(env["APERTUS_BASE_URL"], env["LLM_BASE_URL"])
        self.assertEqual(env["APERTUS_API_KEY"], env["LLM_API_KEY"])
        self.assertEqual(env["APERTUS_MODE"], "live")

    def test_missing_live_configuration_never_silently_mocks(self):
        with self.assertRaises(ValueError):
            entry.configure({})
        env = {"APERTUS_MODE": "mock"}
        entry.configure(env)
        self.assertEqual(env["APERTUS_MODE"], "mock")

    def test_package_has_exact_public_runtime_sources(self):
        for directory, pattern in (("app", "*.py"), ("static", "*.html")):
            originals = {p.name: p.read_bytes() for p in (ROOT / directory).glob(pattern)}
            packaged = {p.name: p.read_bytes() for p in (ROOT / "track_2b/src" / directory).glob(pattern)}
            self.assertEqual(originals, packaged)


if __name__ == "__main__":
    unittest.main()
