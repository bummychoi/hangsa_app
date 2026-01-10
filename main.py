from flask import Flask, render_template,jsonify,redirect,request,url_for
from datetime import datetime,timedelta
import pymysql

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
            out_qty INT NOT NULL,
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
            cur.execute('SELECT * FROM in_d_bar ORDER BY date_at DESC')
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
                    "date":row[11],
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
                        (o.out_qty * i.mt_weight) AS out_wt,
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
                        (o.out_qty * i.mt_weight) AS out_wt,
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

if __name__ == "__main__":
    print(app.url_map)
    app.run(host="127.0.0.1", port=8000, debug=True)

# if __name__ == "__main__":
#     import webbrowser
#     webbrowser.open("http://127.0.0.1:8000/list")  # 시작 페이지
#     app.run(host="127.0.0.1", port=8000)

