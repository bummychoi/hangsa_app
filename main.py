from flask import Flask, render_template,jsonify,redirect,request,url_for
from datetime import datetime,timedelta
import pymysql
import pandas as pd
import re

import subprocess
import time
import webbrowser

# from routes.customs_routes import customs_bp

from decimal import Decimal, InvalidOperation



def ensure_mysql_service(service_name="MySQL80"):
    try:
        q = subprocess.run(["sc", "query", service_name], capture_output=True, text=True)
        if "RUNNING" in q.stdout:
            return True

        subprocess.run(["sc", "start", service_name], capture_output=True, text=True)
        time.sleep(2)
    except Exception:
        pass

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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS in_d_bar (
            lot_no VARCHAR(20) PRIMARY KEY,
            vessel_name VARCHAR(30) NOT NULL,
            owner_name VARCHAR(30) NOT NULL,
            cargo_no VARCHAR(20),
            bl_no VARCHAR(20) NOT NULL,
            maker VARCHAR(20) NOT NULL,
            cargo_type VARCHAR(20),
            steel_type VARCHAR(20),
            size VARCHAR(20),
            bundle_qty DECIMAL(10,1) NOT NULL DEFAULT 0.0,
            mt_weight DECIMAL(10,3) DEFAULT 0.000,

            unit_wt DECIMAL(12,6)
            GENERATED ALWAYS AS (
                CASE 
                    WHEN bundle_qty > 0 
                    THEN mt_weight / bundle_qty
                    ELSE 0
                END
            ) STORED,

            date_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
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
        print("🔥 /list DB 선택 오류:", e)
        return jsonify({"error": str(e)}), 500

    try:
        all_flag = (request.args.get("all") or "").strip()  # '1'이면 전체조회
        search_date = (request.args.get("search_date") or "").strip()

        # (검색 기능 남겨두려면 유지)
        search_type = (request.args.get("search_type") or "all").strip()
        keyword = (request.args.get("keyword") or "").strip()

        sql = "SELECT * FROM in_d_bar WHERE 1=1"
        params = []

        sum_sql = """
            SELECT
                IFNULL(SUM(bundle_qty), 0) AS total_bundle,
                IFNULL(SUM(mt_weight), 0) AS total_weight
            FROM in_d_bar
            WHERE 1=1
        """
        sum_params = []

        # ✅ 날짜필터는 "검색어 없을 때(조회)"만 적용
        if all_flag != "1" and not keyword:
            if not search_date:
                search_date = datetime.now().strftime("%Y-%m-%d")
            yymmdd = datetime.strptime(search_date, "%Y-%m-%d").strftime("%y%m%d")

            sql += " AND lot_no LIKE %s"
            params.append(yymmdd + "%")

            sum_sql += " AND lot_no LIKE %s"
            sum_params.append(yymmdd + "%")
        else:
            # 검색 모드(키워드 있음) 또는 전체조회면 날짜는 표시만 유지하고 필터는 안 건다
            if not search_date:
                search_date = datetime.now().strftime("%Y-%m-%d")

        # ✅ (선택) 키워드 검색 - 전체조회/날짜조회와 함께 동작
        allowed = {
            "lot_no": "lot_no",
            "vessel_name": "vessel_name",
            "cargo_no": "cargo_no",
            "owner_name": "owner_name",
        }

        if keyword:
            like = f"%{keyword}%"

            if search_type == "all":
                sql += """
                    AND (
                        lot_no LIKE %s OR
                        vessel_name LIKE %s OR
                        cargo_no LIKE %s OR
                        owner_name LIKE %s
                    )
                """
                params += [like, like, like, like]

                sum_sql += """
                    AND (
                        lot_no LIKE %s OR
                        vessel_name LIKE %s OR
                        cargo_no LIKE %s OR
                        owner_name LIKE %s
                    )
                """
                sum_params += [like, like, like, like]

            elif search_type in allowed:
                col = allowed[search_type]
                sql += f" AND {col} LIKE %s"
                params.append(like)

                sum_sql += f" AND {col} LIKE %s"
                sum_params.append(like)

        sql += " ORDER BY lot_no DESC"

        with conn.cursor() as cur:
            cur.execute(sql, params)
            contents = cur.fetchall()

            cur.execute(sum_sql, sum_params)
            total_bundle, total_weight = cur.fetchone()

        rows = [{
            "lot_no": row[0],
            "vessel_name": row[1],
            "owner_name": row[2],
            "cargo_no": row[3],
            "bl_no": row[4],
            "maker": row[5],
            "cargo_type": row[6],
            "steel_type": row[7],
            "size": row[8],
            "bundle_qty": row[9],
            "mt_weight": row[10],
            "unit_wt": row[11],
            "date_at": row[12]
        } for row in contents]

        return render_template(
            "in_list.html",
            rows=rows,
            search_date=search_date,
            all_flag=all_flag,
            total_bundle=total_bundle,
            total_weight=total_weight,
            search_type=search_type,
            keyword=keyword
        )

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
            "bl_no":row[2],
            "owner_name": row[3],
            "cargo_no": row[4],
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

        # ✅ 합계(전체 / pending / day)
        total_qty = sum(r["out_qty"] for r in rows)
        total_wt  = sum(r["out_wt"]  for r in rows)

        pending_total_qty = sum(r["out_qty"] for r in pending_rows)
        pending_total_wt  = sum(r["out_wt"]  for r in pending_rows)

        day_total_qty = sum(r["out_qty"] for r in day_rows)
        day_total_wt  = sum(r["out_wt"]  for r in day_rows)
        return render_template(
            "out_d_bar_lists.html",
            date_str=date_str,
            date_kr=date_kr,
            rows=rows,
            pending_rows=pending_rows,
            day_rows=day_rows,

            total_qty=total_qty,
            total_wt=total_wt,
            pending_total_qty=pending_total_qty,
            pending_total_wt=pending_total_wt,
            day_total_qty=day_total_qty,
            day_total_wt=day_total_wt
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
    today = datetime.now().strftime("%Y-%m-%d")
    return render_template("out_bulk_form.html", date=today)

def _clean(v):
    return (str(v).strip() if v is not None else "")

def _to_decimal(v, default=Decimal("0")):
    s = _clean(v).replace(",", "")
    if s == "":
        return default
    try:
        return Decimal(s)
    except InvalidOperation:
        return default

@app.route("/out_bulk_save", methods=["POST"])
def out_bulk_save():
    data = request.get_json(silent=True) or {}
    rows = data.get("rows", [])

    if not rows:
        return jsonify({"result": "fail", "msg": "no rows"}), 400

    try:
        with conn.cursor() as cur:
            # 1) lot_no 리스트 만들기
            lot_list = [_clean(r.get("lot_no")) for r in rows if _clean(r.get("lot_no"))]
            lot_list = list(dict.fromkeys(lot_list))
            if not lot_list:
                return jsonify({"result": "fail", "msg": "no lot_no"}), 400

            # 2) lot 존재 검증
            placeholders = ",".join(["%s"] * len(lot_list))
            cur.execute(f"SELECT lot_no FROM in_d_bar WHERE lot_no IN ({placeholders})", lot_list)
            exists = {x[0] for x in cur.fetchall()}

            missing = [x for x in lot_list if x not in exists]
            if missing:
                return jsonify({
                    "result": "fail",
                    "msg": "입고(in_d_bar)에 없는 LOT/NO가 있어서 저장 불가",
                    "missing_lot_no": missing[:50],
                    "missing_count": len(missing)
                }), 400

            # 3) INSERT
            insert_sql = """
                INSERT INTO out_d_bar (out_no, lot_no, car_no, out_qty, out_date)
                VALUES (%s, %s, %s, %s, NOW())
            """

            saved = 0
            for r in rows:
                out_no = _clean(r.get("out_no"))
                lot_no = _clean(r.get("lot_no"))
                car_no = _clean(r.get("car_no")) or None
                out_qty = _to_decimal(r.get("out_qty"), default=Decimal("0"))

                if not out_no or not lot_no:
                    # 한 줄이라도 핵심값 없으면 즉시 실패 처리(원하면 continue로 바꿔도 됨)
                    conn.rollback()
                    return jsonify({"result": "fail", "msg": "row missing out_no/lot_no"}), 400

                cur.execute(insert_sql, (out_no, lot_no, car_no, out_qty))
                saved += 1

        conn.commit()
        return jsonify({"result": "ok", "msg": "saved", "saved_rows": saved}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"result": "fail", "msg": str(e)}), 500



@app.route("/in_bulk_preview")
def in_bulk_preview():
    key = request.args.get("key")

    # ✅ key 없이 들어오면: opener의 localStorage key를 찾을 수 없으니
    # 그냥 템플릿에서 안내만 하지 말고, "key를 붙여서 다시 열어달라"로 유도
    return render_template("in_bulk_preview.html")

@app.route("/in_up_preview", methods=["POST"])
def in_up_preview():
    file = request.files.get("file")
    if not file:
        return "파일 없음", 400

    df = pd.read_excel(file).fillna("")
    headers = list(df.columns)               # ✅ headers
    rows = df.values.tolist()                # ✅ rows (2차원 배열)

    # 합계 (컬럼명이 엑셀에 맞게 조정 필요)
    def to_num(v):
        try: return float(str(v).replace(",", "").strip())
        except: return 0.0

    # 예: "재고수량", "재고중량" 같은 실제 컬럼명으로 바꿔야 함
    total_qty = sum(to_num(r[headers.index("재고수량")]) for r in rows) if "재고수량" in headers else 0
    total_weight = sum(to_num(r[headers.index("재고중량")]) for r in rows) if "재고중량" in headers else 0

    return render_template(
    "in_up_preview.html",
    file_name=file.filename,
    headers=headers,   # 리스트
    rows=rows,         # 2차원 리스트
    total_qty=total_qty,
    total_weight=total_weight
)
@app.route("/customs")
def customs():
    sql = """
    SELECT
        x.cargo_no,
        x.vessel_name,
        x.bl_no,
        x.total_in_qty,
        x.total_in_weight,
        COALESCE(o.total_out_qty, 0) AS total_out_qty
    FROM (
        SELECT
            cargo_no,
            MAX(vessel_name) AS vessel_name,
            MAX(bl_no) AS bl_no,
            SUM(bundle_qty) AS total_in_qty,
            SUM(mt_weight) AS total_in_weight
        FROM in_d_bar
        WHERE cargo_no IS NOT NULL AND cargo_no <> ''
        GROUP BY cargo_no
    ) x
    LEFT JOIN (
        SELECT
            i.cargo_no,
            SUM(o.out_qty) AS total_out_qty
        FROM out_d_bar o
        JOIN in_d_bar i ON i.lot_no = o.lot_no
        WHERE i.cargo_no IS NOT NULL AND i.cargo_no <> ''
        GROUP BY i.cargo_no
    ) o ON o.cargo_no = x.cargo_no
    ORDER BY x.cargo_no
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    return render_template("customs.html", rows=rows)



# # 통관관리
# # 수입신고 통관등록 테이블
# with conn.cursor() as cur:
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS customs_d (
#             id BIGINT AUTO_INCREMENT PRIMARY KEY,

#             cargo_no VARCHAR(30) NOT NULL,
#             declaration_no VARCHAR(30) NOT NULL,
#             declaration_date DATETIME NOT NULL,

#             customs_qty DECIMAL(12,3) NOT NULL DEFAULT 0,
#             customs_qty_unit VARCHAR(10),

#             customs_weight_kg DECIMAL(14,3) NOT NULL DEFAULT 0,

#             customs_weight_mt DECIMAL(14,3)
#             GENERATED ALWAYS AS (
#                 customs_weight_kg / 1000
#             ) STORED,

#             warehouse_name VARCHAR(100),
#             remark VARCHAR(255),

#             created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
#             updated_at DATETIME NOT NULL
#                 DEFAULT CURRENT_TIMESTAMP
#                 ON UPDATE CURRENT_TIMESTAMP,

#             UNIQUE KEY uk_customs_declaration (
#                 cargo_no,
#                 declaration_no
#             ),

#             KEY idx_customs_cargo (cargo_no),
#             KEY idx_customs_date (declaration_date)
#         ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#     """)

#             CASE
#                 WHEN COALESCE(c.customs_weight_mt, 0) = 0
#                     THEN '미통관'

#                 WHEN c.customs_weight_mt < x.total_in_weight - 0.001
#                     THEN '부분통관'

#                 WHEN ABS(c.customs_weight_mt - x.total_in_weight) <= 0.001
#                     THEN '통관완료'

#                 ELSE '확인필요'
#             END AS customs_status


# if __name__ == "__main__":
#     # print(app.url_map)
#     app.run(host="127.0.0.1", port=5000, debug=True)


# 통관입력
# 통관 입력창 + 화물관리번호별 저장내역 조회
@app.route("/customs/input")
def customs_input():
    cargo_no = (request.args.get("cargo_no") or "").strip()

    sql = """
        SELECT
            id,
            declaration_date,
            declaration_no,
            customs_qty,
            customs_qty_unit,
            customs_weight_kg,
            customs_weight_mt,
            warehouse_name,
            remark
        FROM customs_d
        WHERE cargo_no = %s
        ORDER BY declaration_date DESC, id DESC
    """

    conn.ping(reconnect=True)

    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, (cargo_no,))
        customs_rows = cur.fetchall()

    return render_template(
        "customs_input.html",
        cargo_no=cargo_no,
        today=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        customs_rows=customs_rows
    )


@app.route("/customs/save", methods=["POST"])
def customs_save():
    cargo_no = (request.form.get("cargo_no") or "").strip()
    declaration_no = (
        request.form.get("declaration_no") or ""
    ).strip()

    declaration_date_text = (
        request.form.get("declaration_date") or ""
    ).strip()

    customs_qty_text = (
        request.form.get("customs_qty") or "0"
    ).replace(",", "").strip()

    customs_qty_unit = (
        request.form.get("customs_qty_unit") or "GT"
    ).strip().upper()

    customs_weight_text = (
        request.form.get("customs_weight_kg") or "0"
    ).replace(",", "").strip()

    warehouse_name = (
        request.form.get("warehouse_name") or ""
    ).strip()

    remark = (
        request.form.get("remark") or ""
    ).strip()

    # 필수값 확인
    if not cargo_no:
        return """
            <script>
                alert("화물관리번호가 없습니다.");
                history.back();
            </script>
        """

    if not declaration_no:
        return """
            <script>
                alert("수입신고번호를 입력하세요.");
                history.back();
            </script>
        """

    # 날짜 변환
    try:
        declaration_date = datetime.strptime(
            declaration_date_text,
            "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        return """
            <script>
                alert("수입신고일시는 2026-03-24 16:31:36 형식으로 입력하세요.");
                history.back();
            </script>
        """

    # 수량·중량 숫자 변환
    try:
        customs_qty = Decimal(customs_qty_text)
        customs_weight_kg = Decimal(customs_weight_text)

    except InvalidOperation:
        return """
            <script>
                alert("수량과 중량은 숫자로 입력하세요.");
                history.back();
            </script>
        """

    if customs_qty <= 0 or customs_weight_kg <= 0:
        return """
            <script>
                alert("수량과 중량은 0보다 커야 합니다.");
                history.back();
            </script>
        """

    sql = """
        INSERT INTO customs_d (
            cargo_no,
            declaration_date,
            declaration_no,
            customs_qty,
            customs_qty_unit,
            customs_weight_kg,
            warehouse_name,
            remark
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        conn.ping(reconnect=True)

        with conn.cursor() as cur:
            cur.execute(sql, (
                cargo_no,
                declaration_date,
                declaration_no,
                customs_qty,
                customs_qty_unit,
                customs_weight_kg,
                warehouse_name,
                remark
            ))

        conn.commit()

        return """
            <script>
                alert("수입신고 내역이 저장되었습니다.");

                if (window.opener && !window.opener.closed) {
                    window.opener.location.reload();
                }

                window.close();
            </script>
        """

    except pymysql.err.IntegrityError as e:
        conn.rollback()

        if e.args[0] == 1062:
            return """
                <script>
                    alert("이미 등록된 수입신고번호입니다.");
                    history.back();
                </script>
            """

        return f"""
            <script>
                alert("DB 저장 오류가 발생했습니다.");
                history.back();
            </script>
        """

    except Exception as e:
        conn.rollback()
        print("🔥 통관등록 저장 오류:", e)

        return """
            <script>
                alert("저장 중 오류가 발생했습니다.");
                history.back();
            </script>
        """



import threading, webbrowser, time, socket

def wait_and_open(url="http://127.0.0.1:8000", host="127.0.0.1", port=8000, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                webbrowser.open(url)
                return
        except OSError:
            time.sleep(0.2)

if __name__ == "__main__":
    threading.Thread(target=wait_and_open, daemon=True).start()
    app.run(host="127.0.0.1", port=8000, debug=False)