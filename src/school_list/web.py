from __future__ import annotations

import argparse
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode, parse_qs, urlparse

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


def create_handler(repo: UniversityRepository) -> type[BaseHTTPRequestHandler]:
    class SchoolListHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._render_index(parsed.query)
                return
            if parsed.path.startswith("/schools/"):
                self._render_detail(parsed.path)
                return
            if parsed.path == "/health":
                self._send_text("ok")
                return
            self._send_html(_page("页面未找到", "<main><h1>页面未找到</h1></main>"), HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _render_index(self, query: str) -> None:
            params = parse_qs(query)
            keyword = params.get("keyword", [""])[0].strip()
            level = params.get("level", [""])[0].strip()
            page = _positive_int(params.get("page", ["1"])[0], default=1)
            universities = repo.search(keyword=keyword, level=level)
            body = _render_index_body(universities, keyword=keyword, level=level, page=page)
            self._send_html(_page("学校列表", body))

        def _render_detail(self, path: str) -> None:
            try:
                university_id = int(path.rsplit("/", 1)[-1])
            except ValueError:
                self._send_html(_page("学校不存在", "<main><h1>学校不存在</h1></main>"), HTTPStatus.NOT_FOUND)
                return

            university = repo.get(university_id)
            if university is None:
                self._send_html(_page("学校不存在", "<main><h1>学校不存在</h1></main>"), HTTPStatus.NOT_FOUND)
                return
            self._send_html(_page(university.name, _render_detail_body(university)))

        def _send_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
            payload = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_text(self, text: str) -> None:
            payload = text.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return SchoolListHandler


def seed_if_empty(repo: UniversityRepository) -> None:
    if repo.search():
        return
    repo.bulk_add(SAMPLE_UNIVERSITIES)


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    repo = UniversityRepository(db_path)
    repo.initialize()
    seed_if_empty(repo)
    server = ThreadingHTTPServer((host, port), create_handler(repo))
    print(f"School list web app running at http://{host}:{port}")
    server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the school list web app.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    args = parser.parse_args(argv)
    serve(host=args.host, port=args.port, db_path=args.db)
    return 0


def _render_index_body(
    universities: list[University],
    *,
    keyword: str,
    level: str,
    page: int = 1,
) -> str:
    total = len(universities)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    current_page = min(max(page, 1), total_pages)
    start = (current_page - 1) * PAGE_SIZE
    page_items = universities[start : start + PAGE_SIZE]
    cards = "\n".join(_render_school_card(university) for university in page_items)
    if not cards:
        cards = '<p class="empty">没有找到匹配的学校</p>'

    return f"""
    <header class="topbar">
      <div>
        <p class="eyebrow">Gaokao University Manager</p>
        <h1>学校列表</h1>
      </div>
      <form class="filters" method="get">
        <input name="keyword" placeholder="搜索学校、城市或备注" value="{escape(keyword)}">
        <select name="level">
          {_level_options(level)}
        </select>
        <button type="submit">查询</button>
      </form>
    </header>
    <main>
      <section class="result-meta">
        <strong>共 {total} 所学校</strong>
        <span>第 {current_page} / {total_pages} 页，每页 20 所</span>
      </section>
      <section class="school-grid">
        {cards}
      </section>
      {_pagination(current_page, total_pages, keyword=keyword, level=level)}
    </main>
    """


def _render_school_card(university: University) -> str:
    detail_url = f"/schools/{university.id}"
    location = university.address or university.city or university.province or "待补充"
    icon = university.icon_url or "https://lib.gk100.com/gk100/web/static/images/favicon.png"
    badges = _badge_group(university.badges)
    return f"""
    <a class="school-card" href="{detail_url}">
      <img class="school-logo" src="{escape(icon)}" alt="{escape(university.name)}">
      <div class="school-card-main">
        <div class="school-card-head">
          <h2>{escape(university.name)}</h2>
          <span class="badge">{escape(university.level or "未标注")}</span>
        </div>
        <dl>
          <div><dt>学校类别</dt><dd>{escape(university.school_type or "待补充")}</dd></div>
          <div><dt>学校位置</dt><dd>{escape(location)}</dd></div>
          <div><dt>办学性质</dt><dd>{escape(university.ownership or "待补充")}</dd></div>
        </dl>
        {badges}
      </div>
    </a>
    """


def _render_detail_body(university: University) -> str:
    return f"""
    <header class="detail-hero">
      <a class="back-link" href="/">返回列表</a>
      <h1>{escape(university.name)}</h1>
      <span class="badge">{escape(university.level or "未标注")}</span>
    </header>
    <main>
      <section class="detail-grid">
        {_detail_item("学校名称", university.name)}
        {_detail_item("学校等级", university.level)}
        {_detail_item("学校标签", university.badges)}
        {_detail_item("学校地址", university.address)}
        {_detail_item("学校官网页面地址", university.website, is_link=True)}
        {_detail_item("高考100页面地址", university.source_url, is_link=True)}
        {_detail_item("所在省份", university.province)}
        {_detail_item("所在城市", university.city)}
        {_detail_item("学校类型", university.school_type)}
        {_detail_item("备注", university.notes)}
      </section>
    </main>
    """


def _detail_item(label: str, value: object, *, is_link: bool = False) -> str:
    text = str(value or "待补充")
    rendered = _website_link(text) if is_link and text != "待补充" else escape(text)
    return f"""
    <article class="detail-item">
      <span>{escape(label)}</span>
      <strong>{rendered}</strong>
    </article>
    """


def _website_link(website: str) -> str:
    if not website:
        return "待补充"
    safe_website = escape(website)
    return f'<a href="{safe_website}" target="_blank" rel="noreferrer" onclick="event.stopPropagation()">{safe_website}</a>'


def _level_options(selected: str) -> str:
    levels = ["", "本科", "专科", "985", "211", "双一流", "普通本科", "普通专科"]
    labels = {"": "全部等级"}
    return "\n".join(
        f'<option value="{escape(level)}" {"selected" if level == selected else ""}>'
        f"{escape(labels.get(level, level))}</option>"
        for level in levels
    )


def _badge_group(badges: str) -> str:
    values = [value for value in badges.split("、") if value][:6]
    if not values:
        return ""
    return '<div class="tag-row">' + "".join(
        f'<span class="tag">{escape(value)}</span>' for value in values
    ) + "</div>"


def _pagination(current_page: int, total_pages: int, *, keyword: str, level: str) -> str:
    if total_pages <= 1:
        return ""
    prev_page = max(1, current_page - 1)
    next_page = min(total_pages, current_page + 1)
    prev_disabled = " disabled" if current_page <= 1 else ""
    next_disabled = " disabled" if current_page >= total_pages else ""
    return f"""
    <nav class="pagination">
      <a class="{prev_disabled}" href="{_page_url(prev_page, keyword=keyword, level=level)}">上一页</a>
      <span>{current_page} / {total_pages}</span>
      <a class="{next_disabled}" href="{_page_url(next_page, keyword=keyword, level=level)}">下一页</a>
    </nav>
    """


def _page_url(page: int, *, keyword: str, level: str) -> str:
    params = {"page": str(page)}
    if keyword:
        params["keyword"] = keyword
    if level:
        params["level"] = level
    return "/?" + urlencode(params)


def _positive_int(value: str, *, default: int) -> int:
    try:
        number = int(value)
    except ValueError:
        return default
    return number if number > 0 else default


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} - School List</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #18212f;
      --muted: #667085;
      --line: #d8dee8;
      --surface: #ffffff;
      --page: #f4f7fb;
      --accent: #0f766e;
      --accent-strong: #0b5f59;
      --badge-bg: #fff4d6;
      --badge-ink: #805600;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background: var(--page);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
    }}
    .topbar, .detail-hero {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 24px;
      padding: 32px clamp(16px, 5vw, 64px) 22px;
      background: var(--surface);
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0;
      font-size: 30px;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    .eyebrow {{
      margin: 0 0 6px;
      color: var(--muted);
      font-size: 13px;
    }}
    .filters {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    input, select, button {{
      height: 40px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 12px;
      background: white;
      color: var(--ink);
      font: inherit;
    }}
    input {{ width: min(280px, 70vw); }}
    button {{
      border-color: var(--accent);
      background: var(--accent);
      color: white;
      cursor: pointer;
    }}
    button:hover {{ background: var(--accent-strong); }}
    main {{ padding: 24px clamp(16px, 5vw, 64px) 48px; }}
    .result-meta {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
      color: var(--muted);
      font-size: 14px;
    }}
    .result-meta strong {{ color: var(--ink); }}
    .school-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .school-card {{
      display: grid;
      grid-template-columns: 68px minmax(0, 1fr);
      gap: 14px;
      min-height: 176px;
      padding: 18px;
      color: var(--ink);
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      text-decoration: none;
    }}
    .school-card:hover {{
      border-color: #97c9c4;
      box-shadow: 0 10px 24px rgba(15, 118, 110, 0.12);
      text-decoration: none;
    }}
    .school-logo {{
      width: 64px;
      height: 64px;
      border-radius: 8px;
      object-fit: contain;
      background: #f8fafc;
      border: 1px solid var(--line);
    }}
    .school-card-main {{ min-width: 0; }}
    .school-card-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 12px;
    }}
    .school-card h2 {{
      margin: 0;
      font-size: 19px;
      line-height: 1.35;
      letter-spacing: 0;
    }}
    dl {{
      display: grid;
      gap: 7px;
      margin: 0;
    }}
    dl div {{
      display: grid;
      grid-template-columns: 72px minmax(0, 1fr);
      gap: 8px;
    }}
    dt {{
      color: var(--muted);
      font-size: 13px;
    }}
    dd {{
      margin: 0;
      overflow-wrap: anywhere;
      font-size: 14px;
    }}
    a {{ color: var(--accent-strong); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 3px 10px;
      border-radius: 999px;
      color: var(--badge-ink);
      background: var(--badge-bg);
      font-size: 13px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .tag-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 12px;
    }}
    .tag {{
      min-height: 22px;
      padding: 2px 7px;
      border-radius: 4px;
      color: #53606f;
      background: #eef2f7;
      font-size: 12px;
    }}
    .empty {{ color: var(--muted); text-align: center; }}
    .pagination {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      margin-top: 24px;
    }}
    .pagination a {{
      min-width: 80px;
      padding: 9px 14px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--surface);
      text-align: center;
    }}
    .pagination a.disabled {{
      pointer-events: none;
      color: #a0a8b3;
      background: #eef2f7;
    }}
    .detail-hero {{
      align-items: flex-start;
      flex-direction: column;
    }}
    .back-link {{ font-size: 14px; }}
    .detail-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 14px;
    }}
    .detail-item {{
      min-height: 96px;
      padding: 18px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .detail-item span {{
      display: block;
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 13px;
    }}
    .detail-item strong {{
      display: block;
      line-height: 1.5;
      overflow-wrap: anywhere;
    }}
    @media (max-width: 720px) {{
      .topbar {{ align-items: stretch; flex-direction: column; }}
      .filters {{ justify-content: stretch; }}
      input, select, button {{ width: 100%; }}
      h1 {{ font-size: 26px; }}
      .school-grid {{ grid-template-columns: 1fr; }}
      .school-card {{ grid-template-columns: 56px minmax(0, 1fr); padding: 14px; }}
      .school-logo {{ width: 52px; height: 52px; }}
      .school-card-head {{ flex-direction: column; }}
      .result-meta {{ flex-direction: column; }}
    }}
  </style>
</head>
<body>{body}</body>
</html>"""


if __name__ == "__main__":
    raise SystemExit(main())
