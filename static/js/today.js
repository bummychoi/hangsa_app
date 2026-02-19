document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("search_date");
    if (!input) return;

    // 서버에서 값이 내려오면 그대로 사용
    if (input.value) return;

    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    input.value = `${yyyy}-${mm}-${dd}`;
});

let sortDirections = {};

function sortTable(th, colIndex) {
    const table = document.querySelector("table");
    const tbody = table.querySelector("tbody");
    const rows = Array.from(tbody.querySelectorAll("tr"));

    // 기존 화살표 제거
    document.querySelectorAll(".sort-arrow").forEach(el => el.remove());

    // 방향 토글
    sortDirections[colIndex] = !sortDirections[colIndex];
    const asc = sortDirections[colIndex];

    rows.sort((a, b) => {
        let A = a.children[colIndex].innerText.trim();
        let B = b.children[colIndex].innerText.trim();

        let numA = parseFloat(A.replace(/,/g, ""));
        let numB = parseFloat(B.replace(/,/g, ""));

        if (!isNaN(numA) && !isNaN(numB)) {
            return asc ? numA - numB : numB - numA;
        }

        return asc ? A.localeCompare(B, 'ko') : B.localeCompare(A, 'ko');
    });

    rows.forEach(row => tbody.appendChild(row));

    // 화살표 생성
    const arrow = document.createElement("span");
    arrow.classList.add("sort-arrow");
    arrow.classList.add(asc ? "sort-up" : "sort-down");
    arrow.textContent = asc ? "▲" : "▼";

    th.appendChild(arrow);
}

function searchData() {
    const form = document.querySelector(".search_form");
    const kw = document.getElementById("search_keyword");
    if (!kw.value.trim()) {
        alert("검색어를 입력하세요.");
        kw.focus();
        return;
    }

    // ✅ hidden input으로 all=1 추가 (날짜필터 끄기)
    let hidden = form.querySelector('input[name="all"]');
    if (!hidden) {
        hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = "all";
        form.appendChild(hidden);
    }
    hidden.value = "1";

    form.submit();
}

document.getElementById("btn_query")?.addEventListener("click", () => {
  const kw = document.getElementById("search_keyword");
  if (kw) kw.value = "";   // ✅ 조회는 날짜만 보게
});

document.addEventListener("DOMContentLoaded", function () {

  const queryBtn = document.getElementById("btn_query");
  const keywordInput = document.getElementById("search_keyword");

  if (queryBtn && keywordInput) {
    queryBtn.addEventListener("click", function () {
      keywordInput.value = "";   // ✅ 조회 클릭시 검색어 초기화
    });
  }

});



document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn_filter");
  const btnClear = document.getElementById("btn_clear");
  const sel = document.getElementById("search_type");
  const kw = document.getElementById("search_keyword");

  if (!btn || !sel || !kw) return; // 페이지에 없으면 종료

  btn.addEventListener("click", () => applyFilter());
  kw.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      applyFilter();
    }
  });

  if (btnClear) {
    btnClear.addEventListener("click", () => {
      kw.value = "";
      applyFilter(); // 전체 보이기
    });
  }

  function applyFilter() {
    const keyword = kw.value.trim().toLowerCase();
    const type = sel.value; // 예: lot_no, owner_name ...

    const tbody = document.querySelector(".out-table tbody");
    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll("tr"));

    let sumIn = 0, sumOut = 0, sumStock = 0;

    rows.forEach(tr => {
      const cells = tr.querySelectorAll("td");
      if (!cells.length) return;

      // ✅ 컬럼 인덱스 (네 테이블 순서 기준)
      const colMap = {
        lot_no: 1,      // LOT_NO
        owner_name: 2,  // 화주명
        steel_type: 3,  // 강종
        size: 4,        // 사이즈
        maker: 5,       // 제강사
      };

      const textAll = tr.innerText.toLowerCase();
      const idx = colMap[type];

      const targetText = (type === "all" || idx === undefined)
        ? textAll
        : (cells[idx]?.innerText || "").toLowerCase();

      const matched = keyword === "" ? true : targetText.includes(keyword);

      tr.style.display = matched ? "" : "none";

      // ✅ 보이는 행 기준 합계 다시 계산
      if (matched) {
        const inQty = parseNum(cells[6]?.innerText);    // 입고수량
        const outSum = parseNum(cells[7]?.innerText);   // 출고합계
        const stock = parseNum(cells[8]?.innerText);    // 재고
        sumIn += inQty;
        sumOut += outSum;
        sumStock += stock;
      }
    });

    // ✅ 합계 박스 업데이트 (id는 네가 맞춰줘)
    // 예: <span id="sum_in">...</span>
    setText("sum_in", sumIn);
    setText("sum_out", sumOut);
    setText("sum_stock", sumStock);
  }

  function parseNum(s) {
    if (!s) return 0;
    const v = parseFloat(String(s).replace(/,/g, "").trim());
    return isNaN(v) ? 0 : v;
  }

  function setText(id, num) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = num.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  }
});
