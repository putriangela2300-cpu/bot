"""
Database layer — Direct REST API ke Supabase (tanpa library supabase-py).
Lebih compatible dengan format key baru Supabase.
"""
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
REST_URL = f"{SUPABASE_URL}/rest/v1"


def _headers(prefer=None):
    """Build headers untuk Supabase REST API."""
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _request(method, path, data=None, params=None):
    """HTTP request ke Supabase REST API."""
    url = f"{REST_URL}/{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=_headers(
        prefer="return=representation" if method in ("POST", "DELETE") else None
    ), method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise Exception(f"Supabase error {e.code}: {error_body[:200]}")


# =====================
# TRANSAKSI
# =====================
def add_transaction(user_id: int, tipe: str, amount: int, description: str, category: str) -> dict:
    """Tambah transaksi baru."""
    data = {
        "user_id": user_id,
        "type": tipe,
        "amount": amount,
        "description": description,
        "category": category,
        "created_at": datetime.now().isoformat(),
    }
    result = _request("POST", "transactions", data=data)
    return result[0] if isinstance(result, list) and result else data


def get_balance(user_id: int) -> dict:
    """Hitung total masuk, keluar, dan saldo."""
    rows = _request("GET", "transactions", params={
        "user_id": f"eq.{user_id}",
        "select": "type,amount"
    })

    total_masuk = sum(r["amount"] for r in rows if r["type"] == "masuk")
    total_keluar = sum(r["amount"] for r in rows if r["type"] == "keluar")

    return {
        "masuk": total_masuk,
        "keluar": total_keluar,
        "saldo": total_masuk - total_keluar,
    }


def get_history(user_id: int, limit: int = 10) -> list:
    """Ambil riwayat transaksi terakhir."""
    return _request("GET", "transactions", params={
        "user_id": f"eq.{user_id}",
        "select": "*",
        "order": "created_at.desc",
        "limit": str(limit)
    })


def delete_last(user_id: int, count: int = 1) -> int:
    """Hapus N transaksi terakhir."""
    items = _request("GET", "transactions", params={
        "user_id": f"eq.{user_id}",
        "select": "id",
        "order": "created_at.desc",
        "limit": str(count)
    })

    if not items:
        return 0

    deleted = 0
    for item in items:
        _request("DELETE", "transactions", params={
            "id": f"eq.{item['id']}"
        })
        deleted += 1

    return deleted


def reset_all(user_id: int) -> int:
    """Hapus semua transaksi user."""
    items = _request("GET", "transactions", params={
        "user_id": f"eq.{user_id}",
        "select": "id"
    })

    if not items:
        return 0

    for item in items:
        _request("DELETE", "transactions", params={
            "id": f"eq.{item['id']}"
        })

    return len(items)


def get_report(user_id: int, period: str = "bulan") -> dict:
    """Ambil laporan per periode."""
    now = datetime.now()

    if period == "hari":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label = f"Hari Ini ({now.strftime('%d/%m/%Y')})"
    elif period == "minggu":
        start = now - timedelta(days=7)
        label = "7 Hari Terakhir"
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label = f"Bulan {now.strftime('%B %Y')}"

    transactions = _request("GET", "transactions", params={
        "user_id": f"eq.{user_id}",
        "created_at": f"gte.{start.isoformat()}",
        "select": "*",
        "order": "created_at.desc"
    })

    total_masuk = sum(t["amount"] for t in transactions if t["type"] == "masuk")
    total_keluar = sum(t["amount"] for t in transactions if t["type"] == "keluar")

    categories = {}
    for t in transactions:
        if t["type"] == "keluar":
            cat = t.get("category", "\U0001f4e6 Lainnya")
            categories[cat] = categories.get(cat, 0) + t["amount"]

    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    return {
        "label": label,
        "total_masuk": total_masuk,
        "total_keluar": total_keluar,
        "saldo": total_masuk - total_keluar,
        "categories": sorted_cats,
        "count": len(transactions),
    }
