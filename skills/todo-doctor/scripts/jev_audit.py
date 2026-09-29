"""Audit active Todoist tasks against the user's configured label rules, with TypeSafe Jev for judgments.

Input:  `--todoist` fetches active non-Inbox tasks with TODOIST_API_TOKEN (env or ~/.config/todoist/.env);
        otherwise stdin {"tasks": [{"id", "title", "labels": [...], "project": "Parent / Name",
        "parent_title"?: "top > ... > parent", "has_children"?: bool}]}
        Tasks with subtasks only group them and are exempt from the required-label check.
stdout: {"checked": N, "missing_required": [...], "unlisted_labels": [...], "vague_title": [...],
         "project_label_review": [...], "area_mismatch": [...]}
Only task titles, parent titles and label names leave this machine, one request per task.
Exit 2 = a key is missing, 3 = Jev not enabled.
"""
import json, sys

sys.dont_write_bytecode = True  # no __pycache__: an untracked file blocks aem updates of this checkout
import jevlib  # noqa: E402

VAGUE_MIN = 0.7      # thresholds eyeballed on 39 tasks; retune if findings get noisy
MISMATCH_CONF = 0.8
KEYS = ("missing_required", "unlisted_labels", "vague_title", "project_label_review", "area_mismatch")


def project_labels(t, cfg):
    return [l for l in t["labels"] if l in cfg["projects"]]


def audit(tasks, answers, cfg):
    out = {k: [] for k in KEYS}
    pre, allowed = cfg["required_prefix"], jevlib.allowlist(cfg)
    for t, a in zip(tasks, answers):
        row = {"id": t["id"], "title": t["title"], "project": t["project"], "labels": t["labels"]}
        if pre and not t.get("has_children") and not any(l.startswith(pre) for l in t["labels"]):
            out["missing_required"].append(row)
        if allowed is not None and (unlisted := [l for l in t["labels"] if l.lower() not in allowed]):
            out["unlisted_labels"].append({**row, "unlisted": unlisted})
        if (v := a["vague"]["noul"]) >= VAGUE_MIN:
            out["vague_title"].append({**row, "p": round(v, 2)})
        for j, l in enumerate(project_labels(t, cfg)):
            if (p := a[f"plabel{j}"]["noul"]) < 0.5:
                out["project_label_review"].append({**row, "label": l, "p": round(p, 2)})
        area, actual = a.get("area"), t["project"].split(" / ")[0]
        if area and actual in cfg["areas"] and area["choice"] != actual and area["confidence"] >= MISMATCH_CONF:
            out["area_mismatch"].append({**row, "suggested_area": area["choice"],
                                         "confidence": round(area["confidence"], 2)})
    return out


def questions(t, cfg):
    q = {"vague": {"type": "noul", "instructions":
                   "Is the task title only a bare noun or topic, rather than a concrete action someone could start on?"}}
    if len(cfg["areas"]) > 1:
        q["area"] = {"type": "choice", "instructions": "Which area does this task belong to?", "criteria": cfg["areas"]}
    for j, l in enumerate(project_labels(t, cfg)):
        q[f"plabel{j}"] = {"type": "noul",
                           "instructions": f"Is this task (or its parent task) part of {cfg['projects'][l]}?"}
    return q


def main():
    cfg = jevlib.enabled_config()
    key = jevlib.api_key()
    if not key:
        print("no TYPESAFE_API_KEY (env or ~/.config/typesafe/.env)", file=sys.stderr)
        return jevlib.MISSING_KEY
    if "--todoist" in sys.argv:
        if not (token := jevlib.todoist_token()):
            print("no TODOIST_API_TOKEN (env or ~/.config/todoist/.env)", file=sys.stderr)
            return jevlib.MISSING_KEY
        tasks = jevlib.todoist_tasks(token)
    else:
        tasks = json.load(sys.stdin)["tasks"]
    answers = jevlib.ask_each(key, [({"task": {"title": t["title"],
                                               **({"parent_task": t["parent_title"]} if t.get("parent_title") else {})}},
                                      questions(t, cfg)) for t in tasks])
    json.dump({"checked": len(tasks), **audit(tasks, answers, cfg)}, sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
