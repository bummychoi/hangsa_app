/* =========================
   script.js (정리본)
   - 핵심 수정: selectedLot 중복 선언 제거(전역 1개로 통일)
   - 중복 함수(escapeHtml/toNum/bulkUploadToServer/bulkClosePopup) 1번만 유지
   ========================= */

(function () {
  // ✅ 전역 상태(중복 선언 방지)
  window.selectedLot = window.selectedLot ?? null;
  window.__OUT_ROWS = window.__OUT_ROWS ?? [];
  window.__bulkPreview = window.__bulkPreview ?? null;

  // =======================
  // 공통 유틸
  // =======================
  function escapeHtml(s) {
    return String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function toNum(v) {
    if (v === null || v === undefined) return 0;
    if (typeof v === "number") return v;
    const s = String(v).trim().replaceAll(",", "");
    const n = parseFloat(s);
    return isNaN(n) ? 0 : n;
  }

  // =======================
  // 상단 날짜/메뉴 등(기존)
  // =======================
  $(function () {
    const today = new Date();
    const y = today.getFullYear();
    const m = String(today.getMonth() + 1).padStart(2, "0");
    const d = String(today.getDate()).padStart(2, "0");
    const h = today.getHours();

    const shift =
      h >= 5 && h < 18
        ? "<span style='color:blue'>주간</span>"
        : "<span style='color:red'>야간</span>";

    $("#today").html(`${y}년 ${m}월 ${d}일 : ${shift}`);

    $("nav >ul >li").mouseenter(function () {
      $(this).children(".sub").stop().slideDown();
    });
    $("nav > ul >li").mouseleave(function () {
      $(".sub").stop().slideUp();
    });

    // ✅ 재고 테이블 더블클릭 → 상세 모달
    $("table tbody").on("dblclick", "tr", function () {
      const $td = $(this).children("td");

      // ✅ 헤더: 순번(0) LOT(1) ...
      window.selectedLot = $td.eq(1).text().trim();

      if (!window.selectedLot) {
        alert("LOT/NO를 읽지 못했습니다.");
        return;
      }

      $("#lotText").text(`${window.selectedLot} 선택`);
      $("#lotModal").fadeIn(150);

      fetch(`/search?id=${encodeURIComponent(window.selectedLot)}`)
        .then((res) => res.json())
        .then((data) => {
          window.selectedLot = (data.lot_no || "").trim();

          $("#f_lot_no").val(window.selectedLot);
          $("#f_vessel_name").val(data.vessel_name || "");
          $("#f_owner_name").val(data.owner_name || "");
          $("#f_cargo_no").val(data.cargo_no || "");
          $("#f_bl_no").val(data.bl_no || "");
          $("#f_cargo_type").val(data.cargo_type || "");
          $("#f_maker").val(data.maker || "");
          $("#f_steel_type").val(data.steel_type || "");
          $("#f_size").val(data.size || "");
          $("#f_bundle_qty").val(data.bundle_qty ?? "");
          $("#f_mt_weight").val(data.mt_weight ?? "");

          $("#lotText").text(`${window.selectedLot} 선택`);
        })
        .catch((err) => {
          console.error("fetch error", err);
          alert("데이터 조회 실패");
        });
    });
  });

  // =======================
  // 모달 열기/닫기
  // =======================
  window.in_btn = function () {
    $("#input_tb").hide();
    $("#inModal").fadeIn(200, function () {
      $("#inModal input[name='lot_no']").focus();
    });
  };
  window.in_btn2 = function () {
    window.in_btn();
  };

  $(document).on("click", "#btnCancel", function () {
    $("#lotModal, #inModal").fadeOut(150);
  });

  $(document).on("keydown", function (e) {
    if (e.key === "Escape") $("#lotModal, #inModal").fadeOut(150);
  });

  window.close_in_btn = function () {
    $("#lotModal, #inModal").fadeOut(150);
  };

  // =======================
  // 입고 수정/삭제
  // =======================
  $(document).on("click", "#btnUpdate", function () {
    const payload = {
      lot_no: $("#f_lot_no").val(),
      vessel_name: $("#f_vessel_name").val(),
      cargo_no: $("#f_cargo_no").val(),
      cargo_type: $("#f_cargo_type").val(),
      bl_no: $("#f_bl_no").val(),
      owner_name: $("#f_owner_name").val(),
      size: $("#f_size").val(),
      bundle_qty: $("#f_bundle_qty").val(),
      mt_weight: $("#f_mt_weight").val(),
      maker: $("#f_maker").val(),
      steel_type: $("#f_steel_type").val(),
    };

    fetch("/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.result === "ok") {
          alert("수정 완료");
          $("#lotModal").fadeOut(150);
          location.reload();
        } else {
          alert("수정 실패");
        }
      })
      .catch((err) => {
        console.error(err);
        alert("서버 오류");
      });
  });

  $(document).on("click", "#btnDelete", function () {
    window.selectedLot = $("#f_lot_no").val();

    if (!window.selectedLot) {
      alert("LOT/NO가 없습니다.");
      return;
    }

    if (!confirm(`LOT ${window.selectedLot}을 삭제하시겠습니까?`)) return;

    fetch("/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lot_no: window.selectedLot }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.result === "ok") {
          alert("삭제 완료");
          $("#lotModal").fadeOut(150);
          location.reload();
        } else {
          alert("삭제 실패");
        }
      })
      .catch((err) => {
        console.error("delete error", err);
        alert("서버 오류");
      });
  });

  // =======================
  // 출고 폼(단건 저장)
  // =======================
  window.openOutForm = function (url) {
    const popupWidth = 1000;
    const popupHeight = 700;
    const left = Math.floor((window.screen.width - popupWidth) / 2);
    const top = Math.floor((window.screen.height - popupHeight) / 2);

    window.open(
      url,
      "outFormPopup",
      `width=${popupWidth},height=${popupHeight},left=${left},top=${top},scrollbars=yes,resizable=yes`
    );
  };

  window.save_out = function (btn) {
    const $tr = $(btn).closest("tr");
    const lotNo = $tr.find("input[name='lot_no']").val();
    const carNo = $tr.find("input[name='car_no']").val();
    const outQty = Number($tr.find("input[name='out_qty']").val());
    const outNo = $tr.find("input[name='out_no']").val();

    const payload = { lot_no: lotNo, car_no: carNo, out_qty: outQty, out_no: outNo };

    fetch("/out_d_save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.result === "ok") {
          alert("출고 저장 완료");
          if (window.opener) window.opener.location.reload();
          window.close();
          location.href = "/out_d_bar#out_list";
        } else {
          alert("저장 실패: " + (data.msg || ""));
        }
      })
      .catch((err) => {
        console.error(err);
        alert("서버 오류");
      });
  };

  window.cancel_out = function () {
    if (confirm("출고 입력을 취소하시겠습니까?")) location.href = "/out_d_bar#out_list";
  };

  // =======================
  // 선택출고 버튼(기존)
  // =======================
  let selectedLots_out = [];
  function updateSelectedCount() {
    selectedLots_out = [];
    $(".chk-lot:checked").each(function () {
      selectedLots_out.push($(this).data("lot"));
    });

    $("#btnOut")
      .text(`선택출고 (${selectedLots_out.length})`)
      .prop("disabled", selectedLots_out.length === 0);
  }

  $(document).on("change", ".chk-lot", updateSelectedCount);
  updateSelectedCount();

  $(document).on("click", "#btnOut", function (e) {
    e.preventDefault();

    if (selectedLots_out.length === 0) return alert("출고 선택하세요!!");

    const params = selectedLots_out.map((lot) => `lot_no=${encodeURIComponent(lot)}`).join("&");

    if (selectedLots_out.length === 1) {
      location.href = `/out_form?${params}`;
    } else {
      location.href = `/out_list?${params}`;
    }
  });

  // =======================
  // 출고 다건 저장(기존 all_save_out)
  // =======================
  window.all_save_out = function () {
    const rows = [];
    let invalid = false;

    $(".out-table tbody tr").each(function () {
      const $tr = $(this);
      const lotNo = $tr.find("input[name='lot_no']").val();
      const outNo = $tr.find("input[name='out_no']").val().trim();
      const carNo = $tr.find("input[name='car_no']").val().trim();
      const outQty = Number($tr.find("input[name='out_qty']").val());

      if (!lotNo || !outNo || !carNo || !outQty || outQty <= 0) {
        invalid = true;
        $tr.addClass("row-error");
        return;
      }

      rows.push({ lot_no: lotNo, out_no: outNo, car_no: carNo, out_qty: outQty });
    });

    if (invalid) return alert("빈칸(출고번호/차량번호/수량)을 모두 입력하세요.");
    if (!confirm(`${rows.length}건을 일괄 저장할까요?`)) return;

    fetch("/out_d_save_bulk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rows }),
    })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw data;
        return data;
      })
      .then(() => {
        alert("일괄 저장 완료");
        location.href = "/out_d_bar#out_list";
      })
      .catch((err) => {
        if (err && err.errors) {
          alert("일부 실패:\n" + err.errors.map((e) => `${e.lot_no} : ${e.msg}`).join("\n"));
        } else {
          alert("저장 실패: " + (err.msg || "서버 오류"));
        }
        console.error(err);
      });
  };

  // =======================
  // 일괄 적용(출고번호/차량번호)
  // =======================
  window.apply_bulk = function () {
    const outNo = $("#bulk_out_no").val().trim();
    const carNo = $("#bulk_car_no").val().trim();
    if (outNo) $("input[name='out_no']").val(outNo);
    if (carNo) $("input[name='car_no']").val(carNo);
  };

  // =======================
  // 입고 팝업(기존)
  // =======================
  window.openInPopup = function () {
    const width = 1100;
    const height = 1000;
    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;

    window.open(
      "/in_form",
      "in_form_popup",
      `width=${width},height=${height},left=${left},top=${top},scrollbars=yes`
    );
  };

  // =======================
  // 리스트 팝업(기존)
  // =======================
  window.openCenteredPopup = function (url) {
    const w = 1400;
    const h = 900;

    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const today = `${yyyy}-${mm}-${dd}`;

    const finalUrl = url.includes("?") ? `${url}&date=${today}` : `${url}?date=${today}`;

    const screenX = window.screenX ?? window.screenLeft;
    const screenY = window.screenY ?? window.screenTop;
    const outerW = window.outerWidth || document.documentElement.clientWidth;
    const outerH = window.outerHeight || document.documentElement.clientHeight;

    const left = screenX + Math.max(0, (outerW - w) / 2);
    const top = screenY + Math.max(0, (outerH - h) / 2);

    const opt = `width=${w},height=${h},left=${Math.round(left)},top=${Math.round(top)},scrollbars=yes,resizable=yes`;
    const pop = window.open(finalUrl, "outListPopup", opt);
    if (pop) pop.focus();
  };

  window.goDate = function () {
    const d = document.getElementById("datePicker").value;
    if (!d) return alert("날짜 선택!");
    location.href = "/out_d_bar_lists?date=" + encodeURIComponent(d);
  };

  // =======================
  // out_d_bar_lists 행 그룹 색상/더블클릭
  // =======================
  document.addEventListener("DOMContentLoaded", () => {
    const rows = Array.from(document.querySelectorAll("tr.out-row"));
    let prev = null;
    let groupIndex = 0;

    for (let i = 0; i < rows.length; i++) {
      const outno = rows[i].dataset.outno;
      if (outno !== prev) {
        groupIndex++;
        rows[i].classList.add("group-start");
        prev = outno;
      }
      rows[i].dataset.group = groupIndex;
      rows[i].classList.add(groupIndex % 2 === 0 ? "g-even" : "g-odd");
    }

    rows.forEach((tr) => {
      tr.addEventListener("dblclick", () => {
        const outno = tr.dataset.outno;
        location.href = `/out_edit?out_no=${encodeURIComponent(outno)}`;
      });
    });
  });

  // =======================
  // out_edit 저장/삭제(기존)
  // =======================
  window.saveEdit = function () {
    const outNo = document.getElementById("out_no").innerText.trim();
    const rows = Array.from(document.querySelectorAll("tbody tr[data-id]")).map((tr) => ({
      id: tr.dataset.id,
      car_no: tr.querySelector(".car_no").value.trim(),
      out_qty: Number(tr.querySelector(".out_qty").value),
    }));

    fetch("/out_edit_save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ out_no: outNo, rows }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.result === "ok") {
          alert("수정 완료");
          if (window.opener) window.opener.location.reload();
          window.close();
        } else {
          alert("수정 실패");
        }
      })
      .catch((e) => {
        console.error(e);
        alert("서버 오류");
      });
  };

  window.deleteOut = function () {
    const outNo = document.getElementById("out_no").innerText.trim();
    if (!confirm(outNo + " 전체 삭제?")) return;

    fetch("/out_edit_delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ out_no: outNo }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.result === "ok") {
          alert("삭제 완료");
          if (window.opener) window.opener.location.reload();
          window.close();
        } else {
          alert("삭제 실패");
        }
      })
      .catch((e) => {
        console.error(e);
        alert("서버 오류");
      });
  };

  // =======================
  // out_d_bar_lists 수정/삭제(기존)
  // =======================
  $(document).on("click", "#out_btnUpdate", function () {
    update_rows();
  });

  function update_rows() {
    if (!confirm("수정합니까?")) return;
    const date = $("#work_date").val();

    let rows = [];
    let hasError = false;
    let errorMsg = "";

    $("tbody tr").each(function () {
      const id = $(this).data("id");
      const car_no_raw = $(this).find(".car_no").val();
      const out_qty_raw = $(this).find(".out_qty").val();

      const car_no = (car_no_raw || "").trim();
      const out_qty = parseFloat(out_qty_raw);

      if (car_no.length < 4) {
        hasError = true;
        errorMsg = `ID ${id} : 차량번호는 4자리 이상 입력하세요.`;
        $(this).find(".car_no").focus();
        return false;
      }

      if (isNaN(out_qty) || out_qty <= 0) {
        hasError = true;
        errorMsg = `ID ${id} : 출고수량은 0보다 커야 합니다.`;
        $(this).find(".out_qty").focus();
        return false;
      }

      rows.push({ id, car_no, out_qty });
    });

    if (hasError) return alert(errorMsg);

    $.ajax({
      url: "/out_d_bar_lists_Update",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({ rows }),
      success: function (res) {
        alert(`수정완료(${res.updated}건)`);
        location.href = `/out_d_bar_lists?date=${date}`;
      },
      error: function (xhr) {
        console.log("ERROR:", xhr.status, xhr.responseText);
        alert("수정실패");
        location.href = `/out_d_bar_lists?date=${date}`;
      },
    });
  }

  $(document).on("click", "#out_btnDelete", function () {
    delete_rows();
  });

  function delete_rows() {
    if (!confirm("정말 삭제합니까?")) return;

    const out_no = $("#out_no").val();
    const date = $("#work_date").val();

    if (!out_no) return alert("out_no 값이 없습니다. (#out_no 확인)");

    $.ajax({
      url: "/out_delete_by_outno",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({ out_no }),
      success: function (res) {
        alert(`삭제완료(${res.deleted}건)`);
        location.href = `/out_d_bar_lists?date=${date}`;
      },
      error: function (xhr) {
        console.log("삭제 ERROR:", xhr.status, xhr.responseText);
        alert("삭제실패");
      },
    });
  }

  // =======================
  // 파일명 표시(.xlsx)
  // =======================
  $(document).on("change", "#bulkFile", function () {
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

  // ✅ 입고업로드 버튼: 엑셀 파싱 → __bulkPreview 세팅 → 미리보기 팝업 열기
  $(document).on("click", "#fileUploadBtn", function () {
    const input = document.getElementById("bulkFile");

    if (!input || !input.files || !input.files.length) {
      alert("엑셀 파일을 먼저 선택하세요.");
      return;
    }

    if (typeof XLSX === "undefined") {
      alert("XLSX 라이브러리가 없습니다. (xlsx.full.min.js 로드 확인)");
      return;
    }

    const file = input.files[0];
    const reader = new FileReader();

    reader.onload = function (e) {
      try {
        const data = new Uint8Array(e.target.result);
        const wb = XLSX.read(data, { type: "array" });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const body = XLSX.utils.sheet_to_json(ws, { defval: "" });

        if (!body.length) {
          alert("엑셀 데이터가 비어있습니다.");
          return;
        }

        const headers = Object.keys(body[0] || {});

        // ✅ 서버 합계 검증 통과하려면 totalQty/totalWeight 계산 필요
        const norm = (h) => String(h || "").replace(/\s+/g, "").replace(/\//g, "").toUpperCase();
        const normHeaders = headers.map(norm);

        const findIdx = (cands) => {
          for (const c of cands) {
            const key = norm(c);
            const idx = normHeaders.indexOf(key);
            if (idx >= 0) return idx;
          }
          return -1;
        };

        const idx_qty = findIdx(["재고수량", "수량"]);
        const idx_wt = findIdx(["재고중량", "중량"]);

        const toNum = (v) => {
          const n = parseFloat(String(v ?? "").replace(/,/g, "").trim());
          return isNaN(n) ? 0 : n;
        };

        let totalQty = 0;
        let totalWeight = 0;

        // sheet_to_json이 객체배열이라 index 계산 위해 배열화
        body.forEach((obj) => {
          const arr = headers.map((h) => obj[h]);
          if (idx_qty >= 0) totalQty += toNum(arr[idx_qty]);
          if (idx_wt >= 0) totalWeight += toNum(arr[idx_wt]);
        });

        totalWeight = Math.round(totalWeight * 1000) / 1000;

        window.__bulkPreview = { headers, body, totalQty, totalWeight };

        // ✅ 미리보기 창 열기 (이 창이 bulkResult 이름을 써야 bulkClosePopup이 닫음)
        const w = 1100, h = 900;
        const left = Math.floor((window.screen.width - w) / 2);
        const top = Math.floor((window.screen.height - h) / 2);
        window.open("/in_bulk_preview", "bulkResult",
          `width=${w},height=${h},left=${left},top=${top},scrollbars=yes,resizable=yes`
        );

      } catch (err) {
        console.error(err);
        alert("엑셀 파싱 실패: " + err.message);
      }
    };

    reader.readAsArrayBuffer(file);
  });





  // =======================
  // out_bulk_form 팝업 열기 버튼
  // =======================
  $(document).on("click", "#lists_btnOut", function () {
    const w = 1200;
    const h = 700;

    const screenX = window.screenX ?? window.screenLeft;
    const screenY = window.screenY ?? window.screenTop;

    const outerW = window.outerWidth || document.documentElement.clientWidth;
    const outerH = window.outerHeight || document.documentElement.clientHeight;

    const left = screenX + Math.max(0, (outerW - w) / 2);
    const top = screenY + Math.max(0, (outerH - h) / 2);

    const opt = `width=${w},height=${h},left=${Math.round(left)},top=${Math.round(top)},scrollbars=yes,resizable=yes`;

    const pop = window.open("/out_bulk_form", "outBulk", opt);
    if (pop) pop.focus();
  });

  $(document).on("click", "#fileUploadBtn", function () {
    window.bulkUploadToServer();
  });


  // work_date 기본값
  $(function () {
    if ($("#work_date").length && !$("#work_date").val()) {
      const d = new Date();
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, "0");
      const day = String(d.getDate()).padStart(2, "0");
      $("#work_date").val(`${y}-${m}-${day}`);
    }
  });

  // 차량번호 경고 숨김
  $(document).on("focus input", "input.car_no", function () {
    $(this).closest("td").find(".car-warning").hide();
  });
  $(document).on("click", ".car-warning", function () {
    $(this).hide();
  });

  console.log("✅ script.js loaded (clean)");
})();

$(document).on("click", "#btnParse_view", function () {
  const input = document.getElementById("bulkFile");
  if (!input.files || !input.files.length) {
    alert("엑셀 파일을 먼저 선택하세요.");
    return;
  }

  const file = input.files[0];
  const reader = new FileReader();

  reader.onload = function (e) {
    const data = new Uint8Array(e.target.result);
    const wb = XLSX.read(data, { type: "array" });
    const ws = wb.Sheets[wb.SheetNames[0]];

    const rows = XLSX.utils.sheet_to_json(ws, { defval: "" });

    const totalQty = 0;
    const totalWeight = 0;

    window.__bulkPreview = {
      headers: Object.keys(rows[0] || {}),
      body: rows,
      totalQty,
      totalWeight,
    };

    // ✅ 여기만 /in_up_list 로!
    window.open("/in_up_list", "bulkResult", "width=1100,height=900,scrollbars=yes");
  };

  reader.readAsArrayBuffer(file);
});
