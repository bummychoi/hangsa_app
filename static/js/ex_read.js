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
    const cargoNo = selectElement.dataset.cargo;

    if (selectedValue === "입력") {
        window.open(
            `/customs/input?cargo_no=${encodeURIComponent(cargoNo)}`,
            "customsInput",
            "width=700,height=600"
        );

        // 팝업을 열고 선택값 초기화
        selectElement.value = "";
        return;
    }

    // 미통관·부분통관·통관 상태 저장
    if (selectedValue) {
        saveCustomsStatus(cargoNo, selectedValue);
    }
}