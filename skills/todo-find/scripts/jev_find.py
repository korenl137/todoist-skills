"""Find active Todoist tasks related to a free-text query with TypeSafe Jev (optional; one Noul per task).

Usage:  jev_find.py "<concept>" ["<concept>" ...] [--with-description] [--top N]
        Pass each concept separately: a task matches if any concept matches (one combined query
        for two unrelated things tended to find neither).
stdout: {"checked": N, "matches": [{"id", "title", "project", "labels", "p"}]}, best first.
Sends task titles, parent-task chains, project and label names, and the query; task descriptions
only with --with-description and [jev] send_descriptions = true.
Exit 2 = TYPESAFE_API_KEY or TODOIST_API_TOKEN missing, 3 = Jev not enabled.
"""
import argparse, json, sys

sys.dont_write_bytecode = True  # no __pycache__: an untracked file blocks aem updates of this checkout
import jevlib  # noqa: E402

MIN_P = 0.65  # from 6 test queries, false hits sat at 0.50-0.60; retune on more queries


def request(queries, t, with_description):
    task = {"title": t["title"], "project": t["project"], "labels": t["labels"]}
    if t.get("parent_title"):
        task["parent_task"] = t["parent_title"]
    if with_description and t.get("description"):
        task["description"] = t["description"][:1500]
    q = {f"q{i}": {"type": "noul", "instructions":
                   f"Would someone searching their to-do list for \"{query}\" want to see this task "
                   "(counting what its parent task is about)?"} for i, query in enumerate(queries)}
    return {"task": task}, q


def rank(tasks, answers, top):
    hits = [{"id": t["id"], "title": t["title"], "project": t["project"], "labels": t["labels"],
             "p": round(max(x["noul"] for x in a.values()), 2)} for t, a in zip(tasks, answers)]
    return sorted((h for h in hits if h["p"] >= MIN_P), key=lambda h: -h["p"])[:top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--with-description", action="store_true")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()
    cfg = jevlib.enabled_config()
    key, token = jevlib.api_key(), jevlib.todoist_token()
    if not (key and token):
        print("missing TYPESAFE_API_KEY or TODOIST_API_TOKEN (env or ~/.config/{typesafe,todoist}/.env)",
              file=sys.stderr)
        return jevlib.MISSING_KEY
    with_description = args.with_description and cfg["jev"]["send_descriptions"]
    tasks = jevlib.todoist_tasks(token, include_inbox=True)
    answers = jevlib.ask_each(key, [request(args.queries, t, with_description) for t in tasks])
    json.dump({"checked": len(tasks), "matches": rank(tasks, answers, args.top)}, sys.stdout,
              ensure_ascii=False, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
