"""Optional Jev support for a todo-* skill: user config, keys, the TypeSafe call, and Todoist task fetching.

Each skill that uses Jev ships its own identical copy of this file (tests/test_copies.py checks that),
so every skill folder works on its own. Edit dev/jevlib.py and run `python3 dev/sync.py`.

Config: $TODOIST_SKILLS_CONFIG or ~/.config/todoist-skills/config.toml (see config.example.toml).
Keys: the environment, or ~/.config/typesafe/.env and ~/.config/todoist/.env; none live in the repo.
Exit codes: 2 = a key is missing, 3 = Jev is not enabled, 4 = invalid settings.
"""
import json, os, pathlib, sys, tomllib, urllib.request
from concurrent.futures import ThreadPoolExecutor

MISSING_KEY, DISABLED, INVALID_CONFIG = 2, 3, 4


def config_path():
    default = pathlib.Path.home() / ".config/todoist-skills/config.toml"
    return pathlib.Path(os.environ.get("TODOIST_SKILLS_CONFIG") or default).expanduser()


def load_config(p=None):
    p = pathlib.Path(p) if p else config_path()
    raw = tomllib.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    labels, jev, grouping = raw.get("labels", {}), raw.get("jev", {}), raw.get("grouping", {})
    if not all(isinstance(value, dict) for value in (labels, jev, grouping)):
        raise ValueError("labels, jev and grouping must be tables")
    guide = raw.get("guide", "")
    if not isinstance(guide, str):
        raise ValueError("guide must be a path string")
    guide_path = pathlib.Path(guide).expanduser() if guide else None
    cfg = {
        "guide": str((guide_path if guide_path.is_absolute() else p.parent / guide_path).resolve()) if guide_path else "",
        "selection": labels.get("selection", "legacy"),
        "roles": labels.get("roles", {}),
        "required_prefix": labels.get("required_prefix", ""),
        "allowed": labels.get("allowed", {}),
        "projects": labels.get("projects", {}),
        "ignore": labels.get("ignore", []),
        "areas": dict(raw.get("areas", {})),
        "header_prefix": grouping.get("header_prefix", ""),
        "jev": {"enabled": bool(jev.get("enabled", False)),
                "send_descriptions": bool(jev.get("send_descriptions", False))},
    }

    if not isinstance(cfg["header_prefix"], str):
        raise ValueError("grouping.header_prefix must be a string")
    if cfg["selection"] not in ("legacy", "multiple"):
        raise ValueError("labels.selection must be legacy or multiple")
    for group in ("allowed", "projects", "roles"):
        value = cfg[group]
        if not isinstance(value, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
            raise ValueError(f"labels.{group} must map label names to strings")
    if not isinstance(labels.get("ignore", []), list) or not all(isinstance(v, str) for v in cfg["ignore"]):
        raise ValueError("labels.ignore must be a list of strings")
    if not isinstance(cfg["required_prefix"], str):
        raise ValueError("labels.required_prefix must be a string")
    definitions = {**cfg["allowed"], **cfg["projects"]}
    for name, role in cfg["roles"].items():
        if name not in definitions or role not in ("action", "project", "topic", "state"):
            raise ValueError(f"labels.roles.{name} needs a definition and action/project/topic/state role")
        if name in cfg["projects"] and role != "project":
            raise ValueError(f"labels.projects.{name} must use the project role")
    for name in cfg["allowed"].keys() & cfg["projects"].keys():
        if cfg["allowed"][name] != cfg["projects"][name]:
            raise ValueError(f"conflicting label meanings: {name}")
    return cfg


def required_prefix(cfg):
    """Multiple selection is optional even if an old prefix is still present."""
    return cfg["required_prefix"] if cfg["selection"] == "legacy" else ""


def acts(cfg):
    """Explicit optional actions in multiple mode, or the legacy prefix group."""
    if cfg["selection"] == "multiple":
        return {k: v for k, v in {**cfg["allowed"], **cfg["projects"]}.items() if cfg["roles"].get(k) == "action"}
    pre = required_prefix(cfg)
    return {k: v for k, v in cfg["allowed"].items() if pre and k.startswith(pre)}


def goal_labels(cfg):
    """Named goals, including explicitly typed flat labels."""
    result = dict(cfg["projects"])
    if cfg["selection"] == "multiple":
        result.update({k: v for k, v in cfg["allowed"].items() if cfg["roles"].get(k) == "project"})
    return result


def extras(cfg):
    """Legacy labels outside the action/goal groups; all labels in multiple mode."""
    if cfg["selection"] == "multiple":
        return {**cfg["allowed"], **cfg["projects"]}
    a = acts(cfg)
    return {k: v for k, v in cfg["allowed"].items() if k not in a and k not in cfg["projects"]}


def allowlist(cfg):
    """Every label a task may carry (lowercase), or None when the config sets no allowlist."""
    if not (cfg["allowed"] or cfg["projects"]):
        return None
    return {l.lower() for l in (*cfg["allowed"], *cfg["projects"], *cfg["ignore"])}


def enabled_config():
    """Return the config, or exit 3 unless [jev] enabled = true."""
    try:
        cfg = load_config()
    except (ValueError, TypeError) as error:
        print(f"Invalid Todoist settings: {error}", file=sys.stderr)
        sys.exit(INVALID_CONFIG)
    if not cfg["jev"]["enabled"]:
        print(f"Jev is not enabled: set [jev] enabled = true in {config_path()}", file=sys.stderr)
        sys.exit(DISABLED)
    return cfg


def _key(var, env_file):
    if value := os.environ.get(var):
        return value
    env = pathlib.Path.home() / env_file
    for line in env.read_text(encoding="utf-8").splitlines() if env.exists() else []:
        if line.startswith(f"{var}="):
            return line.split("=", 1)[1].strip()
    return None


def api_key():
    return _key("TYPESAFE_API_KEY", ".config/typesafe/.env")


def todoist_token():
    return _key("TODOIST_API_TOKEN", ".config/todoist/.env")


def ask(key, state, questions):
    req = urllib.request.Request(
        "https://api.typesafe.ai/v1/systemone",
        data=json.dumps({"state": state, "model": "jev-latest", "questions": questions}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["answers"]


def ask_each(key, requests):
    """Run [(state, questions), ...] as separate parallel requests. One request per item: a single
    request over a whole task list drifted by list position when tried."""
    with ThreadPoolExecutor(8) as pool:
        return list(pool.map(lambda r: ask(key, *r), requests))


def fetch_all(token, kind):
    items, cursor = [], None
    while True:
        url = f"https://api.todoist.com/api/v1/{kind}?limit=200" + (f"&cursor={cursor}" if cursor else "")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            page = json.load(r)
        items += page["results"]
        if not (cursor := page.get("next_cursor")):
            return items


def todoist_tasks(token, include_inbox=False):
    projects = {p["id"]: p for p in fetch_all(token, "projects")}
    raw = fetch_all(token, "tasks")
    by_id = {t["id"]: t for t in raw}
    parents = {t["parent_id"] for t in raw if t.get("parent_id")}
    full = lambda p: (projects[p["parent_id"]]["name"] + " / " if p.get("parent_id") in projects else "") + p["name"]

    def ancestors(t):  # "top > ... > direct parent": the project context often sits only on the top task
        chain = []
        while (t := by_id.get(t.get("parent_id"))):
            chain.insert(0, t["content"])
        return " > ".join(chain)

    return [{"id": t["id"], "title": t["content"], "labels": t["labels"], "project": full(projects[t["project_id"]]),
             "description": t["description"],
             "has_children": t["id"] in parents, **({"parent_title": a} if (a := ancestors(t)) else {})}
            for t in raw if not t["checked"] and (include_inbox or not projects[t["project_id"]].get("inbox_project"))]
