from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request

from .models import University
from .repository import UniversityRepository


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_DB_PATH = Path("data/schools.db")
PAGE_SIZE = 20

SAMPLE_UNIVERSITIES = [
    University(
        name="清华大学",
        province="北京",
        city="北京",
        level="985",
        school_type="综合",
        address="北京市海淀区清华园1号",
        website="https://www.tsinghua.edu.cn",
    ),
    University(
        name="北京邮电大学",
        province="北京",
        city="北京",
        level="211",
        school_type="理工",
        address="北京市海淀区西土城路10号",
        website="https://www.bupt.edu.cn",
    ),
    University(
        name="南方科技大学",
        province="广东",
        city="深圳",
        level="双一流",
        school_type="理工",
        address="广东省深圳市南山区学苑大道1088号",
        website="https://www.sustech.edu.cn",
    ),
    University(
        name="深圳大学",
        province="广东",
        city="深圳",
        level="普通本科",
        school_type="综合",
        address="广东省深圳市南山区南海大道3688号",
        website="https://www.szu.edu.cn",
    ),
    University(
        name="深圳职业技术大学",
        province="广东",
        city="深圳",
        level="普通专科",
        school_type="综合",
        address="广东省深圳市南山区西丽湖",
        website="https://www.szpu.edu.cn",
    ),
]


def create_app(db_path: str | Path = DEFAULT_DB_PATH) -> Flask:
    app = Flask(__name__)
    repo = UniversityRepository(db_path)
    repo.initialize()
    seed_if_empty(repo)

    @app.get("/")
    def index() -> str:
        return render_template("index.html", levels=_level_options())

    @app.get("/schools/<int:school_id>")
    def detail(school_id: int) -> str:
        return render_template("detail.html", school_id=school_id)

    @app.get("/api/schools")
    def api_schools():
        keyword = request.args.get("keyword", "").strip()
        level = request.args.get("level", "").strip()
        page = _positive_int(request.args.get("page", "1"), default=1)
        page_size = _positive_int(request.args.get("page_size", str(PAGE_SIZE)), default=PAGE_SIZE)
        page_size = min(page_size, 100)

        universities = repo.search(keyword=keyword, level=level)
        total = len(universities)
        total_pages = max(1, (total + page_size - 1) // page_size)
        current_page = min(max(page, 1), total_pages)
        start = (current_page - 1) * page_size
        items = universities[start : start + page_size]

        return jsonify(
            {
                "items": [_serialize_university(university) for university in items],
                "pagination": {
                    "page": current_page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                },
            }
        )

    @app.get("/api/schools/<int:school_id>")
    def api_school(school_id: int):
        university = repo.get(school_id)
        if university is None:
            abort(404)
        return jsonify(_serialize_university(university))

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


def seed_if_empty(repo: UniversityRepository) -> None:
    if repo.search():
        return
    repo.bulk_add(SAMPLE_UNIVERSITIES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Flask school list web app.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    app = create_app(args.db)
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


def _serialize_university(university: University) -> dict[str, object]:
    data = asdict(university)
    data["display_location"] = university.address or university.city or university.province or "待补充"
    data["badge_list"] = [badge for badge in university.badges.split("、") if badge]
    return data


def _level_options() -> list[str]:
    return ["本科", "专科", "985", "211", "双一流", "普通本科", "普通专科"]


def _positive_int(value: str, *, default: int) -> int:
    try:
        number = int(value)
    except ValueError:
        return default
    return number if number > 0 else default


if __name__ == "__main__":
    raise SystemExit(main())
