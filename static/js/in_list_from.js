(function () {
  // 1) key 읽기
  const params = new URLSearchParams(location.search);
  const key = params.get("key");
  if (!key) return showEmpty("key가 없습니다. (미리보기 버튼으로 열었는지 확인)");

  // 2) localStorage에서 payload 읽기
  const raw = localStorage.getItem(key);
  if (!raw) return showEmpty("엑셀 데이터가 없습니다. (localStorage key 없음)");

  let payload;
  try { payload = JSON.parse(raw); }
  catch { return showEmpty("payload JSON 파싱 실패"); }

  const rows = Array.isArray(payload.rows) ? payload.rows : [];
  if (!rows.length) return showEmpty("rows가 비어있습니다.");

  // 3) 상단 표시
  setText("#pv_filename", payload.filename || "");
  setText("#pv_total_count", String(rows.length));
  setText("#pv_total_qty", fmt(payload.totalQty));
  setText("#pv_total_wt", fmt(payload.totalWeight));

  // 4) 테이블 렌더
  const tbody = document.querySelector("#pv_tbody");
  tbody.innerHTML = rows.slice(0, 1000).map(r => `
      <tr>
        <td>${esc(r.lot_no)}</td>
        <td>${esc(r.owner_name)}</td>
        <td>${esc(r.cargo_type)}</td>
        <td>${esc(r.size)}</td>
        <td style="text-align:right">${fmt(r.unit_wt)}</td>
        <td style="text-align:right">${fmt(r.stock_qty)}</td>
        <td style="text-align:right">${fmt(r.stock_wt)}</td>
      </tr>
    `).join("");

  // 5) 저장 버튼
  const btn = document.querySelector("#btnSaveJson");
  btn.disabled = false;
  btn.addEventListener("click", async () => {
    if (!confirm(`${rows.length}건을 저장할까요?`)) return;

    try {
      const res = await fetch("/in_bulk_save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rows })
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok && data.result === "ok") {
        alert("입고 일괄 저장 완료");
        localStorage.removeItem(key);
        // 부모창 갱신(있으면)
        try { if (window.opener && !window.opener.closed) window.opener.location.reload(); } catch (e) { }
        window.close();
      } else {
        alert("저장 실패: " + (data.msg || "서버 오류"));
      }
    } catch (err) {
      console.error(err);
      alert("저장 중 오류: " + (err?.message || err));
    }
  });

  // --- helpers ---
  function showEmpty(msg) {
    const e = document.querySelector("#pv_error");
    if (e) e.textContent = msg;
    const btn = document.querySelector("#btnSaveJson");
    if (btn) btn.disabled = true;
  }
  function setText(sel, v) {
    const el = document.querySelector(sel);
    if (el) el.textContent = v;
  }
  function esc(v) {
    return String(v ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
  function fmt(v) {
    const n = Number(v);
    if (!Number.isFinite(n)) return "0";
    return n.toLocaleString();
  }
})();