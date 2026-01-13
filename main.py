from flask import Flask, render_template,jsonify,redirect,request,url_for
from datetime import datetime,timedelta
import pymysql
import pandas as pd
import re

from decimal import Decimal, InvalidOperation

app = Flask(__name__)
conn = pymysql.connect(
    host="127.0.0.1",
    user = "root",
    charset="utf8",
    passwd="0001",
    autocommit=True
)

with conn.cursor() as cur:
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS hangsa")
conn.select_db("hangsa")


# 테이블 생성
with conn.cursor() as cur:
    cur.execute("CREATE TABLE IF NOT EXISTS in_d_bar (\
                    lot_no VARCHAR(20) PRIMARY KEY ,\
                    vessel_name VARCHAR(30) NOT NULL,\
                    owner_name VARCHAR(30) NOT NULL,\
                    cargo_no VARCHAR(20),\
                    bl_no VARCHAR(20) NOT NULL,\
                    maker VARCHAR(20) NOT NULL,\
                    cargo_type VARCHAR(20),\
                    steel_type VARCHAR(20),\
                    size VARCHAR(20),\
                    bundle_qty int,\
                    mt_weight decimal(10,3),\
                    date_at DATETIME DEFAULT CURRENT_TIMESTAMP\
                    );")
# 출고테이블 생성 (DB 수정본 반영)
with conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS out_d_bar (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            out_no VARCHAR(30) NOT NULL,
            lot_no VARCHAR(20) NOT NULL,
            car_no VARCHAR(20),
            out_qty DECIMAL(10,1) NOT NULL DEFAULT 0.0,
            out_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

            UNIQUE KEY uk_out_no (out_no),
            KEY idx_lot_date (lot_no, out_date),

            CONSTRAINT fk_out_lot
              FOREIGN KEY (lot_no)
              REFERENCES in_d_bar(lot_no)
              ON UPDATE CASCADE
              ON DELETE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
    """)
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/list")
def in_list():
    try:
        conn.select_db("hangsa")
    except Exception as e:
        print("🔥 /list 오류:", e)
        return jsonify({"error": str(e)}), 500
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM in_d_bar ORDER BY date_at DESC;')
            contents = cur.fetchall()
            rows=[{"lot_no":row[0],
                    "vessel_name":row[1],
                    "owner_name":row[2],
                    "cargo_no":row[3],
                    "bl_no" :row[4],
                    "maker":row[5],
                    "cargo_type":row[6],
                    "steel_type":row[7],
                    "size":row[8],
                    "bundle_qty":row[9],
                    "mt_weight":row[10],
                    "unit_wt": row[11],        # (선택)
                    "date_at": row[12]        # ✅ 저장시간
                    } for row in contents]

            # print(rows)
            return render_template("in_list.html", rows=rows)

    except Exception as e:
        print("🔥 /list 실행 오류:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/in_d_bar")
def in_d_bar():
    return render_template("in_d_bar.html")



@app.route("/in_form", methods=["GET", "POST"])
def in_form():
    if request.method == "POST":
        lot_no_receive      = request.form.get("lot_no")
        vessel_name_receive = request.form.get("vessel_name")
        owner_name_receive  = request.form.get("owner_name")
        cargo_no_receive    = request.form.get("cargo_no")
        bl_no_receive       = request.form.get("bl_no")
        maker_receive       = request.form.get("maker")
        cargo_type_receive  = request.form.get("cargo_type")
        steel_type_receive  = request.form.get("steel_type")
        size_receive        = request.form.get("size")
        bundle_qty_receive  = request.form.get("bundle_qty")
        mt_weight_receive   = request.form.get("mt_weight")
        now = datetime.now()
        try:
            with conn.cursor() as cur:

                # 1️⃣ 중복 체크
                cur.execute(
                    "SELECT COUNT(*) FROM in_d_bar WHERE lot_no=%s",
                    (lot_no_receive,)
                )
                if cur.fetchone()[0] > 0:
                    return "<h1>lot_NO 중복입니다.</h1>"

                # 2️⃣ INSERT (이게 빠져 있었음)
                sql = """
                INSERT INTO in_d_bar (
                    lot_no, vessel_name, owner_name, cargo_no,
                    bl_no, maker, cargo_type, steel_type,
                    size, bundle_qty, mt_weight,date_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
                cur.execute(sql, (
                    lot_no_receive,
                    vessel_name_receive,
                    owner_name_receive,
                    cargo_no_receive,
                    bl_no_receive,
                    maker_receive,
                    cargo_type_receive,
                    steel_type_receive,
                    size_receive,
                    bundle_qty_receive,
                    mt_weight_receive,
                    now
                ))

            # 3️⃣ 커밋 (이것도 필수)
            conn.commit()
            return """
                        <script>
                        if (window.opener) {
                            window.opener.location.href = "/list";
                        }
                        window.close();
                        </script>
                    """

        except Exception as e:
            conn.rollback()
            print("DB ERROR:", e)
            return "ERROR"
    else:
        return render_template("in_form.html")

@app.route("/search")
def search():
    data = request.args.get("id")
    if not data:
        return jsonify({"error":"missing id"}),400
    app.logger.info(f"search lot_no={data}")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                   
                SELECT lot_no, vessel_name, bl_no, owner_name,cargo_no,cargo_type,
                    size, bundle_qty, mt_weight, maker, steel_type, date_at
                FROM in_d_bar WHERE lot_no = %s
            """, (data,))
            row = cur.fetchone()

        if not row:
            return jsonify({"error": "not found"}), 404

        return jsonify({
            "lot_no": row[0],
            "vessel_name": row[1],
            "cargo_no":row[2],
            "bl_no": row[3],
            "owner_name": row[4],
            "cargo_type":row[5],
            "size": row[6],
            "bundle_qty": row[7],
            "mt_weight": row[8],
            "maker": row[9],
            "steel_type": row[10],
            "date": row[11].strftime("%Y-%m-%d %H:%M") if row[10] else ""
        })
        # print(vessel_name)
    except Exception as e:
        app.logger.exception("search error")
        return jsonify({"error": str(e)}), 500

@app.route("/update", methods=["POST"])
def update():
    data = request.get_json()
    if not data:
        return jsonify({"error": "no data"}), 400

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE in_d_bar SET
                    vessel_name=%s,
                    cargo_no=%s,
                    cargo_type=%s,
                    bl_no=%s,
                    owner_name=%s,
                    size=%s,
                    bundle_qty=%s,
                    mt_weight=%s,
                    maker=%s,
                    steel_type=%s
                WHERE lot_no=%s
            """, (
                data["vessel_name"],
                data["cargo_no"],
                data["cargo_type"],
                data["bl_no"],
                data["owner_name"],
                data["size"],
                data["bundle_qty"],
                data["mt_weight"],
                data["maker"],
                data["steel_type"],
                data["lot_no"]
            ))

        return jsonify({"result": "ok"})
    except Exception as e:
        app.logger.exception("update error")
        return jsonify({"error": str(e)}), 500

@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_json(silent=True) or {}
    lot_no = data.get("lot_no")
    print(lot_no)
    if not lot_no:
        return jsonify({"error": "lot_no missing"}), 400

    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM in_d_bar WHERE lot_no=%s",
                (lot_no,)
            )
        return jsonify({"result": "ok"})
    except Exception as e:
        app.logger.exception("delete error")
        return jsonify({"error": str(e)}), 500
# 출고입력
@app.route('/out_form')
def out_form():
    lot_no = request.args.get("lot_no")
    # print(lot_no)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT lot_no, vessel_name, bl_no, owner_name, cargo_no, cargo_type,
                    size, bundle_qty, mt_weight, maker, steel_type, date_at
                FROM in_d_bar
                WHERE lot_no = %s
            """, (lot_no,))
            row = cur.fetchone()

        if not row:
            return render_template("out_form.html", idx=lot_no, rows=[], msg="해당 LOT_NO 없음")

        # ✅ SELECT 순서 그대로 매핑
        rows = [{
            "lot_no": row[0],
            "vessel_name": row[1],
            "bl_no": row[2],
            "owner_name": row[3],
            "cargo_no": row[4],
            "cargo_type": row[5],
            "size": row[6],
            "bundle_qty": row[7],
            "mt_weight": row[8],
            "maker": row[9],
            "steel_type": row[10],
            "date_at": row[11],
        }]
        # print(rows)
        return render_template("out_form.html", idx=lot_no, rows=rows)

    except Exception as e:
        app.logger.exception("out_form error")
        return str(e), 500

@app.route('/out_list')
def out_list():
    lot_nos = request.args.getlist("lot_no")
    # print("✅ lot_nos:", lot_nos)

    if not lot_nos:
        return redirect(url_for("out_d_bar"))

    placeholders = ",".join(["%s"] * len(lot_nos))

    sql = f"""
        SELECT
            i.lot_no,
            i.owner_name,
            i.steel_type,
            i.size,
            i.maker,
            i.bundle_qty AS in_qty,
            IFNULL(SUM(o.out_qty), 0) AS out_sum,
            (i.bundle_qty - IFNULL(SUM(o.out_qty), 0)) AS stock_qty,
            MAX(o.out_date) AS last_out_date
        FROM in_d_bar i
        LEFT JOIN out_d_bar o ON i.lot_no = o.lot_no
        WHERE i.lot_no IN ({placeholders})
        GROUP BY
            i.lot_no, i.owner_name, i.steel_type, i.size, i.maker, i.bundle_qty
        ORDER BY i.lot_no
    """

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            print("✅ SQL:", sql)
            print("✅ params:", lot_nos)
            cur.execute(sql, lot_nos)
            rows = cur.fetchall()

        return render_template("out_list.html", rows=rows)

    except Exception as e:
        print("🔥 out_list 오류:", e)
        return f"ERROR: {e}", 500
   
    except Exception as e:
        print("🔥 out_list 오류:", e)
        return f"ERROR: {e}", 500

@app.route("/out_d_bar", methods=["GET"])
def out_d_bar():
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    i.lot_no,
                    i.owner_name,
                    i.steel_type,
                    i.size,
                    i.maker,
                    i.bundle_qty AS in_qty,
                    IFNULL(SUM(o.out_qty), 0) AS out_sum,
                    (i.bundle_qty - IFNULL(SUM(o.out_qty), 0)) AS stock_qty,
                    MAX(o.out_date) AS last_out_date,
                    MAX(i.date_at) AS last_in_date
                FROM in_d_bar i
                LEFT JOIN out_d_bar o
                    ON o.lot_no = i.lot_no
                GROUP BY
                    i.lot_no, i.owner_name, i.steel_type, i.size, i.maker, i.bundle_qty
                ORDER BY  stock_qty DESC, MAX(i.date_at) DESC
            """)
            rows = cur.fetchall()

        result = [{
            "lot_no": r[0],
            "owner_name": r[1],
            "steel_type": r[2],
            "size": r[3],
            "maker": r[4],
            "in_qty": float(r[5]) if r[5] is not None else 0,
            "out_sum": float(r[6]) if r[6] is not None else 0,
            "stock_qty": float(r[7]) if r[7] is not None else 0,
            "last_out_date": r[8].strftime("%Y-%m-%d %H:%M") if r[8] else ""
        } for r in rows]

        return render_template("out_d_bar.html", rows=result)

    except Exception as e:
        app.logger.exception("out_d_bar error")
        return str(e), 500

@app.route("/in_bulk_upload_json", methods=["POST"])
def in_bulk_upload_json():
    print("✅ /in_bulk_upload_json CALLED")
    print("✅ content-type:", request.content_type)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        print("❌ JSON NONE. raw=", request.data[:300])
        return jsonify(result="fail", msg="JSON 데이터 없음"), 400

    # ✅ 먼저 꺼내야 함 (NameError 방지)
    headers = data.get("headers", [])
    rows = data.get("rows", [])
    client_total_qty = data.get("totalQty", 0)
    client_total_weight = data.get("totalWeight", 0)

    if not headers or not rows:
        return jsonify(result="fail", msg="헤더 또는 데이터 비어있음"), 400

    # ✅ 헤더 정규화 (공백 제거 + / 정리)
    def norm(h):
        s = str(h)
        s = re.sub(r"\s+", "", s)   # 모든 공백 제거
        s = s.replace("/", "")      # LOT/NO -> LOTNO (원하면 유지해도 됨)
        return s.upper()

    norm_headers = [norm(h) for h in headers]

    # ---------------------------
    # 컬럼 인덱스 찾기 (norm_headers 기준)
    # ---------------------------
    def find_idx(cands):
        for c in cands:
            c = norm(c)
            if c in norm_headers:
                return norm_headers.index(c)
        return -1

    idx_lot    = find_idx(["LOT/NO", "LOT / NO", "LOTNO", "LOT", "LOT NO"])
    idx_vsl    = find_idx(["선명"])
    idx_owner  = find_idx(["원화주", "화주"])
    idx_qty    = find_idx(["재고수량", "수량"])
    idx_wt     = find_idx(["재고중량", "중량"])
    idx_size   = find_idx(["규격"])
    idx_cn     = find_idx(["CN", "C/N"])
    idx_origin = find_idx(["원산지"])
    idx_cargo  = find_idx(["통관"])
    idx_cust   = find_idx(["수탁품"])
    idx_steel  = find_idx(["강종", "재질", "STEEL"])

    print("✅ idx:", idx_lot, idx_vsl, idx_owner, idx_qty, idx_wt)

    if idx_lot < 0 or idx_qty < 0 or idx_wt < 0 or idx_vsl < 0 or idx_owner < 0:
        return jsonify(result="fail", msg="필수 컬럼(LOT/NO, 선명, 화주, 수량, 중량) 누락"), 400

    # ---------------------------
    # 숫자 파싱
    # ---------------------------
    def to_num(v):
        try:
            return float(str(v).replace(",", "").strip())
        except:
            return 0.0

    # 합계 재검증
    server_total_qty = 0.0
    server_total_wt  = 0.0
    for r in rows:
        server_total_qty += to_num(r[idx_qty])
        server_total_wt  += to_num(r[idx_wt])

    if abs(server_total_qty - float(client_total_qty)) > 0.0001 or \
       abs(server_total_wt  - float(client_total_weight)) > 0.0001:
        return jsonify(
            result="fail",
            msg="합계 불일치",
            serverQty=server_total_qty, serverWt=server_total_wt,
            clientQty=client_total_qty, clientWt=client_total_weight
        ), 400

    # ---------------------------
    # DB 저장
    # ---------------------------
    inserted = 0
    try:
        with conn.cursor() as cur:
            for r in rows:
                lot_no = str(r[idx_lot]).strip()
                if not lot_no or lot_no.lower() == "nan":
                    continue

                vessel_name = str(r[idx_vsl]).strip()
                owner_name  = str(r[idx_owner]).strip()

                bl_no  = (str(r[idx_cn]).strip() if idx_cn >= 0 and str(r[idx_cn]).strip() else "미상")
                maker  = (str(r[idx_origin]).strip() if idx_origin >= 0 and str(r[idx_origin]).strip() else "미상")

                cargo_no   = (str(r[idx_cargo]).strip() if idx_cargo >= 0 else "")
                cargo_type = (str(r[idx_cust]).strip()  if idx_cust  >= 0 else "")
                steel_type = (str(r[idx_steel]).strip() if idx_steel >= 0 else "")
                size       = (str(r[idx_size]).strip()  if idx_size  >= 0 else "")

                bundle_qty = float(to_num(r[idx_qty]))
                mt_weight  = round(to_num(r[idx_wt]), 3)

                cur.execute("""
                    INSERT INTO in_d_bar
                    (lot_no, vessel_name, owner_name, cargo_no, bl_no, maker,
                     cargo_type, steel_type, size, bundle_qty, mt_weight)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                        vessel_name=VALUES(vessel_name),
                        owner_name=VALUES(owner_name),
                        cargo_no=VALUES(cargo_no),
                        bl_no=VALUES(bl_no),
                        maker=VALUES(maker),
                        cargo_type=VALUES(cargo_type),
                        steel_type=VALUES(steel_type),
                        size=VALUES(size),
                        bundle_qty=VALUES(bundle_qty),
                        mt_weight=VALUES(mt_weight)
                """, (
                    lot_no, vessel_name, owner_name, cargo_no, bl_no, maker,
                    cargo_type, steel_type, size, bundle_qty, mt_weight
                ))
                inserted += 1

        conn.commit()  # ✅ 확실히 커밋
        return jsonify(result="ok", inserted=inserted)

    except Exception as e:
        conn.rollback()
        print("🔥 DB ERROR:", e)
        return jsonify(result="fail", msg=str(e)), 500




@app.route("/out_d_save", methods=["POST"])
def out_d_save():
    data = request.get_json() or {}

    lot_no = data["lot_no"]
    out_qty = float(data["out_qty"])

    try:
        with conn.cursor() as cur:
            # 현재 재고 계산
            cur.execute("""
                SELECT
                    i.bundle_qty - IFNULL(SUM(o.out_qty), 0)
                FROM in_d_bar i
                LEFT JOIN out_d_bar o ON o.lot_no = i.lot_no
                WHERE i.lot_no = %s
                GROUP BY i.bundle_qty
            """, (lot_no,))
            stock = cur.fetchone()[0]

            if out_qty > stock:
                return jsonify({
                    "result": "error",
                    "msg": f"재고 부족 (현재 재고: {stock})"
                }), 400

            # 출고 저장
            cur.execute("""
                INSERT INTO out_d_bar (lot_no, car_no, out_qty, out_no)
                VALUES (%s, %s, %s, %s)
            """, (
                lot_no,
                data["car_no"],
                out_qty,
                data["out_no"]
            ))

        conn.commit()
        return jsonify({"result": "ok"})

    except Exception as e:
        conn.rollback()
        return jsonify({"result": "error", "msg": str(e)}), 500


@app.route("/out_d_save_bulk", methods=["POST"])
def out_d_save_bulk():
    data = request.get_json() or {}
    rows = data.get("rows", [])
    if not rows:
        return jsonify({"result": "error", "msg": "rows 비어있음"}), 400

    errors = []
    try:
        with conn.cursor() as cur:
            # 재고 체크
            for r in rows:
                lot_no = r.get("lot_no")
                out_qty = float(r.get("out_qty", 0))

                cur.execute("""
                    SELECT i.bundle_qty - IFNULL(SUM(o.out_qty), 0)
                    FROM in_d_bar i
                    LEFT JOIN out_d_bar o ON o.lot_no = i.lot_no
                    WHERE i.lot_no = %s
                    GROUP BY i.bundle_qty
                """, (lot_no,))
                row = cur.fetchone()
                stock = row[0] if row else 0

                if out_qty > stock:
                    errors.append({"lot_no": lot_no, "msg": f"재고 부족 (현재 {stock})"})

            if errors:
                conn.rollback()
                return jsonify({"result": "error", "errors": errors}), 400

            # insert
            for r in rows:
                cur.execute("""
                    INSERT INTO out_d_bar (lot_no, car_no, out_qty, out_no)
                    VALUES (%s, %s, %s, %s)
                """, (r["lot_no"], r["car_no"], float(r["out_qty"]), r["out_no"]))

        conn.commit()
        return jsonify({"result": "ok"})

    except Exception as e:
        conn.rollback()
        return jsonify({"result": "error", "msg": str(e)}), 500

# ---------- OUT LIST BY DATE ----------
def get_conn():
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        passwd="0001",
        db="hangsa",          # ✅ 이거 추가가 제일 깔끔
        charset="utf8mb4",
        autocommit=True  # 또는 False로 통일
    )

@app.route("/out_d_bar_lists")
def out_d_bar_lists():
    date_str = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    ymd = date_str.replace("-", "")  # 2026-01-09 -> 20260109

    start = datetime.strptime(date_str, "%Y-%m-%d")
    end = start + timedelta(days=1)

    date_kr = f"{start.year}년 {start.month}월 {start.day}일"

    conn = get_conn()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # ✅ UNION 전체 ORDER BY에서 o.id 같은 테이블별칭 사용 불가 → tid로 뽑아서 정렬
            cur.execute("""
                SELECT
                    grp, out_no, owner_name, maker, steel_type, size,
                    car_no, out_qty, out_wt, out_date, tid
                FROM (
                    -- ✅ A) 미출고(차량번호 4자리 미만) + 선택일자 이하(out_date 기준)
                    SELECT
                        'PENDING' AS grp,
                        o.out_no,
                        i.owner_name,
                        i.maker,
                        i.steel_type,
                        i.size,
                        o.car_no,
                        o.out_qty,
                        ROUND(o.out_qty * i.unit_wt, 3) AS out_wt,
                        o.out_date,
                        o.id AS tid
                    FROM out_d_bar o
                    LEFT JOIN in_d_bar i ON i.lot_no = o.lot_no
                    WHERE (
                        o.car_no IS NULL
                        OR TRIM(o.car_no) = ''
                        OR o.car_no = '.'
                        OR LENGTH(TRIM(o.car_no)) < 4
                    )
                    AND o.out_date < %s   -- ✅ 2026-01-09 이하(= 2026-01-10 미만)

                    UNION ALL

                    -- ✅ B) 선택일자 출고내역 전부(out_no 기준, 차량번호 조건 없음)
                    SELECT
                        'DAY' AS grp,
                        o.out_no,
                        i.owner_name,
                        i.maker,
                        i.steel_type,
                        i.size,
                        o.car_no,
                        o.out_qty,
                        ROUND(o.out_qty * i.unit_wt, 3) AS out_wt,
                        o.out_date,
                        o.id AS tid
                    FROM out_d_bar o
                    LEFT JOIN in_d_bar i ON i.lot_no = o.lot_no
                    WHERE o.out_no LIKE %s
                ) t
                ORDER BY
                    CASE WHEN grp='PENDING' THEN 0 ELSE 1 END,
                    out_date DESC, out_no DESC, tid DESC
            """, (end, ymd + "%"))

            raw = cur.fetchall()

        pending_rows, day_rows = [], []
        for r in raw:
            out_dt = r.get("out_date")
            r["out_qty"] = float(r.get("out_qty") or 0)
            r["out_wt"] = float(r.get("out_wt") or 0)
            r["save_time"] = out_dt.strftime("%H:%M:%S") if out_dt else ""

            # 화면에는 tid 안 보여도 됨(정렬용)
            r.pop("tid", None)

            if r.get("grp") == "PENDING":
                pending_rows.append(r)
            else:
                day_rows.append(r)

        # ✅ 기존 템플릿(rows) 호환
        rows = pending_rows + day_rows

        return render_template(
            "out_d_bar_lists.html",
            date_str=date_str,
            date_kr=date_kr,
            rows=rows,
            pending_rows=pending_rows,
            day_rows=day_rows
        )
    finally:
        conn.close()

@app.route("/out_edit", methods=["GET"])
def out_edit():
    out_no = request.args.get("out_no")
    if not out_no:
        return "out_no가 없습니다", 400

    conn = get_conn()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("""
                SELECT
                    o.id,
                    o.out_no,
                    o.lot_no,
                    o.car_no,
                    o.out_qty,
                    o.out_date
                FROM out_d_bar o
                WHERE o.out_no = %s
                ORDER BY o.id ASC
            """, (out_no,))
            rows = cur.fetchall()

        if not rows:
            return f"해당 전표(out_no={out_no})가 없습니다", 404

        # ✅ date 넘겨줘야 JS에서 /out_d_bar_lists?date= 로 돌아갈 때 필요
        date_str = rows[0]["out_date"].strftime("%Y-%m-%d") if rows[0].get("out_date") else ""

        return render_template("out_edit.html", out_no=out_no, rows=rows, date=date_str)
    finally:
        conn.close()


@app.route("/out_d_bar_lists_Update", methods=["POST"])
def out_d_bar_lists_Update():
    data = request.get_json(silent=True) or {}
    rows = data.get("rows") or []
    if not rows:
        return jsonify(result="fail", msg="rows 없음"), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            updated = 0
            for r in rows:
                _id = r.get("id")
                car_no = (r.get("car_no") or "").strip()
                out_qty = r.get("out_qty")

                if not _id:
                    continue

                cur.execute("""
                    UPDATE out_d_bar
                    SET car_no=%s, out_qty=%s
                    WHERE id=%s
                """, (car_no, out_qty, _id))
                updated += cur.rowcount

        conn.commit()
        return jsonify(result="ok", updated=updated)
    except Exception as e:
        conn.rollback()
        return jsonify(result="fail", msg=str(e)), 500
    finally:
        conn.close()


@app.route("/out_delete_by_outno", methods=["POST"])
def out_delete_by_outno():
    data = request.get_json(silent=True) or {}
    out_no = (data.get("out_no") or "").strip()
    if not out_no:
        return jsonify(result="fail", msg="out_no 없음"), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM out_d_bar WHERE out_no=%s", (out_no,))
            deleted = cur.rowcount
        conn.commit()
        return jsonify(result="ok", deleted=deleted)
    except Exception as e:
        conn.rollback()
        return jsonify(result="fail", msg=str(e)), 500
    finally:
        conn.close()






@app.route("/out_bulk_form", methods=["GET"])
def out_bulk_form():
    return render_template("out_bulk_form.html")

# =========================
# OUT BULK SAVE (최종)
# - 엑셀 복붙 텍스트에서:
#   out_no = (일자8자리 + 번호4자리)
#   lot_no = LOT 패턴(250821-196, 251212-13-Q1 등)
#   car_no = 차량번호 패턴(89오4552, 경기93아5400 등)
#   out_qty = "운송수량" (제강사/원산지 다음에 나오는 첫 숫자 우선)
# - out_date = DB DEFAULT CURRENT_TIMESTAMP 사용 (INSERT에서 out_date 제외)
# - (out_no, lot_no) UNIQUE 기준으로 중복 방지 + ON DUPLICATE KEY UPDATE(수량 합산)
# =========================

import re
from datetime import datetime
from flask import request, jsonify

# ---- patterns
LOT_RE   = re.compile(r"^\d{6}-[A-Za-z0-9-]+$")   # 251215-1650, 251212-13-Q1
DATE8_RE = re.compile(r"^\d{8}$")                 # 20260102
SEQ4_RE  = re.compile(r"^\d{4}$")                 # 0003

# 숫자(소수 포함)
def _is_num(s: str) -> bool:
    try:
        float(str(s).replace(",", ""))
        return True
    except:
        return False

def _to_float(s: str, default=None):
    try:
        return float(str(s).replace(",", "").strip())
    except:
        return default

# 차량번호: "89오4552" / "84저3196" / "경기93아5400" / "서울87아2216" / "전북81사4321" 등
CAR_RE = re.compile(r"^(?:[가-힣]{2}\d{2}[가-힣]\d{4}|\d{2,3}[가-힣]\d{4})$")

def _clean_token(s: str) -> str:
    if s is None:
        return ""
    s = str(s).replace("\u00a0", " ").strip()
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _tokenize_line(line: str):
    """
    엑셀 복붙 라인: 탭 기준이지만, 셀 안에 공백이 섞일 수 있어 2단계로 토큰화
    """
    cols = [c for c in line.split("\t") if str(c).strip() != ""]
    toks = []
    for c in cols:
        c = _clean_token(c)
        if not c:
            continue
        # 셀 안 공백을 다시 쪼개기 (단, 한글 회사명 등은 통째로 남아도 상관 없음)
        toks.extend([x for x in c.split(" ") if x.strip() != ""])
    # 공백 제거(토큰 내부 공백 제거가 필요할 때가 있어서 한 번 더)
    toks = [re.sub(r"\s+", "", t) for t in toks if t]
    return toks

# "제강사/원산지 힌트" (네 화면에 나오는 값들 위주)
MAKER_HINT = (
    "중국", "중국산", "일본", "일본산", "국산",
    "POSCO", "포스코", "JFE", "현대", "동국", "KISCO",
)

def _pick_qty(tokens):
    """
    운송수량 추출:
    1) 제강사/원산지 힌트가 들어있는 토큰 뒤에서 가장 먼저 나오는 숫자 => 운송수량
    2) 없으면 fallback:
       - DATE8/SEQ4 제외
       - 0보다 큰 숫자 중, '너무 큰 날짜(>=10000000)'는 제외
       - 첫 번째 값 사용
    """
    # 1) maker hint 뒤 숫자
    for i, t in enumerate(tokens):
        if any(h in t for h in MAKER_HINT):
            for j in range(i + 1, min(i + 12, len(tokens))):
                if _is_num(tokens[j]):
                    v = _to_float(tokens[j])
                    if v is not None:
                        return v

    # 2) fallback 숫자
    for t in tokens:
        if DATE8_RE.match(t) or SEQ4_RE.match(t):
            continue
        if _is_num(t):
            v = _to_float(t)
            if v is None:
                continue
            # 날짜 같은 큰 숫자 방지
            if v >= 10000000:
                continue
            if v > 0:
                return v

    return 1.0


@app.route("/out_bulk_save", methods=["POST"])
def out_bulk_save():
    """
    폼 필드:
      - bulk_text: 엑셀에서 복사/붙여넣기한 텍스트 (필수)
    """
    bulk_text = (request.form.get("bulk_text") or "").strip()

    if not bulk_text:
        return jsonify({"ok": False, "msg": "붙여넣기 데이터(bulk_text)가 비었습니다."}), 400

    lines = [ln for ln in bulk_text.splitlines() if ln.strip()]
    parsed = []  # (out_no, lot, car_no, qty)

    for ln in lines:
        toks = _tokenize_line(ln)
        if not toks:
            continue

        # out_no = 날짜8 + 번호4 (같은 줄에 있어야 함)
        date8 = next((t for t in toks if DATE8_RE.match(t)), None)
        seq4  = next((t for t in toks if SEQ4_RE.match(t)), None)
        if not (date8 and seq4):
            # 일자/번호가 없는 줄은 무시
            continue
        out_no = date8 + seq4

        # lot
        lot = next((t for t in toks if LOT_RE.match(t)), None)
        if not lot:
            continue

        # car_no (없으면 None)
        car_no = next((t for t in toks if CAR_RE.match(t)), None)
        if not car_no:
            car_no = None

        # qty = 운송수량
        qty = _pick_qty(toks)

        parsed.append((out_no, lot, car_no, qty))

    if not parsed:
        return jsonify({"ok": False, "msg": "파싱된 행이 없습니다. (일자/번호/LOT 인식 실패)"}), 400

    # ✅ (out_no, lot_no) 기준으로 중복 합치기 (같은 전표에서 같은 LOT가 여러 줄이면 수량 합산)
    #    car_no는 값이 있으면 마지막 값으로 업데이트
    key_map = {}
    for out_no, lot, car, qty in parsed:
        k = (out_no, lot)
        if k not in key_map:
            key_map[k] = {"qty": 0.0, "car": car}
        key_map[k]["qty"] += float(qty or 0.0)
        if car:
            key_map[k]["car"] = car

    unique_lots = list({lot for (_, lot) in key_map.keys()})

    try:
        with conn.cursor() as cur:
            # ✅ FK 통과: in_d_bar에 존재하는 LOT만 저장
            fmt = ",".join(["%s"] * len(unique_lots))
            cur.execute(f"SELECT lot_no FROM in_d_bar WHERE lot_no IN ({fmt})", unique_lots)
            rows = cur.fetchall()
            exists = set(r["lot_no"] if isinstance(r, dict) else r[0] for r in rows)

            ok_rows = []
            missing = []

            for (out_no, lot), v in key_map.items():
                if lot not in exists:
                    missing.append(lot)
                    continue

                # out_date는 DB DEFAULT CURRENT_TIMESTAMP 사용 (INSERT에서 제외)
                ok_rows.append((out_no, lot, v["car"], v["qty"]))

            if not ok_rows:
                conn.rollback()
                return jsonify({
                    "ok": True,
                    "inserted": 0,
                    "missing_count": len(set(missing)),
                    "missing_lots": sorted(list(set(missing)))[:200],
                    "msg": "저장할 LOT가 없습니다. (모두 누락 또는 FK 불일치)"
                })

            # ✅ (out_no, lot_no) UNIQUE 필요:
            # ALTER TABLE out_d_bar ADD UNIQUE KEY uq_outno_lotno (out_no, lot_no);
            #
            # ✅ 중복이면 수량 합산, 차량번호는 새 값이 있으면 덮어씀
            cur.executemany("""
                INSERT INTO out_d_bar (out_no, lot_no, car_no, out_qty)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    out_qty = out_qty + VALUES(out_qty),
                    car_no  = COALESCE(VALUES(car_no), car_no)
            """, ok_rows)

            conn.commit()

        return jsonify({
            "ok": True,
            "inserted": len(ok_rows),                 # 사용자 체감용(처리 대상 행 수)
            "missing_count": len(set(missing)),
            "missing_lots": sorted(list(set(missing)))[:200],
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "msg": str(e)}), 500
    

# @app.route("/up_list")
# def up_list():
#     return in_list()




# if __name__ == "__main__":
#     # print(app.url_map)
#     app.run(host="127.0.0.1", port=8000, debug=True)

if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://127.0.0.1:8000/list")  # 시작 페이지
    app.run(host="127.0.0.1", port=8000)

