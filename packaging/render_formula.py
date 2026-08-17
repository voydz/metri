#!/usr/bin/env python3
"""Render the Homebrew formula for a release from packaging/metri.rb.tmpl.

`brew bump-formula-pr` only understands a formula with a single url/sha256 pair,
so multi-platform binary releases are rendered here and committed to the tap
directly.

Usage:
    render_formula.py --version 0.1.0 --repo voydz/metri \
        --sha256 darwin-arm64=abc... \
        --sha256 linux-x86_64=def... \
        --sha256 linux-arm64=ghi... \
        --output metri.rb
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TEMPLATE = Path(__file__).with_name("metri.rb.tmpl")
PLATFORMS = ("darwin-arm64", "linux-x86_64", "linux-arm64")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="release version, without a 'v' prefix")
    parser.add_argument("--repo", required=True, help="owner/name of the source repository")
    parser.add_argument(
        "--sha256",
        action="append",
        default=[],
        metavar="PLATFORM=SHA256",
        help=f"one per platform, of {', '.join(PLATFORMS)}",
    )
    parser.add_argument("--output", type=Path, help="write here instead of stdout")
    return parser.parse_args(argv)


def collect_shas(pairs: list[str]) -> dict[str, str]:
    shas: dict[str, str] = {}
    for pair in pairs:
        platform, _, sha = pair.partition("=")
        if platform not in PLATFORMS:
            raise SystemExit(f"unknown platform {platform!r}, expected one of {PLATFORMS}")
        if len(sha) != 64 or not all(c in "0123456789abcdef" for c in sha):
            raise SystemExit(f"{platform}: {sha!r} is not a sha256 digest")
        shas[platform] = sha

    missing = [platform for platform in PLATFORMS if platform not in shas]
    if missing:
        raise SystemExit(f"missing --sha256 for: {', '.join(missing)}")
    return shas


def render(version: str, repo: str, shas: dict[str, str]) -> str:
    formula = TEMPLATE.read_text()
    formula = formula.replace("@@VERSION@@", version).replace("@@REPO@@", repo)

    for platform, sha in shas.items():
        asset = f"metri-{version}-{platform}.tar.gz"
        url = f"https://github.com/{repo}/releases/download/v{version}/{asset}"
        key = platform.upper().replace("-", "_")
        formula = formula.replace(f"@@URL_{key}@@", url)
        formula = formula.replace(f"@@SHA256_{key}@@", sha)

    if "@@" in formula:
        leftover = [line.strip() for line in formula.splitlines() if "@@" in line]
        raise SystemExit("unsubstituted placeholders:\n  " + "\n  ".join(leftover))
    return formula


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    formula = render(args.version.lstrip("v"), args.repo, collect_shas(args.sha256))

    if args.output:
        args.output.write_text(formula)
    else:
        sys.stdout.write(formula)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
