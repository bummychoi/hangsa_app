document.addEventListener("DOMContentLoaded", function () {

  const customsModal =
    document.getElementById("customsModal");

  const customsInputForm =
    document.getElementById("customsInputForm");

  const modalTitle =
    document.getElementById("modalTitle");

  const customsIdInput =
    document.getElementById("customs_id");

  const cargoNoInput =
    document.getElementById("cargo_no");

  const declarationDateInput =
    document.getElementById("declaration_date");

  const declarationNoInput =
    document.getElementById("declaration_no");

  const customsQtyInput =
    document.getElementById("customs_qty");

  const customsQtyUnitInput =
    document.getElementById("customs_qty_unit");

  const customsWeightKgInput =
    document.getElementById("customs_weight_kg");

  const customsWeightMtInput =
    document.getElementById("customs_weight_mt");

  const warehouseNameInput =
    document.getElementById("warehouse_name");

  const remarkInput =
    document.getElementById("remark");

  const saveButton =
    document.getElementById("saveButton");

  const deleteButton =
    document.getElementById("deleteButton");


  /*
   * 필수 요소 확인
   */
  if (
    !customsModal ||
    !customsInputForm ||
    !saveButton ||
    !deleteButton
  ) {
    console.error(
      "수입신고 모달에 필요한 요소를 찾을 수 없습니다."
    );

    return;
  }


  /*
   * 기존 저장내역 수정 모달
   */
  function openCustomsModal(row) {

    modalTitle.textContent =
      "수입신고 수정";

    saveButton.textContent =
      "수정";

    deleteButton.hidden =
      false;

    customsIdInput.value =
      row.dataset.id || "";

    declarationDateInput.value =
      row.dataset.date || "";

    declarationNoInput.value =
      row.dataset.no || "";

    customsQtyInput.value =
      row.dataset.qty || "";

    customsQtyUnitInput.value =
      row.dataset.unit || "GT";

    customsWeightKgInput.value =
      formatInputNumber(row.dataset.weightKg);

    customsWeightMtInput.value =
      formatMt(row.dataset.weightMt);

    warehouseNameInput.value =
      row.dataset.warehouse ||
      "동방북항보세창고";

    remarkInput.value =
      row.dataset.remark || "";

    /*
     * 수정 저장 주소로 원상복구
     */
    customsInputForm.action =
      "/customs/save";

    customsModal.classList.add("show");

    setTimeout(function () {
      declarationDateInput.focus();
      declarationDateInput.select();
    }, 50);
  }


  /*
   * 신규 등록 모달
   */
  function openNewCustomsModal() {

    const cargoNo =
      cargoNoInput.defaultValue ||
      cargoNoInput.value;

    const today =
      declarationDateInput.defaultValue ||
      declarationDateInput.value;

    customsInputForm.reset();

    modalTitle.textContent =
      "수입신고 등록";

    saveButton.textContent =
      "저장";

    deleteButton.hidden =
      true;

    customsIdInput.value = "";

    cargoNoInput.value =
      cargoNo;

    declarationDateInput.value =
      today;

    declarationNoInput.value = "";
    customsQtyInput.value = "";
    customsQtyUnitInput.value = "GT";
    customsWeightKgInput.value = "";
    customsWeightMtInput.value = "0.000";

    warehouseNameInput.value =
      "동방북항보세창고";

    remarkInput.value = "";

    customsInputForm.action =
      "/customs/save";

    customsModal.classList.add("show");

    setTimeout(function () {
      declarationDateInput.focus();
      declarationDateInput.select();
    }, 50);
  }


  /*
   * 모달 닫기
   */
  function closeCustomsModal() {
    customsModal.classList.remove("show");
  }


  /*
   * 선택 자료 삭제
   */
  function deleteCustoms() {

    const customsId =
      customsIdInput.value;

    if (!customsId) {
      alert("삭제할 수입신고 자료가 없습니다.");
      return;
    }

    const declarationNo =
      declarationNoInput.value || "";

    const confirmed =
      confirm(
        `수입신고번호 ${declarationNo} 자료를 삭제하시겠습니까?`
      );

    if (!confirmed) {
      return;
    }

    customsInputForm.action =
      "/customs/delete";

    /*
     * required 검사 없이 삭제 요청
     */
    customsInputForm.submit();
  }


  /*
   * kg 입력값 표시
   */
  function formatInputNumber(value) {

    if (
      value === undefined ||
      value === null ||
      value === ""
    ) {
      return "";
    }

    const number =
      Number(value);

    if (!Number.isFinite(number)) {
      return "";
    }

    return number.toFixed(3);
  }


  /*
   * 톤수 표시
   */
  function formatMt(value) {

    const number =
      Number(value || 0);

    if (!Number.isFinite(number)) {
      return "0.000";
    }

    return number.toFixed(3);
  }


  /*
   * HTML onclick에서 사용
   */
  window.openCustomsModal =
    openCustomsModal;

  window.openNewCustomsModal =
    openNewCustomsModal;

  window.closeCustomsModal =
    closeCustomsModal;

  window.deleteCustoms =
    deleteCustoms;


  /*
   * 저장내역 행 클릭
   */
  document.addEventListener(
    "click",
    function (event) {

      const row =
        event.target.closest(".history-row");

      if (!row) return;

      openCustomsModal(row);
    }
  );


  /*
   * kg 입력 시 M/T 자동 계산
   */
  customsWeightKgInput.addEventListener(
    "input",
    function () {

      const weightKg =
        Number(this.value || 0);

      const weightMt =
        weightKg / 1000;

      customsWeightMtInput.value =
        weightMt.toFixed(3);
    }
  );


  /*
   * 모달 바깥 클릭 시 닫기
   */
  customsModal.addEventListener(
    "click",
    function (event) {

      if (event.target === customsModal) {
        closeCustomsModal();
      }
    }
  );


  /*
   * ESC 키로 닫기
   */
  document.addEventListener(
    "keydown",
    function (event) {

      if (
        event.key === "Escape" &&
        customsModal.classList.contains("show")
      ) {
        closeCustomsModal();
      }
    }
  );

});


function applyStatusStyle(select) {

  const status =
    (select.value || "").trim();

  select.style.color = "#fff";
  select.style.fontWeight = "bold";

  if (status === "미통관") {

    // 적색
    select.style.backgroundColor =
      "#e11d48";

  } else if (status === "부분통관") {

    // 노란색
    select.style.backgroundColor =
      "#f59e0b";

    select.style.color =
      "#222";

  } else if (status === "통관") {

    // 파란색
    select.style.backgroundColor =
      "#2563eb";

  } else {

    select.style.backgroundColor =
      "";

    select.style.color =
      "";

    select.style.fontWeight =
      "";
  }
}


/*
 * 선택 변경 시 색상 적용
 */
document.addEventListener(
  "change",
  function (event) {

    const select =
      event.target.closest(".customs-status");

    if (!select) return;

    applyStatusStyle(select);
  }
);


/*
 * 처음 화면이 열릴 때 색상 적용
 */
window.addEventListener(
  "DOMContentLoaded",
  function () {

    document
      .querySelectorAll(".customs-status")
      .forEach(applyStatusStyle);
  }
);