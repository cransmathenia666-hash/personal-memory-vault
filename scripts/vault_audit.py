#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only audit of a Markdown knowledge vault. Writes nothing.

Reports: broken wikilinks, missing required frontmatter fields, duplicate
basenames, orphan formal pages, stale inbox items, updated-date distribution.

Usage:
    python vault_audit.py "/path/to/vault"
    python vault_audit.py <vault> --root-alias 个人信息库 --inbox-age 30
    python vault_audit.py <vault> --skip .obsidian,.trash,_recovery-evidence --json > audit.json

Conventions assumed (override with flags): top dirs starting 1/2/3 are formal
knowledge, top dirs starting 0 are inbox; pages carry YAML frontmatter.
"""
import argparse
import collections
import datetime
import io
import json
import os
import re
import sys

DEFAULT_REQ = ["title", "domain", "kind", "status", "confidence",
               "created", "updated", "source_refs", "tags"]
LINK = re.compile(r"\[\[([^\]]+)\]\]")
DATE = re.compile(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})")


def read(path):
    return io.open(path, encoding="utf-8", errors="replace").read()


def frontmatter(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    return text[3:end] if end > 0 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--skip", default=".obsidian,.trash,.git,.obsidian.bak")
    ap.add_argument("--formal-prefixes", default="1,2,3")
    ap.add_argument("--inbox-prefix", default="0")
    ap.add_argument("--inbox-age", type=int, default=30)
    ap.add_argument("--req", default=",".join(DEFAULT_REQ))
    ap.add_argument("--root-alias", default="",
                    help="leading segment links use for the vault itself, e.g. its folder name")
    args = ap.parse_args()

    vault = os.path.abspath(args.vault)
    skip = {s for s in args.skip.split(",") if s}
    req = [r for r in args.req.split(",") if r]
    prefixes = tuple(p for p in args.formal_prefixes.split(",") if p)
    alias = args.root_alias.strip("/")

    files = []
    for root, dirs, names in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in skip]
        files += [os.path.join(root, n) for n in names if n.lower().endswith(".md")]

    def rel(path):
        return os.path.relpath(path, vault).replace(os.sep, "/")

    by_rel = {rel(p): p for p in files}
    by_base = collections.defaultdict(list)
    for p in files:
        by_base[os.path.basename(p)[:-3]].append(rel(p))

    broken = collections.defaultdict(list)
    inbound = collections.Counter()
    links = 0
    for p in files:
        source = rel(p)
        for m in LINK.finditer(read(p)):
            target = m.group(1).split("|")[0].split("#")[0].strip()
            if not target:
                continue
            links += 1
            if target.lower().endswith(".md"):
                target = target[:-3]
            if alias and (target == alias or target.startswith(alias + "/")):
                target = target[len(alias) + 1:]
            base = target.split("/")[-1]
            if target in by_rel:
                if target != source:
                    inbound[target] += 1
            elif base in by_base:
                for cand in by_base[base]:
                    if cand != source:
                        inbound[cand] += 1
            else:
                broken[target].append(source)

    missing_fields = {}
    no_fm = []
    for p in files:
        r = rel(p)
        fm = frontmatter(read(p))
        if fm is None:
            no_fm.append(r)
            continue
        keys = set(re.findall(r"^([A-Za-z_]+):", fm, re.M))
        miss = [k for k in req if k not in keys]
        if miss:
            missing_fields[r] = miss

    dup = {b: rs for b, rs in by_base.items() if len(rs) > 1}
    formal = [r for r in by_rel if r.split("/")[0].startswith(prefixes)]
    orphans = sorted(r for r in formal if inbound[r] == 0)

    today = datetime.date.today()
    inbox, stale = [], []
    for r in by_rel:
        if not r.split("/")[0].startswith(args.inbox_prefix):
            continue
        age = None
        m = DATE.search(os.path.basename(r))
        if m:
            try:
                age = (today - datetime.date(int(m.group(1)), int(m.group(2)),
                                             int(m.group(3)))).days
            except ValueError:
                age = None
        inbox.append({"page": r, "age_days": age})
        if age is not None and age > args.inbox_age:
            stale.append({"page": r, "age_days": age})

    updated = {}
    for p in files:
        fm = frontmatter(read(p)) or ""
        m = re.search(r"^updated:\s*(\S+)", fm, re.M)
        updated[rel(p)] = m.group(1) if m else None

    print(json.dumps({
        "vault": vault,
        "markdown_pages": len(files),
        "wikilinks": links,
        "broken_links_unique": len(broken),
        "broken_link_occurrences": sum(len(v) for v in broken.values()),
        "broken_by_target": {k: {"count": len(v), "sources": v[:6]}
                             for k, v in sorted(broken.items(), key=lambda kv: -len(kv[1]))},
        "pages_without_frontmatter": no_fm,
        "pages_missing_fields": missing_fields,
        "duplicate_basenames": dup,
        "orphan_formal_pages": orphans,
        "inbox": inbox,
        "stale_inbox": stale,
        "updated_distribution": {str(k): v for k, v in sorted(
            collections.Counter(updated.values()).items(),
            key=lambda kv: (kv[0] is None, str(kv[0])))},
        "oldest_updated": [{"page": k, "updated": v} for k, v in
                           sorted(updated.items(), key=lambda kv: str(kv[1]))[:15]],
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
