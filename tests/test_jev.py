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



MULTIPLE_CONFIG = """
[labels]
selection = "multiple"
required_prefix = "kind/"  # explicit multiple mode overrides a legacy requirement
ignore = ["imported"]
[labels.allowed]
agent = "agent environment"
pkm = "knowledge management"
design = "design structure or workflows"
write = "write documents"
waiting = "confirmed outstanding dependency"
[labels.projects]
community = "community site"
[labels.roles]
agent = "topic"
pkm = "topic"
design = "action"
write = "action"
waiting = "state"
community = "project"
[jev]
enabled = true
"""

class MultipleLabels(unittest.TestCase):
    def test_explicit_roles_do_not_require_name_prefixes(self):
        cfg = config(MULTIPLE_CONFIG)
        self.assertEqual(set(jevlib.acts(cfg)), {"design", "write"})
        self.assertEqual(set(jevlib.goal_labels(cfg)), {"community"})
        self.assertEqual(jevlib.required_prefix(cfg), "")

    def test_all_labels_get_independent_placement_questions(self):
        cfg = config(MULTIPLE_CONFIG)
        _, q, _, names = jev_place.build({"title": "Design and document an agent wiki", "projects": [{"id": "p", "name": "Work"}]}, cfg)
        self.assertNotIn("act", q)
        self.assertNotIn("project_label", q)
        self.assertEqual(set(names), {"agent", "pkm", "design", "write", "waiting", "community"})
        self.assertTrue(all(q[f"x{i}"]["type"] == "noul" for i in range(len(names))))
        self.assertIn("current condition confirmed", q[f"x{names.index('waiting')}"]["instructions"])
        self.assertNotIn("current condition confirmed", q[f"x{names.index('design')}"]["instructions"])

    def test_multiple_placement_result_preserves_zero_or_many_labels(self):
        cfg = config(MULTIPLE_CONFIG)
        names = ["agent", "pkm", "design", "write"]
        a = {"project": {"choice": "Work", "probabilities": {"Work": 1.0}, "confidence": 1.0},
             **{f"x{i}": {"noul": p} for i, p in enumerate([0.9, 0.8, 0.95, 0.75])}}
        result = jev_place.placement(a, {"Work": {"id": "p"}}, names, cfg)
        self.assertEqual({l["label"] for l in result["labels"]}, set(names))
        self.assertEqual({l["role"] for l in result["labels"]}, {"topic", "action"})
        self.assertNotIn("act", result)
        self.assertEqual(jev_place.placement({"project": a["project"]}, {"Work": {"id": "p"}}, [], cfg)["labels"], [])

    def test_audit_accepts_unlabelled_and_multiple_action_tasks(self):
        cfg = config(MULTIPLE_CONFIG)
        tasks = [{"id": "0", "title": "Renew passport", "project": "Personal", "labels": []},
                 {"id": "1", "title": "Design and document workflow", "project": "Work", "labels": ["agent", "pkm", "design", "write"]}]
        out = jev_audit.audit(tasks, [{"vague": {"noul": 0.1}}] * 2, cfg)
        self.assertEqual(out["missing_required"], [])
        self.assertEqual(out["unlisted_labels"], [])

    def test_project_roles_in_allowed_are_checked_independently(self):
        cfg = config(MULTIPLE_CONFIG.replace('[labels.projects]\ncommunity = "community site"', 'community = "community site"'))
        qs = jev_audit.questions({"labels": ["community", "agent"]}, cfg)
        self.assertIn("community site", qs["plabel0"]["instructions"])

    def test_legacy_placement_output_is_unchanged(self):
        cfg = config()
        a = {"project": {"choice": "Work", "probabilities": {"Work": 1.0}, "confidence": 1.0},
             "act": {"choice": "kind/write", "probabilities": {"kind/write": 0.9}, "confidence": 0.9},
             "project_label": {"choice": "none", "probabilities": {"none": 0.8}, "confidence": 0.8},
             "x0": {"noul": 0.2}}
        result = jev_place.placement(a, {"Work": {"id": "p"}}, ["topic/food"], cfg)
        self.assertEqual(set(result), {"project", "act", "project_label", "extra_labels"})
        self.assertEqual(result["act"]["value"], "kind/write")
        self.assertEqual(result["project_label"]["value"], "none")
        self.assertEqual(result["extra_labels"], [{"label": "topic/food", "p": 0.2}])

    def test_relative_guide_and_invalid_settings_fail_before_model_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "config.toml"
            p.write_text('guide = "guide.md"\n' + MULTIPLE_CONFIG, encoding="utf-8")
            self.assertEqual(jevlib.load_config(p)["guide"], str(Path(tmp) / "guide.md"))
            p.write_text(MULTIPLE_CONFIG.replace('selection = "multiple"', 'selection = "invalid"'), encoding="utf-8")
            env = {**os.environ, "TODOIST_SKILLS_CONFIG": str(p)}
            for skill, script in [("todo-add", "jev_place"), ("todo-doctor", "jev_audit"), ("todo-find", "jev_find")]:
                result = subprocess.run([sys.executable, str(SKILLS / skill / "scripts" / f"{script}.py"),
                                         *(["example"] if script == "jev_find" else [])],
                                        input="{}", capture_output=True, text=True, env=env)
                self.assertEqual(result.returncode, 4)
                self.assertIn("Invalid Todoist settings", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_invalid_selection_roles_and_missing_definitions_rejected(self):
        for bad in [MULTIPLE_CONFIG.replace('selection = "multiple"', 'selection = "random"'),
                    MULTIPLE_CONFIG.replace('design = "action"', 'design = "invalid"'),
                    MULTIPLE_CONFIG.replace('design = "design structure or workflows"', ''),
                    MULTIPLE_CONFIG.replace('design = "action"', 'design = 7'),
                    MULTIPLE_CONFIG.replace('ignore = ["imported"]', 'ignore = "imported"'),
                    MULTIPLE_CONFIG.replace('community = "project"', 'community = "action"')]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    config(bad)


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
        self.assertEqual(cfg["selection"], "multiple")
        self.assertIn("write", jevlib.acts(cfg))

    def test_scripts_exit_3_when_jev_not_enabled(self):
        env = {**os.environ, "TODOIST_SKILLS_CONFIG": str(ROOT / "no-such-config.toml")}
        for skill, script in (("todo-add", "jev_place"), ("todo-find", "jev_find"), ("todo-doctor", "jev_audit")):
            r = subprocess.run([sys.executable, str(SKILLS / skill / "scripts" / f"{script}.py"), "x"],
                               input="{}", capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 3, (script, r.stderr))


class Audit(unittest.TestCase):
    def test_group_headers_are_not_vague_but_keep_other_findings(self):
        cfg = config(CONFIG + '\n[grouping]\nheader_prefix = "* "\n')
        tasks = [
            {"id": "h", "title": "* hermes-agent-playbook", "project": "Personal", "labels": ["unknown"]},
            {"id": "p", "title": "Research", "project": "Personal", "labels": [], "has_children": True},
            {"id": "t", "title": "Stuff", "project": "Personal", "labels": ["kind/write"]},
        ]
        out = jev_audit.audit(tasks, [answers(vague=0.9)] * 3, cfg)
        self.assertEqual([r["id"] for r in out["vague_title"]], ["t"])
        self.assertEqual(out["missing_required"], [])
        self.assertEqual([r["id"] for r in out["unlisted_labels"]], ["h"])

    def test_invalid_grouping_is_rejected(self):
        for text in ('grouping = "bad"\n', '[grouping]\nheader_prefix = 3\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                config(text)

    def test_unconfigured_prefix_does_not_exempt_ordinary_task(self):
        task = {"id": "t", "title": "* Stuff", "project": "Personal", "labels": ["kind/write"]}
        out = jev_audit.audit([task], [answers(vague=0.9)], config())
        self.assertEqual([r["id"] for r in out["vague_title"]], ["t"])

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


class Routes(unittest.TestCase):
    def test_no_todoist_route_is_preferred(self):
        # Neither MCP nor td may be the default: the user names one, or settings do, or the skill asks.
        for skill_md in SKILLS.glob("*/SKILL.md"):
            text = skill_md.read_text(encoding="utf-8")
            self.assertNotIn("if available", text, skill_md)
            self.assertNotIn("then the authenticated", text, skill_md)


if __name__ == "__main__":
    unittest.main()
