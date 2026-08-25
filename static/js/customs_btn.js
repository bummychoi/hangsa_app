/*
 * 저장내역 행 클릭
 */
document.addEventListener("click", function (e) {
  const tr = e.target.closest(".customs-history-row");

  if (!tr) return;

  openCustomsModal(tr);
});


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


/*
 * 기존 저장내역 수정
 */
function openCustomsModal(row) {
  if (!customsModal || !customsInputForm) {
    console.error("수입신고 모달 또는 입력폼을 찾을 수 없습니다.");
    return;
  }

  modalTitle.textContent = "수입신고 수정";

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
    row.dataset.warehouse || "동방북항보세창고";

  remarkInput.value =
    row.dataset.remark || "";

  customsModal.classList.add("show");

  setTimeout(function () {
    declarationDateInput.focus();
    declarationDateInput.select();
  }, 50);
}


/*
 * 신규 등록
 */
function openNewCustomsModal() {
  if (!customsModal || !customsInputForm) {
    console.error("수입신고 모달 또는 입력폼을 찾을 수 없습니다.");
    return;
  }

  /*
   * reset 전에 HTML에 들어 있던 기본값 보관
   */
  const cargoNo =
    cargoNoInput.defaultValue || cargoNoInput.value;

  const today =
    declarationDateInput.defaultValue ||
    declarationDateInput.value;

  customsInputForm.reset();

  modalTitle.textContent = "수입신고 등록";

  customsIdInput.value = "";

  /*
   * 외부 JS에서는 Jinja를 사용하지 않고
   * HTML input의 기본값을 이용한다.
   */
  cargoNoInput.value = cargoNo;
  declarationDateInput.value = today;

  declarationNoInput.value = "";
  customsQtyInput.value = "";
  customsQtyUnitInput.value = "GT";
  customsWeightKgInput.value = "";
  customsWeightMtInput.value = "0.000";
  warehouseNameInput.value = "동방북항보세창고";
  remarkInput.value = "";

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
  if (!customsModal) return;

  customsModal.classList.remove("show");
}


/*
 * 중량 입력값
 */
function formatInputNumber(value) {
  if (value === undefined || value === null || value === "") {
    return "";
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "";
  }

  return number.toFixed(3);
}


/*
 * 톤수 소수점 3자리
 */
function formatMt(value) {
  const number = Number(value || 0);

  if (!Number.isFinite(number)) {
    return "0.000";
  }

  return number.toFixed(3);
}


/*
 * kg 입력 시 M/T 자동 계산
 */
if (customsWeightKgInput && customsWeightMtInput) {
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
}


/*
 * 모달 바깥 영역 클릭 시 닫기
 */
if (customsModal) {
  customsModal.addEventListener(
    "click",
    function (event) {
      if (event.target === customsModal) {
        closeCustomsModal();
      }
    }
  );
}


/*
 * ESC 키로 모달 닫기
 */
document.addEventListener(
  "keydown",
  function (event) {
    if (
      customsModal &&
      event.key === "Escape" &&
      customsModal.classList.contains("show")
    ) {
      closeCustomsModal();
    }
  }
);