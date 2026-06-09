from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class University:
    name: str
    province: str
    city: str = ""
    level: str = ""
    school_type: str = ""
    ownership: str = ""
    address: str = ""
    icon_url: str = ""
    website: str = ""
    source_url: str = ""
    badges: str = ""
    authority: str = ""
    notes: str = ""
    id: int | None = None

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("University name is required.")
        if not self.province.strip():
            raise ValueError("Province is required.")
