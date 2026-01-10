$(function () {
    const today = new Date();
    const y = today.getFullYear();
    const m = String(today.getMonth() + 1).padStart(2, "0");
    const d = String(today.getDate()).padStart(2, "0");

    const h = today.getHours();
    const min = String(today.getMinutes()).padStart(2, "0");
    const s = String(today.getSeconds()).padStart(2, "0");


    const shift = (h >= 5 && h < 18) ? "<span style='color:blue'>주간</span>" : "<span style='color:red'>야간</span>";

    const formatted = `${y}년 ${m}월 ${d}일 : ${shift}`;
    $("#today").html(formatted);

    $("nav >ul >li").mouseenter(function () {
        $(this).children(".sub").stop().slideDown();
    })
    $("nav > ul >li").mouseleave(function () {
        $(".sub").stop().slideUp();
    })



    let selectedLot = null;

    $("table tbody").on("dblclick", "tr", function () {
        selectedLot = $(this).data('lot') || this.id;
        $("#lotText").text(`${selectedLot} 선택`);
        $("#lotModal").fadeIn(150);
        const url = `/search?id=${encodeURIComponent(selectedLot)}`;
        fetch(url).then(res => res.json()).then(data => {
            // console.log(data);
            $("#f_lot_no").val(data.lot_no);
            $("#f_vessel_name").val(data.vessel_name);
            $("#f_cargo_no").val(data.cargo_no);
            $("#f_cargo_type").val(data.cargo_type);
            $("#f_bl_no").val(data.bl_no);
            $("#f_owner_name").val(data.owner_name);
            $("#f_size").val(data.size);
            $("#f_bundle_qty").val(data.bundle_qty);
            $("#f_mt_weight").val(data.mt_weight);
            $("#f_maker").val(data.maker);
            $("#f_steel_type").val(data.steel_type);
            // f_date input이 실제로 있으면만 세팅
            if ($("#f_date").length && data.date) $("#f_date").val(data.date);

            $("#lotText").text(`${data.lot_no} 선택`);
        })

            .catch(err => {
                console.error("fetch error", err);
                // $("#lotText").text("조회 실패");
                // alert("데이터 조회 실패");
            });

    });
})

function in_btn() {
    $("#input_tb").hide();
    $("#inModal").fadeIn(200, function () {
        $("#inModal input[name='lot_no']").focus();
    });
}
function in_btn2() {
    in_btn();
}

$(document).on("click", "#btnCancel", function (e) {
    $("#lotModal, #inModal").fadeOut(150);
});


$(document).on("keydown", function (e) {
    if (e.key === "Escape") {
        $("#lotModal, #inModal").fadeOut(150);
    }
});
function close_in_btn() {
    $("#lotModal, #inModal").fadeOut(150);
}

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
        steel_type: $("#f_steel_type").val()
    };
    fetch("/update", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(data => {
            if (data.result === "ok") {
                alert("수정 완료");
                $("#lotModal").fadeOut(150);
                location.reload();   // 목록 갱신
            } else {
                alert("수정 실패");
            }
        })
        .catch(err => {
            console.error(err);
            alert("서버 오류");
        });
})

let selectedLot = null;

$(document).on("click", "#btnDelete", function () {
    selectedLot = $("#f_lot_no").val();
    if (!selectedLot) {
        alert(selectedLot)
        return;
    }
    if (!confirm(`LOT ${selectedLot}을 삭제하시겠습니까?`)) {
        return;
    }
    fetch("/delete", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            lot_no: selectedLot   // 🔥 핵심
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.result === "ok") {
                alert("삭제 완료");
                $("#lotModal").fadeOut(150);
                location.reload();   // 목록 갱신
            } else {
                alert("삭제 실패");
            }
        })
        .catch(err => {
            console.error("delete error", err);
            alert("서버 오류");
        });
})

// 출고 폼화면창
function openOutForm(url) {
    const popupWidth = 1000;
    const popupHeight = 700;

    const left = Math.floor((window.screen.width - popupWidth) / 2);
    const top = Math.floor((window.screen.height - popupHeight) / 2);

    window.open(
        url,
        "outFormPopup",
        `width=${popupWidth},
         height=${popupHeight},
         left=${left},
         top=${top},
         scrollbars=yes,
         resizable=yes`
    );
}

function save_out(btn) {
    const $tr = $(btn).closest("tr");

    const lotNo = $tr.find("input[name='lot_no']").val();
    const carNo = $tr.find("input[name='car_no']").val();
    const outQty = Number($tr.find("input[name='out_qty']").val());
    const outNo = $tr.find("input[name='out_no']").val();
    // alert(`LOT=${lotNo}\n차량=${carNo}\n수량=${outQty}`);
    const payload = {
        lot_no: lotNo,
        car_no: carNo,
        out_qty: outQty,
        out_no: outNo,
    }

    fetch("/out_d_save", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(data => {
            if (data.result === "ok") {
                alert("출고 저장 완료");
                // 팝업이면:
                if (window.opener) window.opener.location.reload();
                window.close();
                location.href = "/out_d_bar#out_list";
                // 팝업이 아니라면:
                // location.reload();
            } else {
                alert("저장 실패: " + (data.msg || ""));
            }
        })
        .catch(err => {
            console.error(err);
            alert("서버 오류");
        });
}

function cancel_out() {
    if (confirm("출고 입력을 취소하시겠습니까?")) {
        location.href = "/out_d_bar#out_list";
    }
}
//  재고 더블클릭시 출고창 or 선택버튼

// $("table tbody").on("dblclick", "tr", function () {

// })


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
    // alert("🔥 btnOut 클릭됨");

    if (selectedLots_out.length === 0) {
        alert("출고 선택하세요!!")
        return;
    }
    // 쿼리스트링 생성
    const params = selectedLots_out
        .map(lot => `lot_no=${encodeURIComponent(lot)}`)
        .join("&");

    if (selectedLots_out.length === 1) {
        alert("1개")
        // ✅ 1개 → 출고 입력
        location.href = `/out_form?${params}`;
    } else {
        alert("여러개")
        // 여러 개 → 출고 조회
        location.href = `/out_list?${params}`;
    }

});

function all_save_out() {
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
            $tr.addClass("row-error"); // 필요하면 CSS로 표시
            return;
        }

        rows.push({ lot_no: lotNo, out_no: outNo, car_no: carNo, out_qty: outQty });
    });

    if (invalid) {
        alert("빈칸(출고번호/차량번호/수량)을 모두 입력하세요.");
        return;
    }

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
            // err.errors 있으면 어떤 LOT가 실패했는지 보여줌
            if (err && err.errors) {
                alert("일부 실패:\n" + err.errors.map(e => `${e.lot_no} : ${e.msg}`).join("\n"));
            } else {
                alert("저장 실패: " + (err.msg || "서버 오류"));
            }
            console.error(err);
        });
}


function apply_bulk() {
    const outNo = $("#bulk_out_no").val().trim();
    const carNo = $("#bulk_car_no").val().trim();

    if (outNo) $("input[name='out_no']").val(outNo);
    if (carNo) $("input[name='car_no']").val(carNo);
}

function openInPopup() {
    const width = 1100;
    const height = 1000;

    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;

    window.open(
        "/in_form",
        "in_form_popup",
        `width=${width},height=${height},left=${left},top=${top},scrollbars=yes`
    );
}


function openCenteredPopup(url) {
    const w = 1400;
    const h = 900;

    // ✅ 오늘 날짜
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const today = `${yyyy}-${mm}-${dd}`;

    // ✅ date 파라미터 추가
    const finalUrl = url.includes("?")
        ? `${url}&date=${today}`
        : `${url}?date=${today}`;

    // ✅ 화면 중앙 계산
    const screenX = window.screenX !== undefined ? window.screenX : window.screenLeft;
    const screenY = window.screenY !== undefined ? window.screenY : window.screenTop;

    const outerW = window.outerWidth || document.documentElement.clientWidth;
    const outerH = window.outerHeight || document.documentElement.clientHeight;

    const left = screenX + Math.max(0, (outerW - w) / 2);
    const top = screenY + Math.max(0, (outerH - h) / 2);

    const opt = `width=${w},height=${h},left=${Math.round(left)},top=${Math.round(top)},scrollbars=yes,resizable=yes`;

    const pop = window.open(finalUrl, "outListPopup", opt);
    if (pop) pop.focus();
}

function goDate() {
    const d = document.getElementById("datePicker").value;
    if (!d) return alert("날짜 선택!");
    alert(d);
    // 여기서 바로 이동 (이 페이지 라우터로)
    location.href = "/out_d_bar_lists?date=" + encodeURIComponent(d);
}

document.addEventListener("DOMContentLoaded", () => {
    const rows = Array.from(document.querySelectorAll("tr.out-row"));

    // 1) out_no가 같은 구간을 그룹으로 묶어 스타일 적용
    let prev = null;
    let groupIndex = 0;

    for (let i = 0; i < rows.length; i++) {
        const outno = rows[i].dataset.outno;

        if (outno !== prev) {
            groupIndex++;
            // 그룹 시작 표시(윗줄 굵은 선)
            rows[i].classList.add("group-start");
            prev = outno;
        }

        // 그룹 번호 부여(홀/짝 배경 다르게)
        rows[i].dataset.group = groupIndex;
        rows[i].classList.add(groupIndex % 2 === 0 ? "g-even" : "g-odd");
    }

    // 2) 더블클릭하면 해당 out_no 수정 페이지로 이동(팝업 유지)
    rows.forEach(tr => {
        tr.addEventListener("dblclick", () => {
            const outno = tr.dataset.outno;
            // alert(outno)
            location.href = `/out_edit?out_no=${encodeURIComponent(outno)}`;
        });
    });
});


function saveEdit() {
    const outNo = document.getElementById("out_no").innerText.trim();
    const rows = Array.from(document.querySelectorAll("tbody tr[data-id]")).map(tr => ({
        id: tr.dataset.id,
        car_no: tr.querySelector(".car_no").value.trim(),
        out_qty: Number(tr.querySelector(".out_qty").value)
    }));

    fetch("/out_edit_save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ out_no: outNo, rows })
    })
        .then(r => r.json())
        .then(d => {
            if (d.result === "ok") {
                alert("수정 완료");
                if (window.opener) window.opener.location.reload();
                window.close();
            } else {
                alert("수정 실패");
            }
        })
        .catch(e => {
            console.error(e);
            alert("서버 오류");
        });
}

// 삭제(출고번호 단위) - /out_edit_delete 라우터로 POST 보내는 예시
function deleteOut() {
    const outNo = document.getElementById("out_no").innerText.trim();
    if (!confirm(outNo + " 전체 삭제?")) return;

    fetch("/out_edit_delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ out_no: outNo })
    })
        .then(r => r.json())
        .then(d => {
            if (d.result === "ok") {
                alert("삭제 완료");
                if (window.opener) window.opener.location.reload();
                window.close();
            } else {
                alert("삭제 실패");
            }
        })
        .catch(e => {
            console.error(e);
            alert("서버 오류");
        });
}

$(document).on("click", "#out_btnUpdate", function () {
    update_rows();
})


function update_rows() {
    if (!confirm("수정합니까?")) return;

    const date = $("#work_date").val();   // ✅ 여기로 빼기(중요!)

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

    if (hasError) {
        alert(errorMsg);
        return;
    }

    $.ajax({
        url: "/out_d_bar_lists_Update",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ rows }),
        success: function (res) {
            alert(`수정완료(${res.updated}건)`);
            location.href = `/out_d_bar_lists?date=${date}`; // ✅ 이제 정상
        },
        error: function (xhr) {
            console.log("ERROR:", xhr.status, xhr.responseText);
            alert("수정실패");
            location.href = `/out_d_bar_lists?date=${date}`;
        }
    });
}


$(document).on("click", "#out_btnDelete", function () {
    delete_rows();
})
function delete_rows() {
    if (!confirm("정말 삭제합니까?")) return;
    const out_no = $("#out_no").val();
    const date = $("#work_date").val();   // ✅ 이 줄 추가
    if (!out_no) {
        alert("out_no 값이 없습니다. (#out_no 확인)");
        return;
    }

    $.ajax({
        url: "/out_delete_by_outno",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ out_no: out_no }),
        success: function (res) {
            alert(`삭제완료(${res.deleted}건)`);
            location.href = `/out_d_bar_lists?date=${date}`;
        },
        error: function (xhr) {
            console.log("삭제 ERROR:", xhr.status, xhr.responseText);
            alert("삭제실패");
        }
    });
}

// 파일명 표시
$(document).on("change", "#bulkFile", function () {
    if (!this.files || !this.files.length) return;

    const file = this.files[0];
    const name = file.name.toLowerCase();

    if (!name.endsWith(".xlsx")) {
        alert("⚠️ .xlsx 파일만 업로드 가능합니다.\n(.xls 파일은 Excel에서 저장 후 다시 올려주세요)");
        this.value = ""; // 선택 취소
        $("#bulkFileName").text("선택된 파일 없음");
        return;
    }
    $("#bulkFileName").text(file.name);
});


// 파일 선택 시 파일명 표시
$(document).on("change", "#bulkFile", function () {
    const name = this.files && this.files.length ? this.files[0].name : "선택된 파일 없음";
    $("#bulkFileName").text(name);
});

// 일괄등록 버튼 클릭
$(document).on("click", "#bulkUploadBtn", function () {
    const fileInput = $("#bulkFile")[0];

    if (!fileInput.files || fileInput.files.length === 0) {
        alert("업로드할 파일을 선택하세요.");
        return;
    }

    const file = fileInput.files[0];

    // 확장자 체크 (xlsx만)
    const name = (file.name || "").toLowerCase();
    if (!name.endsWith(".xlsx")) {
        alert("xlsx 파일만 업로드 가능합니다. (.xls 불가)");
        return;
    }

    const fd = new FormData();
    fd.append("file", file);

    $.ajax({
        url: "/in_bulk_upload",
        type: "POST",
        data: fd,
        processData: false,   // FormData 필수
        contentType: false,   // FormData 필수
        success: function (res) {
            if (res.result === "ok") {
                alert(`일괄등록 완료 (${res.inserted || res.rows || 0}건)`);
                // 필요하면 리스트 새로고침
                // location.reload();
            } else {
                alert(res.msg || "일괄등록 실패");
            }
        },
        error: function (xhr) {
            let msg = "일괄등록 실패";
            try {
                const r = JSON.parse(xhr.responseText);
                if (r.msg) msg = r.msg;
            } catch (e) { }
            alert(msg);
        }
    });
});

$(document).on("click", "#lists_btnOut", function () {
    const w = 1200;
    const h = 700;

    const screenX = window.screenX !== undefined ? window.screenX : window.screenLeft;
    const screenY = window.screenY !== undefined ? window.screenY : window.screenTop;

    const outerW = window.outerWidth || document.documentElement.clientWidth;
    const outerH = window.outerHeight || document.documentElement.clientHeight;

    const left = screenX + Math.max(0, (outerW - w) / 2);
    const top  = screenY + Math.max(0, (outerH - h) / 2);

    const opt = `
        width=${w},
        height=${h},
        left=${Math.round(left)},
        top=${Math.round(top)},
        scrollbars=yes,
        resizable=yes
    `;

    const pop = window.open("/out_bulk_form", "outBulk", opt);
    if (pop) pop.focus();
});


$(function(){
    if(!$("#work_date").val()){
      const d = new Date();
      const y = d.getFullYear();
      const m = String(d.getMonth()+1).padStart(2,"0");
      const day = String(d.getDate()).padStart(2,"0");
      $("#work_date").val(`${y}-${m}-${day}`);
    }
})



