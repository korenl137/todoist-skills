import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
sys.path.insert(0, str(ROOT / "dev"))  # jevlib for the scripts below: every skill's copy is identical

import jevlib  # noqa: E402
import sync  # noqa: E402


def load(skill, name):
    spec = importlib.util.spec_from_file_location(name, SKILLS / skill / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


jev_place = load("todo-add", "jev_place")
jev_find = load("todo-find", "jev_find")
jev_audit = load("todo-doctor", "jev_audit")

CONFIG = """
[labels]
required_prefix = "kind/"
ignore = ["imported"]
[labels.allowed]
"kind/write" = "write a document"
"kind/buy" = "buy something"
"topic/food" = "food or cooking"
[labels.projects]
"project/community-site" = "the community site"
[areas]
Personal = "home and hobbies"
Work = "job projects"
[jev]
enabled = true
"""


def config(text=CONFIG):
    f = tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False, encoding="utf-8")
    f.write(text)
    f.close()
    return jevlib.load_config(f.name)


def answers(vague=0.1, area="Personal", conf=0.9, plabel=None):
    a = {"vague": {"noul": vague}, "area": {"choice": area, "confidence": conf}}
    if plabel is not None:
        a["plabel0"] = {"noul": plabel}
    return a


class Config(unittest.TestCase):
    def test_missing_file_means_defaults(self):
        cfg = jevlib.load_config(ROOT / "no-such-config.toml")
        self.assertFalse(cfg["jev"]["enabled"])
        self.assertIsNone(jevlib.allowlist(cfg))
        self.assertEqual(jevlib.acts(cfg), {})

    def test_label_groups(self):
        cfg = config()
        self.assertEqual(sorted(jevlib.acts(cfg)), ["kind/buy", "kind/write"])
        self.assertEqual(sorted(jevlib.extras(cfg)), ["topic/food"])
        self.assertIn("imported", jevlib.allowlist(cfg))

    def test_example_config_parses(self):
        cfg = jevlib.load_config(ROOT / "config.example.toml")
        self.assertFalse(cfg["jev"]["enabled"])
        self.assertIn("kind/write", jevlib.acts(cfg))

    def test_scripts_exit_3_when_jev_not_enabled(self):
        env = {**os.environ, "TODOIST_SKILLS_CONFIG": str(ROOT / "no-such-config.toml")}
        for skill, script in (("todo-add", "jev_place"), ("todo-find", "jev_find"), ("todo-doctor", "jev_audit")):
            r = subprocess.run([sys.executable, str(SKILLS / skill / "scripts" / f"{script}.py"), "x"],
                               input="{}", capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 3, (script, r.stderr))


class Audit(unittest.TestCase):
    def test_rule_checks_and_thresholds(self):
        cfg = config()
        tasks = [
            {"id": "1", "title": "Replace razor", "project": "Personal / Home", "labels": ["old-shopping"]},
            {"id": "2", "title": "Stuff", "project": "Personal / Hobby", "labels": ["kind/write"]},
            {"id": "3", "title": "Pay rent", "project": "Work / Admin", "labels": ["kind/buy", "project/community-site"]},
            {"id": "4", "title": "Read a recipe", "project": "Personal / Home", "labels": ["kind/write", "imported"]},
            {"id": "5", "title": "Sort inbox", "project": "Inbox", "labels": ["kind/write"]},
            {"id": "6", "title": "Group: Event planning", "project": "Work / Events", "labels": [], "has_children": True},
        ]
        out = jev_audit.audit(tasks, [
            answers(),
            answers(vague=0.85),
            answers(plabel=0.2),                  # area Personal, but filed in Work
            answers(area="Work", conf=0.79),      # below MISMATCH_CONF: not reported
            answers(area="Work", conf=1.0),       # project outside the configured areas: not reported
            answers(area="Work"),
        ], cfg)
        ids = lambda k: [x["id"] for x in out[k]]
        self.assertEqual(ids("missing_required"), ["1"])
        self.assertEqual(out["unlisted_labels"][0]["unlisted"], ["old-shopping"])
        self.assertEqual(len(out["unlisted_labels"]), 1)
        self.assertEqual(ids("vague_title"), ["2"])
        self.assertEqual(ids("project_label_review"), ["3"])
        self.assertEqual(ids("area_mismatch"), ["3"])

    def test_no_rules_no_rule_findings(self):
        cfg = config("[jev]\nenabled = true\n")
        tasks = [{"id": "1", "title": "t", "project": "P", "labels": ["anything"]}]
        out = jev_audit.audit(tasks, [{"vague": {"noul": 0.1}}], cfg)
        self.assertEqual(out["missing_required"], [])
        self.assertEqual(out["unlisted_labels"], [])
        self.assertNotIn("area", jev_audit.questions(tasks[0], cfg))

    def test_questions_only_for_project_labels_present(self):
        cfg = config()
        self.assertIn("plabel0", jev_audit.questions({"labels": ["project/community-site"]}, cfg))
        self.assertNotIn("plabel0", jev_audit.questions({"labels": ["kind/write"]}, cfg))


class Place(unittest.TestCase):
    def test_build_uses_config_and_skips_inbox(self):
        cfg = config()
        projects = [{"id": "i", "name": "Posteingang", "inbox": True}, {"id": "w", "name": "Work"},
                    {"id": "r", "name": "Operations", "parent": "Work", "description": "routine work"}]
        state, q, by_key, names = jev_place.build(
            {"title": "t", "parent_title": "p", "description": "secret", "projects": projects}, cfg)
        self.assertEqual(sorted(by_key), ["Work", "Work / Operations"])
        self.assertIn("job projects", q["project"]["criteria"]["Work / Operations"])
        self.assertEqual(sorted(q["act"]["criteria"]), ["kind/buy", "kind/write"])
        self.assertEqual(names, ["topic/food"])
        self.assertEqual(state["task"]["parent_task"], "p")
        self.assertNotIn("description", state["task"])     # send_descriptions defaults to false

    def test_build_without_labels_asks_only_for_project(self):
        cfg = config("[jev]\nenabled = true\nsend_descriptions = true\n")
        state, q, _, names = jev_place.build({"title": "t", "description": "d", "projects": [{"id": "a", "name": "A"}]}, cfg)
        self.assertEqual(list(q), ["project"])
        self.assertEqual(names, [])
        self.assertEqual(state["task"]["description"], "d")


class Find(unittest.TestCase):
    def test_rank_keeps_best_concept_above_threshold(self):
        tasks = [{"id": i, "title": i, "project": "P", "labels": []} for i in "abc"]
        noul = lambda *ps: {f"q{i}": {"noul": p} for i, p in enumerate(ps)}
        out = jev_find.rank(tasks, [noul(0.2, 0.9), noul(0.6, 0.64), noul(0.7, 0.1)], top=10)
        self.assertEqual([(h["id"], h["p"]) for h in out], [("a", 0.9), ("c", 0.7)])
        self.assertEqual(len(jev_find.rank(tasks, [noul(0.9)] * 3, top=2)), 2)

    def test_request_asks_one_question_per_concept(self):
        state, q = jev_find.request(["garden project", "bike repair"], {"title": "t", "project": "P", "labels": [],
                                                              "description": "d"}, with_description=False)
        self.assertEqual(sorted(q), ["q0", "q1"])
        self.assertNotIn("description", state["task"])


class Copies(unittest.TestCase):
    def test_every_skill_copy_matches_its_source(self):
        stale = [str(dst.relative_to(ROOT)) for src, dst in sync.targets()
                 if not dst.exists() or dst.read_bytes() != src.read_bytes()]
        self.assertEqual(stale, [], "run: python3 dev/sync.py")

    def test_eval_scenarios_are_self_contained(self):
        import json
        for f in SKILLS.glob("*/evals/scenarios.json"):
            skill = f.parents[1]
            for sc in json.loads(f.read_text(encoding="utf-8")):
                self.assertEqual(sc["skills"], [skill.name], f)
                for fixture in sc["files"]:
                    self.assertTrue((skill / fixture).exists(), (f, fixture))
        for cfg in SKILLS.glob("*/evals/fixtures/config.toml"):
            self.assertTrue(jevlib.acts(jevlib.load_config(cfg)), cfg)

    def test_scripts_write_no_bytecode_into_the_install(self):
        for script in SKILLS.glob("*/scripts/jev_*.py"):
            text = script.read_text(encoding="utf-8")
            self.assertLess(text.index("sys.dont_write_bytecode = True"), text.index("import jevlib"), script)

    def test_scripts_import_only_their_own_folder(self):
        for script in SKILLS.glob("*/scripts/*.py"):
            self.assertNotIn("sys.path", script.read_text(encoding="utf-8"), script)


if __name__ == "__main__":
    unittest.main()
