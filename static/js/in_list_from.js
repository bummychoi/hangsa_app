$(document).on("change", "#fileUploadBtn", function () {
  if (!this.files || !this.files.length) return;

  const file = this.files[0];
  const name = file.name.toLowerCase();

  if (!name.endsWith(".xlsx")) {
    alert("⚠️ .xlsx 파일만 업로드 가능합니다.\n(.xls 파일은 Excel에서 저장 후 다시 올려주세요)");
    this.value = "";
    $("#bulkFileName").text("선택된 파일 없음");
    return;
  }

  $("#bulkFileName").text(file.name);
});

