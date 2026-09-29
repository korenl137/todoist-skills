#!/usr/bin/env python3
"""Check the td command examples in skill tables; optionally exercise Todoist."""

import argparse
from datetime import date, timedelta
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
GROUPS = {"task", "project", "section", "label", "completed", "comment", "auth"}


def td_command():
    node = shutil.which("node")
    if shutil.which("td") and node:
        version = subprocess.check_output([node, "--version"], text=True).strip()
        if int(version.removeprefix("v").split(".")[0]) >= 24:
            return ["td"]
    return ["npx", "-y", "@doist/todoist-cli"]


def run(base, args, *, token=None, input_text=None):
    env = os.environ.copy()
    if token:
        env["TODOIST_API_TOKEN"] = token
    result = subprocess.run(base + args, input=input_text, text=True,
                            capture_output=True, env=env, check=False)
    if result.returncode:
        raise RuntimeError(f"td {' '.join(args)} failed ({result.returncode}): "
                           f"{result.stderr.strip() or result.stdout.strip()}")
    return result.stdout


def examples():
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|") or "`td " not in line:
                continue
            for match in re.finditer(r"`(td [^`]+)`", line):
                yield path, match.group(1)


def static_check(base):
    found = list(examples())
    if not found:
        raise RuntimeError("no td commands found in SKILL.md tables")
    help_cache = {}
    for path, example in found:
        words = shlex.split(example)
        name = words[1:3] if len(words) > 2 and words[1] in GROUPS else words[1:2]
        key = tuple(name)
        if key not in help_cache:
            help_cache[key] = run(base, list(key) + ["--help"])
        help_text = help_cache[key]
        for flag in (word for word in words if word.startswith("--")):
            if flag not in help_text:
                raise RuntimeError(f"{path}: {example}: {flag} absent from td {' '.join(key)} --help")
    print(f"static OK: {len(found)} examples, {len(help_cache)} commands")


def api_token():
    if os.environ.get("TODOIST_API_TOKEN"):
        return os.environ["TODOIST_API_TOKEN"]
    path = Path.home() / ".config/todoist/.env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("TODOIST_API_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"\'')
    raise RuntimeError("--live needs TODOIST_API_TOKEN or ~/.config/todoist/.env")


def as_json(base, args, token):
    return json.loads(run(base, args + ["--json"], token=token))


def live_check(base, token):
    # Read-only commands stay separate from the default static check.
    for args in (["today"], ["upcoming", "7"], ["task", "list", "--all"],
                 ["project", "list"], ["section", "list", "Inbox"],
                 ["label", "list"], ["completed", "list", "--search", "td-test"],
                 ["activity", "--type", "task", "--event", "completed"]):
        run(base, args + ["--json"], token=token)
    print("live reads OK")

    task_id = None
    try:
        created = as_json(base, ["task", "add", "[td-test] CLI skill check",
                                 "--project", "Inbox", "--due", "every day"], token)
        task_id = str(created["id"])
        ref = f"id:{task_id}"
        as_json(base, ["task", "view", ref], token)
        labels = as_json(base, ["label", "list"], token)
        if isinstance(labels, dict):
            labels = labels.get("results", labels.get("labels", []))
        if labels:
            name = labels[0]["name"]
            updated = as_json(base, ["task", "update", ref, "--labels", name], token)
            if name not in updated.get("labels", []):
                raise RuntimeError("td task update did not retain the test label")
        next_date = (date.today() + timedelta(days=1)).isoformat()
        rescheduled = as_json(base, ["task", "reschedule", ref, next_date], token)
        due = rescheduled.get("due") or {}
        if not due.get("is_recurring", due.get("isRecurring", False)):
            raise RuntimeError("td task reschedule lost recurrence")
        projects = as_json(base, ["project", "list", "--full"], token)["results"]
        other = next((item for item in projects if not item.get("inboxProject")
                      and not item.get("isShared") and not item.get("isArchived")), None)
        if not other:
            raise RuntimeError("no personal non-Inbox project available to test task move")
        try:
            run(base, ["task", "move", ref, "--project", f"id:{other['id']}"], token=token)
        finally:
            run(base, ["task", "move", ref, "--project", "Inbox"], token=token)
        print("live writes OK: add, view, label update, recurrence, move")
    finally:
        if task_id:
            run(base, ["task", "delete", f"id:{task_id}", "--yes"], token=token)
            print("temporary Inbox task deleted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="also use a Todoist account and a temporary Inbox task")
    args = parser.parse_args()
    base = td_command()
    static_check(base)
    if args.live:
        live_check(base, api_token())


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print(f"check_td_commands: {exc}", file=sys.stderr)
        sys.exit(1)
