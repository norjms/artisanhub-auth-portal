#!/usr/bin/env python3
"""What may be in this repository, and how its commits are made.

    python3 tests/check_tree.py [<first commit to check>..HEAD]

Every tracked file must be on the list below; anything else (an editor's or an assistant's settings, a stray
note) fails. Every commit in the range must be authored and committed by the maintainer's public address and
carry no trailer lines. No file may contain an em dash.
"""

from __future__ import annotations

import fnmatch
import subprocess
import sys

ALLOWED = (
    ".dockerignore", ".gitignore", "Dockerfile", "LICENSE", "NOTICE", "README.md", "upstream.env",
    "convert/convert.py", "convert/files/web/src/*", "convert/files/web/src/*/*", "convert/files/web/src/*/*/*",
    "tests/*.py", "tests/*.sh", "tests/*.mjs", "tests/stack/*", ".github/workflows/*.yml",
)
IDENTITY = "James Norman <3048818+norjms@users.noreply.github.com>"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def main(argv: list[str]) -> int:
    problems = []
    for path in git("ls-files").splitlines():
        if not any(fnmatch.fnmatchcase(path, pattern) for pattern in ALLOWED):
            problems.append(f"{path}: not a file this repository holds")
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        if "\u2014" in text:
            problems.append(f"{path}: an em dash")
    span = argv[1] if len(argv) > 1 else "HEAD"
    for line in git("log", "--format=%H%x09%an <%ae>%x09%cn <%ce>", span).splitlines():
        sha, author, committer = line.split("\t")
        if author != IDENTITY or committer != IDENTITY:
            problems.append(f"{sha[:7]}: authored or committed as {author} / {committer}")
        message = git("log", "-1", "--format=%B", sha)
        trailers = subprocess.run(["git", "interpret-trailers", "--parse"], input=message, capture_output=True,
                                  text=True, check=True).stdout
        if trailers.strip():
            problems.append(f"{sha[:7]}: trailer lines in the message")
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
