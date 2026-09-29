"""Suggest a Todoist project and labels for one task with TypeSafe Jev (optional; see the skill's Jev section).

stdin:  {"title": str, "description"?: str, "parent_title"?: str,
         "projects": [{"id", "name", "parent"?, "description"?, "inbox"?: bool}]}
stdout: {"project": {...}, "act"?: {...}, "project_label"?: {...}, "extra_labels": [...]}
Labels and areas come from the user's config. Sends the task title, parent task title, project names
and descriptions, and label meanings; the first 1500 characters of the description only when
[jev] send_descriptions = true. Exit 2 = no TYPESAFE_API_KEY, 3 = Jev not enabled.
"""
import json, sys

sys.dont_write_bytecode = True  # no __pycache__: an untracked file blocks aem updates of this checkout
import jevlib  # noqa: E402

NONE = "none"


def build(task, cfg):
    projects = [p for p in task["projects"] if not p.get("inbox") and p.get("name") != "Inbox"]
    by_key = {(f"{p['parent']} / " if p.get("parent") else "") + p["name"]: p for p in projects}
    areas = cfg["areas"]

    def meaning(p):
        area = areas.get(p.get("parent") or p["name"], "")
        return f"{area} — {p.get('description') or p['name']}" if area else (p.get("description") or p["name"])

    q = {"project": {"type": "choice", "instructions": "Which Todoist project should this task be filed in?",
                     "criteria": {k: meaning(p) for k, p in by_key.items()}}}
    if acts := jevlib.acts(cfg):
        q["act"] = {"type": "choice", "instructions": "Which verb best describes the main action this task asks for?",
                    "criteria": acts}
    if cfg["projects"]:
        q["project_label"] = {"type": "choice",
                              "instructions": "Does the task explicitly belong to one of these named projects?",
                              "criteria": {**cfg["projects"], NONE: "no named project applies"}}
    extras = jevlib.extras(cfg)
    names = list(extras)
    for i, l in enumerate(names):
        q[f"x{i}"] = {"type": "noul", "instructions": f"Is this task specifically about {extras[l]}?"}
    state = {"task": {"title": task["title"]}}
    if cfg["jev"]["send_descriptions"] and task.get("description"):
        state["task"]["description"] = task["description"][:1500]
    if task.get("parent_title"):
        state["task"]["parent_task"] = task["parent_title"]
    return state, q, by_key, names


def main():
    cfg = jevlib.enabled_config()
    key = jevlib.api_key()
    if not key:
        print("no TYPESAFE_API_KEY (env or ~/.config/typesafe/.env)", file=sys.stderr)
        return jevlib.MISSING_KEY
    task = json.load(sys.stdin)
    state, q, by_key, names = build(task, cfg)
    a = jevlib.ask(key, state, q)
    pick = lambda ans: {"value": ans["choice"], "p": round(ans["probabilities"][ans["choice"]], 3),
                        "confidence": round(ans["confidence"], 3)}
    proj = pick(a["project"])
    out = {"project": {**proj, "id": by_key[proj["value"]]["id"]}}
    for k in ("act", "project_label"):
        if k in a:
            out[k] = pick(a[k])
    out["extra_labels"] = sorted(({"label": l, "p": round(a[f"x{i}"]["noul"], 3)} for i, l in enumerate(names)),
                                 key=lambda x: -x["p"])
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
