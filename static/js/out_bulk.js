// ======================================================
// OUT BULK (paste): 1개 표로만 출력
// - 출고번호(out_no) 헤더행 + lot_no별 한줄 + 출고번호 소계 + 일일합계
// out_no = 일자(YYYYMMDD) + 번호(4자리)
// ======================================================

(function () {

    // ---------- util ----------
    function num(v) {
        if (v == null) return 0;
        const s = String(v).replace(/,/g, "").trim();
        const x = parseFloat(s);
        return Number.isFinite(x) ? x : 0;
    }

    function fmt1(v) {
        const n = Number(v);
        return Number.isFinite(n) ? n.toFixed(1) : "0.0";
    }

    function fmt3(v) {
        const n = Number(v);
        return Number.isFinite(n) ? n.toFixed(3) : "0.000";
    }

    function esc(s) {
        return String(s ?? "").replace(/[&<>"']/g, (m) => (
            { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[m]
        ));
    }

    // 헤더 정규화(매칭 안정화)
    function normHeader(h) {
        return String(h ?? "")
            .trim()
            .replace(/\s+/g, "")           // 공백 제거
            .replace(/[()]/g, "")          // 괄호 제거
            .replace(/[_\-]/g, "")         // _ - 제거
            .replace(/[\/]/g, "")          // / 제거 (LOT/NO -> LOTNO)
            .toUpperCase();
    }

    // pattern은 정규식 배열(원본 헤더/정규화 헤더 둘 다 검사)
    function findColIndex(headers, patterns) {
        for (let i = 0; i < headers.length; i++) {
            const raw = String(headers[i] ?? "").trim();
            const h1 = raw.replace(/\s+/g, "").trim();
            const h2 = normHeader(raw);
            for (const p of patterns) {
                if (p.test(h1) || p.test(h2)) return i;
            }
        }
        return -1;
    }

    function padNo(v, len = 4) {
        const s = String(v ?? "").trim();
        if (!s) return "";
        return s.padStart(len, "0");
    }

    // "2026-01-12" / "20260112" / "2026/01/12" -> "20260112"
    function normDate(v) {
        const s = String(v ?? "").trim();
        if (!s) return "";
        if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s.replaceAll("-", "");
        if (/^\d{8}$/.test(s)) return s;
        if (/^\d{4}\/\d{2}\/\d{2}$/.test(s)) return s.replaceAll("/", "");
        return s.replaceAll("-", "").replaceAll("/", "");
    }

    // 출고수량 컬럼: 우선순위로 찾기 (수량이 너무 많아서 오동작 방지)
    function findOutQtyIndex(headers) {
        const candidates = [
            [/^출고수량$/i, /출고수량/i, /OUTQTY/i],
            [/^운송수량$/i, /운송수량/i, /TRANSQTY/i],
            [/^수불수량$/i, /수불수량/i],
            // 마지막 fallback (정말 없을 때만)
            [/^수량$/i],
        ];

        for (const pats of candidates) {
            const idx = findColIndex(headers, pats);
            if (idx !== -1) return idx;
        }
        return -1;
    }

    // ---------- parse ----------
    function parseOutBulkText(raw) {
        const lines = raw.trim().split(/\r?\n/).filter(l => l.trim() !== "");
        if (!lines.length) return [];

        const grid = lines.map(l => l.split("\t"));
        const headers = (grid.shift() || []).map(x => String(x ?? "").trim());

        // 헤더 기반 인덱스 찾기
        const idxDate = findColIndex(headers, [/^일자$/i, /작업일자/i, /출고일자/i, /DATE/i]);
        const idxNo = findColIndex(headers, [/^번호$/i, /전표번호/i, /출고번호/i, /NO$/i]);

        // LOT/NO (강화)
        const idxLot = findColIndex(headers, [/^LOTNO$/i, /^LOT\/?NO$/i, /LOTNO/i, /LOT_NO/i, /^LOT$/i]);

        const idxOwner = findColIndex(headers, [/화주명/i, /^화주$/i, /OWNER/i]);

        // 품명: "품명" 없으면 "강종"도 품명으로 대체
        const idxItem = findColIndex(headers, [/^품명$/i, /품\s*명/i, /^강종$/i, /강종/i, /ITEM/i]);

        const idxSize = findColIndex(headers, [/규격/i, /사이즈/i, /SIZE/i]);
        const idxMaker = findColIndex(headers, [/제강사/i, /MAKER/i]);
        const idxCar = findColIndex(headers, [/차량번호/i, /^차량$/i, /차량NO/i, /CAR/i]);

        // ✅ 출고수량
        const idxOutQty = findOutQtyIndex(headers);

        // ✅ 수불중량(필수)
        const idxInout = findColIndex(headers, [/수불중량/i, /수불\s*중량/i, /INOUTWT/i, /중량t/i]);

        // 필수 체크
        const need = [
            ["일자", idxDate],
            ["번호", idxNo],
            ["LOT/NO", idxLot],
            ["화주명", idxOwner],
            ["출고수량(출고수량/운송수량/수불수량/수량)", idxOutQty],
            ["수불중량", idxInout],
        ];
        const missing = need.filter(([_, idx]) => idx === -1).map(([name]) => name);

        if (missing.length) {
            alert("엑셀 헤더에서 필수 컬럼을 못 찾음: " + missing.join(", ") + "\n콘솔에서 headers 확인하세요.");
            console.log("headers(raw):", headers);
            console.log("headers(norm):", headers.map(normHeader));
            return [];
        }

        const rows = grid.map(cols => {
            const d = normDate(cols[idxDate]);
            const n = padNo(cols[idxNo], 4);
            const out_no = `${d}${n}`;

            return {
                out_no,
                lot_no: String(cols[idxLot] ?? "").trim(),
                owner_name: String(cols[idxOwner] ?? "").trim(),
                item_name: idxItem === -1 ? "" : String(cols[idxItem] ?? "").trim(),
                size: idxSize === -1 ? "" : String(cols[idxSize] ?? "").trim(),
                maker: idxMaker === -1 ? "" : String(cols[idxMaker] ?? "").trim(),
                car_no: idxCar === -1 ? "" : String(cols[idxCar] ?? "").trim(),
                out_qty: num(cols[idxOutQty]),
                inout_wt: num(cols[idxInout]),
            };
        }).filter(r => r.out_no && r.lot_no);

        console.log("parsed sample:", rows.slice(0, 5));
        return rows;
    }
    // ✅ 전역 노출(구코드 호환 포함)  ← 추가
    window.parseOutBulkText = parseOutBulkText;
    window.parseBulkText = parseOutBulkText;

    // ---------- group ----------
    function buildOutNoGroups(rows) {
        const map = new Map();

        rows.forEach(r => {
            const key = r.out_no;
            if (!map.has(key)) {
                map.set(key, { out_no: key, items: [], sum_qty: 0, sum_wt: 0 });
            }
            const g = map.get(key);
            g.items.push(r);
            g.sum_qty += num(r.out_qty);
            g.sum_wt += num(r.inout_wt);
        });

        const groups = Array.from(map.values()).sort((a, b) => a.out_no.localeCompare(b.out_no));
        groups.forEach(g => g.items.sort((a, b) => (a.lot_no || "").localeCompare(b.lot_no || "")));
        return groups;
    }

    // ---------- render: SINGLE TABLE ----------
    function renderSingleTable(groups, workDate) {
        let dayCnt = 0, daySumQty = 0, daySumWt = 0;

        let html = `
      <h2 style="margin:0 0 10px 0;">출고번호 → LOT/NO 리스트</h2>
      <div style="margin-bottom:14px;color:#555;">
        작업일자: <b>${esc(workDate || "")}</b> / 출고번호 수: <b>${groups.length}</b>
        <button type="button" id="btnSaveOut" class="btn btn-primary btn-sm" onclick="all_out_save()">저장</button>
        <button type="button"  class="btn btn-outline-secondary btn-sm" onclick="window.close()">닫기</button>
      </div>

      <table border="1" style="border-collapse:collapse; width:100%;">
        <thead>
          <tr style="background:#f3f5f7;">
            <th style="padding:8px;">출고번호(일자+번호)</th>
            <th style="padding:8px;">LOT/NO</th>
            <th style="padding:8px;">화주명</th>
            <th style="padding:8px;">품명</th>
            <th style="padding:8px;">사이즈</th>
            <th style="padding:8px;">제강사</th>
            <th style="padding:8px;">차량번호</th>
            <th style="padding:8px; text-align:right;">출고수량</th>
            <th style="padding:8px; text-align:right;">수불중량(t)</th>
          </tr>
        </thead>
        <tbody>
    `;

        groups.forEach(g => {
            // 출고번호 헤더행
            html += `
        <tr style="background:#eef6ff; font-weight:800;">
          <td style="padding:8px;">${esc(g.out_no)}</td>
          <td style="padding:8px;" colspan="8">LOT/NO 목록</td>
        </tr>
      `;

            g.items.forEach(it => {
                dayCnt += 1;
                daySumQty += num(it.out_qty);
                daySumWt += num(it.inout_wt);

                html += `
          <tr>
            <td style="padding:8px;">${esc(it.out_no)}</td>
            <td style="padding:8px; font-weight:700;">${esc(it.lot_no)}</td>
            <td style="padding:8px;">${esc(it.owner_name)}</td>
            <td style="padding:8px;">${esc(it.item_name)}</td>
            <td style="padding:8px;">${esc(it.size)}</td>
            <td style="padding:8px;">${esc(it.maker)}</td>
            <td style="padding:8px;">${esc(it.car_no)}</td>
            <td style="padding:8px; text-align:right;">${fmt1(it.out_qty)}</td>
            <td style="padding:8px; text-align:right;">${fmt3(it.inout_wt)}</td>
          </tr>
        `;
            });

            // 출고번호 소계
            html += `
        <tr style="background:#fff7e6; font-weight:800;">
          <td style="padding:8px;">${esc(g.out_no)} 소계</td>
          <td style="padding:8px;" colspan="6"></td>
          <td style="padding:8px; text-align:right;">${fmt1(g.sum_qty)}</td>
          <td style="padding:8px; text-align:right;">${fmt3(g.sum_wt)}</td>
        </tr>
      `;
        });

        // 일일 전체 합계 + 행수 표시
        html += `
        <tr style="background:#f0fdf4; font-weight:900;">
          <td style="padding:8px;">일일합계</td>
          <td style="padding:8px;" colspan="6">총 ${dayCnt} 건</td>
          <td style="padding:8px; text-align:right;">${fmt1(daySumQty)}</td>
          <td style="padding:8px; text-align:right;">${fmt3(daySumWt)}</td>
        </tr>
      </tbody>
      </table>
    `;
        return html;
    }

    function openPopup(html) {
        const w = window.open("", "out_single_table",
            "width=1400,height=850,scrollbars=yes,resizable=yes");
        if (!w) { alert("⚠️ 팝업 차단 해제 후 다시"); return; }

        w.document.open();
        w.document.write(`
    <html>
    <head>
      <meta charset="utf-8" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
      <title>출고 리스트</title>
      <style>
        body { font-family: Arial, sans-serif; margin:16px; }
        table { font-size:14px; }
        th, td { border:1px solid #999; }
      </style>
      <script>
        function all_out_save() {
                // ✅ confirm은 팝업에서(사용자 클릭한 창이라 차단 덜함)
                const rows = window.opener?.__OUT_ROWS || [];
                if (!rows.length) { alert("저장할 데이터가 없습니다."); return; }
                if (!confirm(rows.length + "건 저장할까요?")) return;

                // ✅ 부모창 함수 호출(저장 실행)
                if (window.opener && typeof window.opener.go_save === "function") {
                window.opener.go_save(rows);
                window.close();
                } else {
                alert("부모창 go_save 함수가 없습니다.");
                }
            }
      </script>
    </head>
    <body>
      ${html}
    </body>
    </html>
  `);
        w.document.close();
        w.focus();
    }


    // ---------- click ----------
    $(document).on("click", "#btnParse_view", function (e) {
        e.preventDefault();

        const raw = $("#bulkText").val();
        const workDate = $("#work_date").val();

        if (!raw || raw.trim() === "") {
            alert("엑셀에서 복사한 내용을 붙여넣어주세요.");
            return;
        }

        const rows = parseOutBulkText(raw);
        if (!rows.length) return;

        window.__OUT_ROWS = rows;   // ✅✅✅ 이 줄이 핵심 (부모창 전역에 저장)

        const groups = buildOutNoGroups(rows);
        const html = renderSingleTable(groups, workDate);
        openPopup(html);
    });

    console.log("✅ out_bulk(single-table) loaded");
})();



window.all_out_save = function () {
    const rows = [];

    document.querySelectorAll("table tbody tr").forEach(tr => {
        const tds = tr.querySelectorAll("td");

        // 소계/합계 행은 제외
        if (tr.innerText.includes("소계") || tr.innerText.includes("일일합계")) return;

        const row = {
            out_no: tds[0]?.innerText.trim(),
            lot_no: tds[1]?.innerText.trim(),
            owner_name: tds[2]?.innerText.trim(),
            item_name: tds[3]?.innerText.trim(),
            size: tds[4]?.innerText.trim(),
            maker: tds[5]?.innerText.trim(),
            car_no: tds[6]?.innerText.trim(),
            out_qty: Number(tds[7]?.innerText.trim() || 0),
            inout_wt: Number(tds[8]?.innerText.trim() || 0),
        };

        if (row.out_no && row.lot_no) rows.push(row);
    });

    if (!rows.length) {
        alert("저장할 데이터가 없습니다.");
        return;
    }

    if (!confirm(rows.length + "건 저장할까요?")) return;

    fetch("/out_bulk_save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rows })
    })
        .then(r => r.json())
        .then(d => {
            if (d.result === "ok") {
                alert("저장 완료");
                if (window.opener) window.opener.location.reload();
                window.close();
            } else {
                alert("저장 실패: " + (d.msg || ""));
            }
        })
        .catch(err => {
            console.error(err);
            alert("서버 오류");
        });
};

// 1) 파싱 끝나고 rows 만들었을 때 (btnParse_view 클릭 안쪽)
// window.__OUT_ROWS = rows;   // ✅ 전역에 저장 (부모창)

// ✅ 부모창(메인)에 저장 함수 전역으로
// ✅ 부모창 전역
window.go_save = function (rows) {
    if (!rows || !rows.length) return alert("저장할 데이터가 없습니다.");

    fetch("/out_bulk_save", {          // ✅ 여기! 서버에 실제 있는 엔드포인트로
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rows })
    })
        .then(async (r) => {
            // 혹시 서버가 에러페이지(HTML) 주면 여기서 잡힘
            const ct = r.headers.get("content-type") || "";
            const data = ct.includes("application/json") ? await r.json() : { result: "fail", msg: await r.text() };
            return data;
        })
        .then(d => {
            if (d.result === "ok") {
                alert("저장 완료");
                window.close()
            } else {
                alert("저장 실패: " + (d.msg || ""));
            }
        })
        .catch(err => {
            console.error(err);
            alert("서버 오류");
        });
};

