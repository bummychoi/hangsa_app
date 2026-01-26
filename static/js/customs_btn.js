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


function applyStatusStyle(sel){
  const v = (sel.value || "").trim();

  sel.style.color = "#fff";

  if (v === "미통관") {
    sel.style.background = "#e11d48"; // 빨강
  } else if (v === "부분통관") {
    sel.style.background = "#f59e0b"; // 노랑(글자 흰색)
  } else if (v === "통관") {
    sel.style.background = "#2563eb"; // 파랑
  } else {
    sel.style.background = "";
    sel.style.color = "";
  }
}

document.addEventListener("change", function(e){
  const sel = e.target.closest(".customs-status");
  if(!sel) return;
  applyStatusStyle(sel);
});

window.addEventListener("DOMContentLoaded", function(){
  document.querySelectorAll(".customs-status").forEach(applyStatusStyle);
});
