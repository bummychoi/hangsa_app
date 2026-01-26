document.addEventListener("dblclick", function (e) {
  const tr = e.target.closest("tbody tr");
  if (!tr) return;
  if (e.target.closest("select")) return;

  const cell = tr.querySelector("td.cargo-no");
  const raw = (cell?.textContent || "").trim();

  if (!raw) {
    alert("화물관리번호(cargMtNo)를 찾을 수 없습니다.");
    return;
  }

  const cargMtNo = raw.replaceAll("-", "").replace(/\s+/g, "").toUpperCase();

  const base = "https://mcube.ne.kr/interface/cargoTracking.do";
  const url = `${base}?yhtService=whp&cargMtNo=${encodeURIComponent(cargMtNo)}`;

  window.open(url, "_blank", "noopener,noreferrer");
});
