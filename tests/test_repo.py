import json
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
sys.path.insert(0, str(ROOT / "dev"))
import sync  # noqa: E402


class Copies(unittest.TestCase):
    def test_every_skill_copy_matches_its_source(self):
        stale = [str(dst.relative_to(ROOT)) for src, dst in sync.targets()
                 if not dst.exists() or dst.read_bytes() != src.read_bytes()]
        self.assertEqual(stale, [], "run: python3 dev/sync.py")

    def test_eval_scenarios_are_self_contained(self):
        for f in SKILLS.glob("*/evals/scenarios.json"):
            skill = f.parents[1]
            for sc in json.loads(f.read_text(encoding="utf-8")):
                self.assertEqual(sc["skills"], [skill.name], f)
                for fixture in sc["files"]:
                    self.assertTrue((skill / fixture).exists(), (f, fixture))
        for cfg in SKILLS.glob("*/evals/fixtures/*.toml"):
            with cfg.open("rb") as fh:
                self.assertTrue(tomllib.load(fh)["labels"]["allowed"], cfg)


class Config(unittest.TestCase):
    def test_example_config_parses(self):
        with (ROOT / "config.example.toml").open("rb") as fh:
            cfg = tomllib.load(fh)
        self.assertEqual(cfg["labels"]["selection"], "multiple")
        self.assertIn("write", cfg["labels"]["allowed"])


class Routes(unittest.TestCase):
    def test_no_todoist_route_is_preferred(self):
        # Neither MCP nor td may be the default: the user names one, or settings do, or the skill asks.
        for skill_md in SKILLS.glob("*/SKILL.md"):
            text = skill_md.read_text(encoding="utf-8")
            self.assertNotIn("if available", text, skill_md)
            self.assertNotIn("then the authenticated", text, skill_md)


if __name__ == "__main__":
    unittest.main()
