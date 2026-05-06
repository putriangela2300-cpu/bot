"""
Kategori otomatis untuk transaksi keuangan.
Bot mendeteksi kategori berdasarkan kata kunci di keterangan.
"""

CATEGORIES = {
    "\U0001f354 Makanan": [
        "makan", "nasi", "kopi", "coffee", "resto", "warteg", "indomie",
        "mie", "ayam", "bakso", "sate", "gorengan", "snack", "jajan",
        "sarapan", "lunch", "dinner", "breakfast", "es teh", "boba",
        "starbucks", "mcd", "kfc", "pizza", "roti", "lauk", "sayur",
        "buah", "minuman", "juice", "teh", "susu", "cemilan"
    ],
    "\U0001f697 Pengeluaran Lain": [
        "grab", "gojek", "uber", "bensin", "parkir", "tol", "bus",
        "kereta", "ojek", "taxi", "angkot", "transport", "bbm",
        "pertamax", "pertalite", "dollar", "arisan", "topup game", "mrt", "lrt"
    ],
    "\U0001f4f1 Komunikasi": [
        "pulsa", "wifi", "internet", "data", "kuota", "telkomsel",
        "indosat", "xl", "smartfren", "by.u", "paket data"
    ],
    "\U0001f3e0 Rumah": [
        "listrik", "air", "pdam", "kos", "kontrakan", "sewa", "rent",
        "pln", "token listrik", "gas", "laundry", "iuran"
    ],
    "\U0001f6d2 Belanja": [
        "belanja", "shopee", "tokopedia", "lazada", "beli", "baju",
        "celana", "sepatu", "tas", "toko", "market", "supermarket",
        "alfamart", "indomaret"
    ],
    "\U0001f48a Kesehatan": [
        "obat", "dokter", "apotek", "rumah sakit", "rs", "klinik",
        "vitamin", "supplement", "sakit", "berobat"
    ],
    "\U0001f3ae Hiburan": [
        "game", "film", "bioskop", "netflix", "spotify", "youtube",
        "nonton", "top up", "voucher", "liburan", "wisata", "tiket"
    ],
    "\U0001f4bc Pendapatan": [
        "gaji", "salary", "freelance", "bonus", "transfer masuk",
        "project", "bayaran", "komisi", "dividen", "cashback"
    ],
}

DEFAULT_CATEGORY = "\U0001f4e6 Lainnya"


def detect_category(description: str) -> str:
    """Deteksi kategori dari keterangan transaksi."""
    desc_lower = description.lower()

    # Cek hashtag manual dulu (#makanan, #transport, dll)
    for category, keywords in CATEGORIES.items():
        cat_name = category.split(" ", 1)[1].lower()
        if f"#{cat_name}" in desc_lower:
            return category

    # Auto-detect dari kata kunci
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return category

    return DEFAULT_CATEGORY


def get_category_list() -> str:
    """Return daftar kategori untuk ditampilkan."""
    lines = []
    for cat, keywords in CATEGORIES.items():
        sample = ", ".join(keywords[:5])
        lines.append(f"{cat}\n   _Contoh: {sample}_")
    lines.append(f"{DEFAULT_CATEGORY}\n   _Semua yang tidak terdeteksi_")
    return "\n".join(lines)
