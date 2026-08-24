function ex_read() {
    const table = document.getElementById("customsTable");

    if (!table) {
        alert("내려받을 표를 찾을 수 없습니다.");
        return;
    }

    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, "0");
    const day = String(today.getDate()).padStart(2, "0");

    const fileName = `${year}-${month}-${day}_세관조회.xlsx`;

    const workbook = XLSX.utils.table_to_book(table, {
        sheet: "세관조회"
    });

    XLSX.writeFile(workbook, fileName);
}


function customsSelect(selectElement) {
    const selectedValue = selectElement.value;
    const cargoNo = String(
        selectElement.dataset.cargo || ""
    ).trim();

    if (selectedValue !== "입력") {
        return;
    }

    if (!cargoNo) {
        alert("화물관리번호가 없습니다.");
        selectElement.value = "";
        return;
    }

    window.open(
        `/customs/input?cargo_no=${encodeURIComponent(cargoNo)}`,
        "customsInput",
        "width=700,height=720"
    );

    // 팝업을 연 다음 선택값 초기화
    selectElement.value = "";
}


const customsForm = document.getElementById("customsInputForm");

customsForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const saveButton = document.querySelector(".save-button");
    const formData = new FormData(customsForm);

    if (!confirm("수입신고 내용을 저장하시겠습니까?")) {
        return;
    }

    saveButton.disabled = true;
    saveButton.textContent = "저장 중...";

    try {
        const response = await fetch("/customs/save", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.message);
        }

        alert(result.message);

        if (window.opener && !window.opener.closed) {
            window.opener.location.reload();
        }

        window.close();

    } catch (error) {
        alert(error.message || "저장 중 오류가 발생했습니다.");

        saveButton.disabled = false;
        saveButton.textContent = "저장";
    }
});