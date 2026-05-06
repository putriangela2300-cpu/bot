"""
Database layer menggunakan Supabase.
Semua operasi database ada di sini.
"""
import os
from datetime import datetime, timedelta
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

_client: Client = None


def get_client() -> Client:
    """Lazy init Supabase client."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL dan SUPABASE_KEY harus di-set!")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


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
    result = get_client().table("transactions").insert(data).execute()
    return result.data[0] if result.data else data


def get_balance(user_id: int) -> dict:
    """Hitung total masuk, keluar, dan saldo."""
    client = get_client()

    # Total masuk
    res_masuk = client.table("transactions") \
        .select("amount") \
        .eq("user_id", user_id) \
        .eq("type", "masuk") \
        .execute()
    total_masuk = sum(r["amount"] for r in res_masuk.data) if res_masuk.data else 0

    # Total keluar
    res_keluar = client.table("transactions") \
        .select("amount") \
        .eq("user_id", user_id) \
        .eq("type", "keluar") \
        .execute()
    total_keluar = sum(r["amount"] for r in res_keluar.data) if res_keluar.data else 0

    return {
        "masuk": total_masuk,
        "keluar": total_keluar,
        "saldo": total_masuk - total_keluar,
    }


def get_history(user_id: int, limit: int = 10) -> list:
    """Ambil riwayat transaksi terakhir."""
    result = get_client().table("transactions") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    return result.data or []


def delete_last(user_id: int, count: int = 1) -> int:
    """Hapus N transaksi terakhir. Return jumlah yang dihapus."""
    # Ambil ID transaksi terakhir
    items = get_client().table("transactions") \
        .select("id") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(count) \
        .execute()

    if not items.data:
        return 0

    deleted = 0
    for item in items.data:
        get_client().table("transactions") \
            .delete() \
            .eq("id", item["id"]) \
            .execute()
        deleted += 1

    return deleted


def reset_all(user_id: int) -> int:
    """Hapus semua transaksi user. Return jumlah yang dihapus."""
    items = get_client().table("transactions") \
        .select("id") \
        .eq("user_id", user_id) \
        .execute()

    if not items.data:
        return 0

    for item in items.data:
        get_client().table("transactions") \
            .delete() \
            .eq("id", item["id"]) \
            .execute()

    return len(items.data)


def get_report(user_id: int, period: str = "bulan") -> dict:
    """
    Ambil laporan per periode.
    period: 'hari', 'minggu', 'bulan'
    """
    now = datetime.now()

    if period == "hari":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label = f"Hari Ini ({now.strftime('%d/%m/%Y')})"
    elif period == "minggu":
        start = now - timedelta(days=7)
        label = f"7 Hari Terakhir"
    else:  # bulan
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label = f"Bulan {now.strftime('%B %Y')}"

    start_iso = start.isoformat()

    client = get_client()
    result = client.table("transactions") \
        .select("*") \
        .eq("user_id", user_id) \
        .gte("created_at", start_iso) \
        .order("created_at", desc=True) \
        .execute()

    transactions = result.data or []

    total_masuk = sum(t["amount"] for t in transactions if t["type"] == "masuk")
    total_keluar = sum(t["amount"] for t in transactions if t["type"] == "keluar")

    # Hitung per kategori
    categories = {}
    for t in transactions:
        if t["type"] == "keluar":
            cat = t.get("category", "\U0001f4e6 Lainnya")
            categories[cat] = categories.get(cat, 0) + t["amount"]

    # Sort kategori by amount descending
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    return {
        "label": label,
        "total_masuk": total_masuk,
        "total_keluar": total_keluar,
        "saldo": total_masuk - total_keluar,
        "categories": sorted_cats,
        "count": len(transactions),
    }
