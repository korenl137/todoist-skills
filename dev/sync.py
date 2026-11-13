"""Copy shared files into every skill that uses them, so each skill folder stands alone.

Run after editing a source below; tests/test_repo.py fails until the copies match.
"""
import pathlib, shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
# source file -> (path inside each skill, skills that get a copy)
COPIES = {
    SKILLS / "todo-doctor/evals/fixtures/config.toml": ("evals/fixtures/config.toml",
                                                       ["todo-add", "todo-update", "todo-find"]),
}


def targets():
    for src, (rel, skills) in COPIES.items():
        for s in skills:
            yield src, SKILLS / s / rel


if __name__ == "__main__":
    for src, dst in targets():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        print(f"{src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
