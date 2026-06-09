from __future__ import annotations

import argparse
import re
import ssl
import time
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .models import University
from .repository import UniversityRepository


BASE_URL = "https://www.gk100.com"
LIST_URL = f"{BASE_URL}/daxueku"
DEFAULT_DB_PATH = Path("data/schools.db")
DEFAULT_TOTAL_PAGES = 151


@dataclass(frozen=True)
class ImportResult:
    pages: int
    universities: int


def import_gk100_universities(
    db_path: str | Path = DEFAULT_DB_PATH,
    *,
    start_page: int = 1,
    total_pages: int = DEFAULT_TOTAL_PAGES,
    delay: float = 0.2,
    insecure: bool = False,
) -> ImportResult:
    repo = UniversityRepository(db_path)
    repo.initialize()

    imported = 0
    pages_done = 0
    for page in range(start_page, total_pages + 1):
        html = fetch_page(page, insecure=insecure)
        universities = parse_universities(html)
        if not universities:
            break
        imported += repo.bulk_upsert(universities)
        pages_done += 1
        print(f"Imported page {page}: {len(universities)} schools")
        if delay:
            time.sleep(delay)
    return ImportResult(pages=pages_done, universities=imported)


def fetch_page(page: int, *, insecure: bool = False) -> str:
    url = LIST_URL if page <= 1 else f"{LIST_URL}?p={page}"
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    context = ssl._create_unverified_context() if insecure else None
    with urlopen(request, timeout=30, context=context) as response:
        return response.read().decode("utf-8", "ignore")


def parse_universities(html: str) -> list[University]:
    sections = re.findall(r"<section>\s*(<a\s+href=\"/daxueku/\d+\".*?</a>)\s*</section>", html, re.S)
    return [university for section in sections if (university := parse_university(section))]


def parse_university(section_html: str) -> University | None:
    href = _match(r'<a\s+href="([^"]+)"', section_html)
    name = _clean(_match(r"<h3[^>]*>(.*?)</h3>", section_html))
    icon_url = _match(r'<img[^>]+src="([^"]+)"', section_html)
    details_block = _match(r'<div class="text-14 mb-10">(.*?)</div>', section_html)
    badges = [_clean(value) for value in re.findall(r"<span[^>]*>(.*?)</span>", section_html, re.S)]
    badges = [value for value in badges if value and value != "查看详情>"]

    if not href or not name:
        return None

    details = [part for part in (_clean(part) for part in details_block.split("|")) if part]
    province = details[0] if len(details) > 0 else "未知"
    level = details[1] if len(details) > 1 else ""
    school_type = details[2] if len(details) > 2 else ""
    ownership = details[3] if len(details) > 3 else ""
    authority = details[4] if len(details) > 4 else ""

    return University(
        name=name,
        province=province,
        city=province,
        level=level,
        school_type=school_type,
        ownership=ownership,
        address=province,
        icon_url=urljoin(BASE_URL, icon_url),
        source_url=urljoin(BASE_URL, href),
        badges="、".join(badges),
        authority=authority,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import university data from gk100.com.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--pages", type=int, default=DEFAULT_TOTAL_PAGES)
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between page requests.")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Skip TLS verification if the local Python CA store is unavailable.",
    )
    args = parser.parse_args(argv)

    result = import_gk100_universities(
        args.db,
        start_page=args.start_page,
        total_pages=args.pages,
        delay=args.delay,
        insecure=args.insecure,
    )
    print(f"Done. Imported {result.universities} schools from {result.pages} pages.")
    return 0


def _match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.S)
    return match.group(1).strip() if match else ""


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


if __name__ == "__main__":
    raise SystemExit(main())
