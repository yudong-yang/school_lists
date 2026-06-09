const hero = document.querySelector("#detailHero");
const detailGrid = document.querySelector("#detailGrid");

async function loadSchoolDetail() {
  const response = await fetch(`/api/schools/${window.SCHOOL_ID}`);
  if (!response.ok) {
    hero.querySelector("h1").textContent = "学校不存在";
    detailGrid.innerHTML = "";
    return;
  }

  const school = await response.json();
  document.title = `${school.name} - School List`;
  hero.innerHTML = `
    <a class="back-link" href="/">返回列表</a>
    <div class="detail-title">
      <img class="school-logo large" src="${escapeHtml(school.icon_url || defaultLogo())}" alt="${escapeHtml(school.name)}">
      <div>
        <h1>${escapeHtml(school.name)}</h1>
        <span class="badge">${escapeHtml(school.level || "未标注")}</span>
      </div>
    </div>
  `;

  detailGrid.innerHTML = [
    detailItem("学校名称", school.name),
    detailItem("学校等级", school.level),
    detailItem("学校标签", (school.badge_list || []).join("、")),
    detailItem("学校地址", school.address),
    detailItem("学校官网页面地址", school.website, true),
    detailItem("高考100页面地址", school.source_url, true),
    detailItem("所在省份", school.province),
    detailItem("所在城市", school.city),
    detailItem("学校类型", school.school_type),
    detailItem("办学性质", school.ownership),
    detailItem("主管部门", school.authority),
  ].join("");
}

function detailItem(label, value, isLink = false) {
  const text = value || "待补充";
  const body = isLink && value
    ? `<a href="${escapeHtml(value)}" target="_blank" rel="noreferrer">${escapeHtml(value)}</a>`
    : escapeHtml(text);

  return `
    <article class="detail-item">
      <span>${escapeHtml(label)}</span>
      <strong>${body}</strong>
    </article>
  `;
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

loadSchoolDetail();
