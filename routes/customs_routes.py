# from main import conn
# from db import get_db

# @app.route("/customs")
# def customs():
#     sql = """
#     SELECT
#         x.cargo_no,
#         x.vessel_name,
#         x.bl_no,
#         x.total_in_qty,
#         x.total_in_weight,
#         COALESCE(o.total_out_qty, 0) AS total_out_qty
#     FROM (
#         SELECT
#             cargo_no,
#             MAX(vessel_name) AS vessel_name,
#             MAX(bl_no) AS bl_no,
#             SUM(bundle_qty) AS total_in_qty,
#             SUM(mt_weight) AS total_in_weight
#         FROM in_d_bar
#         WHERE cargo_no IS NOT NULL AND cargo_no <> ''
#         GROUP BY cargo_no
#     ) x
#     LEFT JOIN (
#         SELECT
#             i.cargo_no,
#             SUM(o.out_qty) AS total_out_qty
#         FROM out_d_bar o
#         JOIN in_d_bar i ON i.lot_no = o.lot_no
#         WHERE i.cargo_no IS NOT NULL AND i.cargo_no <> ''
#         GROUP BY i.cargo_no
#     ) o ON o.cargo_no = x.cargo_no
#     ORDER BY x.cargo_no
#     """
#     with conn.cursor(pymysql.cursors.DictCursor) as cur:
#         cur.execute(sql)
#         rows = cur.fetchall()

#     return render_template("customs.html", rows=rows)
