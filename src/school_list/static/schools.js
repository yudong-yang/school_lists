const PAGE_SIZE = 20;

const filterForm = document.querySelector("#schoolFilters");
const grid = document.querySelector("#schoolGrid");
const resultMeta = document.querySelector("#resultMeta");
const pagination = document.querySelector("#pagination");

let currentPage = Number(new URLSearchParams(window.location.search).get("page") || "1");

filterForm.addEventListener("submit", (event) => {
  event.preventDefault();
  currentPage = 1;
  loadSchools();
});

async function loadSchools() {
  const formData = new FormData(filterForm);
  const params = new URLSearchParams({
    page: String(currentPage),
    page_size: String(PAGE_SIZE),
  });

  for (const [key, value] of formData.entries()) {
    if (value) params.set(key, value);
  }

  const response = await fetch(`/api/schools?${params.toString()}`);
  const payload = await response.json();
  renderMeta(payload.pagination);
  renderSchools(payload.items);
  renderPagination(payload.pagination);
}

function renderMeta(meta) {
  resultMeta.innerHTML = `
    <strong>共 ${meta.total} 所学校</strong>
    <span>第 ${meta.page} / ${meta.total_pages} 页，每页 ${meta.page_size} 所</span>
  `;
}

function renderSchools(schools) {
  if (!schools.length) {
    grid.innerHTML = '<p class="empty">没有找到匹配的学校</p>';
    return;
  }

  grid.innerHTML = schools.map((school) => `
    <a class="school-card" href="/schools/${school.id}">
      <img class="school-logo" src="${escapeHtml(school.icon_url || defaultLogo())}" alt="${escapeHtml(school.name)}">
      <div class="school-card-main">
        <div class="school-card-head">
          <h2>${escapeHtml(school.name)}</h2>
          <span class="badge">${escapeHtml(school.level || "未标注")}</span>
        </div>
        <dl>
          <div><dt>学校类别</dt><dd>${escapeHtml(school.school_type || "待补充")}</dd></div>
          <div><dt>学校位置</dt><dd>${escapeHtml(school.display_location || "待补充")}</dd></div>
          <div><dt>办学性质</dt><dd>${escapeHtml(school.ownership || "待补充")}</dd></div>
        </dl>
        ${renderTags(school.badge_list)}
      </div>
    </a>
  `).join("");
}

function renderPagination(meta) {
  if (meta.total_pages <= 1) {
    pagination.innerHTML = "";
    return;
  }

  pagination.innerHTML = `
    <button type="button" ${meta.page <= 1 ? "disabled" : ""} data-page="${meta.page - 1}">上一页</button>
    <span>${meta.page} / ${meta.total_pages}</span>
    <button type="button" ${meta.page >= meta.total_pages ? "disabled" : ""} data-page="${meta.page + 1}">下一页</button>
  `;

  pagination.querySelectorAll("button[data-page]").forEach((button) => {
    button.addEventListener("click", () => {
      currentPage = Number(button.dataset.page);
      loadSchools();
    });
  });
}

function renderTags(tags) {
  const visibleTags = (tags || []).slice(0, 6);
  if (!visibleTags.length) return "";
  return `<div class="tag-row">${visibleTags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div>`;
}

function defaultLogo() {
  return "https://lib.gk100.com/gk100/web/static/images/favicon.png";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

loadSchools();
