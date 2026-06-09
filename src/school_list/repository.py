from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .models import University


class UniversityRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS universities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    province TEXT NOT NULL,
                    city TEXT NOT NULL DEFAULT '',
                    level TEXT NOT NULL DEFAULT '',
                    school_type TEXT NOT NULL DEFAULT '',
                    ownership TEXT NOT NULL DEFAULT '',
                    address TEXT NOT NULL DEFAULT '',
                    icon_url TEXT NOT NULL DEFAULT '',
                    website TEXT NOT NULL DEFAULT '',
                    source_url TEXT NOT NULL DEFAULT '',
                    badges TEXT NOT NULL DEFAULT '',
                    authority TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, province)
                )
                """
            )
            self._ensure_column(conn, "address", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "icon_url", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "source_url", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "badges", "TEXT NOT NULL DEFAULT ''")
            self._ensure_column(conn, "authority", "TEXT NOT NULL DEFAULT ''")
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS universities_updated_at
                AFTER UPDATE ON universities
                BEGIN
                    UPDATE universities
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = NEW.id;
                END
                """
            )

    def add(self, university: University) -> int:
        university.validate()
        self.initialize()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO universities (
                    name, province, city, level, school_type, ownership, address,
                    icon_url, website, source_url, badges, authority, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    university.name.strip(),
                    university.province.strip(),
                    university.city.strip(),
                    university.level.strip(),
                    university.school_type.strip(),
                    university.ownership.strip(),
                    university.address.strip(),
                    university.icon_url.strip(),
                    university.website.strip(),
                    university.source_url.strip(),
                    university.badges.strip(),
                    university.authority.strip(),
                    university.notes.strip(),
                ),
            )
            return int(cursor.lastrowid)

    def get(self, university_id: int) -> University | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM universities WHERE id = ?",
                (university_id,),
            ).fetchone()
        return self._from_row(row) if row else None

    def search(
        self,
        *,
        keyword: str = "",
        province: str = "",
        level: str = "",
        school_type: str = "",
    ) -> list[University]:
        self.initialize()
        clauses: list[str] = []
        params: list[str] = []

        if keyword:
            clauses.append("(name LIKE ? OR city LIKE ? OR notes LIKE ?)")
            value = f"%{keyword}%"
            params.extend([value, value, value])
        if province:
            clauses.append("province = ?")
            params.append(province)
        if level:
            clauses.append("level = ?")
            params.append(level)
        if school_type:
            clauses.append("school_type = ?")
            params.append(school_type)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"SELECT * FROM universities {where} ORDER BY province, name"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._from_row(row) for row in rows]

    def bulk_add(self, universities: Iterable[University]) -> int:
        count = 0
        for university in universities:
            self.add(university)
            count += 1
        return count

    def upsert(self, university: University) -> int:
        university.validate()
        self.initialize()
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id FROM universities WHERE name = ? AND province = ?",
                (university.name.strip(), university.province.strip()),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE universities
                    SET city = ?,
                        level = ?,
                        school_type = ?,
                        ownership = ?,
                        address = ?,
                        icon_url = ?,
                        website = ?,
                        source_url = ?,
                        badges = ?,
                        authority = ?,
                        notes = ?
                    WHERE id = ?
                    """,
                    (
                        university.city.strip(),
                        university.level.strip(),
                        university.school_type.strip(),
                        university.ownership.strip(),
                        university.address.strip(),
                        university.icon_url.strip(),
                        university.website.strip(),
                        university.source_url.strip(),
                        university.badges.strip(),
                        university.authority.strip(),
                        university.notes.strip(),
                        existing["id"],
                    ),
                )
                return int(existing["id"])
            return self.add(university)

    def bulk_upsert(self, universities: Iterable[University]) -> int:
        count = 0
        for university in universities:
            self.upsert(university)
            count += 1
        return count

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _from_row(row: sqlite3.Row) -> University:
        return University(
            id=row["id"],
            name=row["name"],
            province=row["province"],
            city=row["city"],
            level=row["level"],
            school_type=row["school_type"],
            ownership=row["ownership"],
            address=row["address"],
            icon_url=row["icon_url"],
            website=row["website"],
            source_url=row["source_url"],
            badges=row["badges"],
            authority=row["authority"],
            notes=row["notes"],
        )

    @staticmethod
    def _ensure_column(conn: sqlite3.Connection, column_name: str, definition: str) -> None:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(universities)")}
        if column_name not in columns:
            conn.execute(f"ALTER TABLE universities ADD COLUMN {column_name} {definition}")
