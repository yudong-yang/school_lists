from __future__ import annotations

import argparse
from pathlib import Path

from .models import University
from .repository import UniversityRepository


DEFAULT_DB_PATH = Path("data/schools.db")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="school-list",
        description="Query and manage Gaokao university information.",
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize the local database.")

    add_parser = subparsers.add_parser("add", help="Add a university.")
    add_parser.add_argument("name")
    add_parser.add_argument("--province", required=True)
    add_parser.add_argument("--city", default="")
    add_parser.add_argument("--level", default="")
    add_parser.add_argument("--type", dest="school_type", default="")
    add_parser.add_argument("--ownership", default="")
    add_parser.add_argument("--address", default="")
    add_parser.add_argument("--website", default="")
    add_parser.add_argument("--notes", default="")

    list_parser = subparsers.add_parser("list", help="List universities.")
    list_parser.add_argument("--keyword", default="")
    list_parser.add_argument("--province", default="")
    list_parser.add_argument("--level", default="")
    list_parser.add_argument("--type", dest="school_type", default="")

    detail_parser = subparsers.add_parser("show", help="Show one university.")
    detail_parser.add_argument("id", type=int)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo = UniversityRepository(args.db)

    if args.command == "init":
        repo.initialize()
        print(f"Database initialized: {args.db}")
        return 0

    if args.command == "add":
        university = University(
            name=args.name,
            province=args.province,
            city=args.city,
            level=args.level,
            school_type=args.school_type,
            ownership=args.ownership,
            address=args.address,
            website=args.website,
            notes=args.notes,
        )
        university_id = repo.add(university)
        print(f"Added university #{university_id}: {args.name}")
        return 0

    if args.command == "list":
        universities = repo.search(
            keyword=args.keyword,
            province=args.province,
            level=args.level,
            school_type=args.school_type,
        )
        if not universities:
            print("No universities found.")
            return 0
        for university in universities:
            print(_format_row(university))
        return 0

    if args.command == "show":
        university = repo.get(args.id)
        if university is None:
            print(f"University not found: {args.id}")
            return 1
        print(_format_detail(university))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def _format_row(university: University) -> str:
    parts = [
        f"#{university.id}",
        university.name,
        university.province,
        university.city,
        university.level,
        university.school_type,
    ]
    return " | ".join(part for part in parts if part)


def _format_detail(university: University) -> str:
    fields = [
        ("ID", university.id),
        ("名称", university.name),
        ("省份", university.province),
        ("城市", university.city),
        ("层次", university.level),
        ("类型", university.school_type),
        ("办学性质", university.ownership),
        ("地址", university.address),
        ("官网", university.website),
        ("备注", university.notes),
    ]
    return "\n".join(f"{label}: {value}" for label, value in fields if value)


if __name__ == "__main__":
    raise SystemExit(main())
