document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("search_date");
    if (!input) return;

    if (input.dataset.all === "1") return; // ✅ 전체조회면 기본값 세팅 안함
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