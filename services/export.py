import csv
import io

from bson import json_util
from openpyxl import Workbook


def _collect_columns(rows):
    columns = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def _cell_value(value):
    if isinstance(value, (dict, list)):
        return json_util.dumps(value, ensure_ascii=False)
    return value


def to_csv_bytes(rows):
    columns = _collect_columns(rows)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for row in rows:
        writer.writerow({col: _cell_value(row.get(col, "")) for col in columns})
    return buffer.getvalue().encode("utf-8-sig")


def to_xlsx_bytes(rows):
    columns = _collect_columns(rows)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "resultado"
    sheet.append(columns)
    for row in rows:
        sheet.append([str(_cell_value(row.get(col, ""))) for col in columns])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def to_json_bytes(rows):
    return json_util.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")
