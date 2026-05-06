"""
💰 Finance Bot — Bot Telegram Pencatat Keuangan Pribadi
Fitur: Catat pemasukan/pengeluaran, saldo, riwayat, laporan, kategori otomatis.
Storage: Supabase (PostgreSQL gratis).
"""
import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from aiohttp import web
from db import (
    add_transaction, get_balance, get_history,
    delete_last, reset_all, get_report
)
from categories import detect_category, get_category_list


# =====================
# HELPER: FORMAT RUPIAH
# =====================
def fmt_rp(amount: int) -> str:
    """Format angka ke Rupiah: 5000000 -> Rp 5.000.000"""
    formatted = f"{abs(amount):,.0f}".replace(",", ".")
    return f"Rp {formatted}"


# =====================
# HELPER: SAFE REPLY
# =====================
async def safe_reply(message, text, **kwargs):
    """Kirim pesan dengan Markdown, fallback ke plain text jika gagal."""
    try:
        return await message.reply_text(text, parse_mode="Markdown", **kwargs)
    except Exception:
        try:
            clean = text.replace('`', '').replace('*', '').replace('_', '')
            return await message.reply_text(clean, **kwargs)
        except Exception as e2:
            return await message.reply_text(f"Error: {str(e2)[:100]}")


# =====================
# /start
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(
        update.message,
        "\U0001f4b0 *FINANCE BOT*\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "Bot pencatat keuangan pribadi.\n\n"
        "*Catat Transaksi:*\n"
        "\U0001f4b8 `/k 50000 makan siang`\n"
        "\U0001f4b5 `/m 5000000 gaji`\n\n"
        "*Lihat Data:*\n"
        "\U0001f4b0 `/saldo` — Saldo saat ini\n"
        "\U0001f4cb `/riwayat` — Riwayat transaksi\n"
        "\U0001f4c8 `/laporan bulan` — Laporan bulanan\n\n"
        "*Lainnya:*\n"
        "\U0001f5d1 `/hapus` — Hapus transaksi terakhir\n"
        "\U0001f3f7 `/kategori` — Daftar kategori\n"
        "\u267b\ufe0f `/reset` — Reset semua data\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
    )


# =====================
# /k atau /keluar
# =====================
async def keluar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "\u26a0\ufe0f Format: `/k 50000 makan siang`",
            parse_mode="Markdown"
        )
        return

    try:
        amount = int(context.args[0].replace(".", "").replace(",", ""))
    except ValueError:
        await update.message.reply_text("\u274c Nominal harus angka. Contoh: `/k 50000 makan`", parse_mode="Markdown")
        return

    if amount <= 0:
        await update.message.reply_text("\u274c Nominal harus lebih dari 0.")
        return

    description = " ".join(context.args[1:])
    category = detect_category(description)
    user_id = update.effective_user.id

    try:
        add_transaction(user_id, "keluar", amount, description, category)
    except Exception as e:
        await update.message.reply_text(f"\u274c Error database: {str(e)[:100]}")
        return

    balance = get_balance(user_id)

    await safe_reply(
        update.message,
        "\U0001f4b8 *PENGELUARAN DICATAT*\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f4b8 Nominal   : `{fmt_rp(amount)}`\n"
        f"\U0001f4dd Catatan   : `{description}`\n"
        f"\U0001f3f7 Kategori  : {category}\n"
        f"\U0001f4b0 Sisa Saldo: `{fmt_rp(balance['saldo'])}`\n"
        f"\U0001f552 Waktu     : `{datetime.now().strftime('%d/%m/%Y %H:%M')}`\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
    )


# =====================
# /m atau /masuk
# =====================
async def masuk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "\u26a0\ufe0f Format: `/m 5000000 gaji`",
            parse_mode="Markdown"
        )
        return

    try:
        amount = int(context.args[0].replace(".", "").replace(",", ""))
    except ValueError:
        await update.message.reply_text("\u274c Nominal harus angka. Contoh: `/m 5000000 gaji`", parse_mode="Markdown")
        return

    if amount <= 0:
        await update.message.reply_text("\u274c Nominal harus lebih dari 0.")
        return

    description = " ".join(context.args[1:])
    category = detect_category(description)
    user_id = update.effective_user.id

    try:
        add_transaction(user_id, "masuk", amount, description, category)
    except Exception as e:
        await update.message.reply_text(f"\u274c Error database: {str(e)[:100]}")
        return

    balance = get_balance(user_id)

    await safe_reply(
        update.message,
        "\U0001f4b5 *PEMASUKAN DICATAT*\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f4b5 Nominal   : `{fmt_rp(amount)}`\n"
        f"\U0001f4dd Catatan   : `{description}`\n"
        f"\U0001f3f7 Kategori  : {category}\n"
        f"\U0001f4b0 Saldo     : `{fmt_rp(balance['saldo'])}`\n"
        f"\U0001f552 Waktu     : `{datetime.now().strftime('%d/%m/%Y %H:%M')}`\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
    )


# =====================
# /saldo
# =====================
async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        bal = get_balance(user_id)
    except Exception as e:
        await update.message.reply_text(f"\u274c Error: {str(e)[:100]}")
        return

    # Emoji saldo
    if bal["saldo"] > 0:
        saldo_icon = "\U0001f7e2"
    elif bal["saldo"] < 0:
        saldo_icon = "\U0001f534"
    else:
        saldo_icon = "\u26aa"

    await safe_reply(
        update.message,
        "\U0001f4b0 *SALDO KAMU*\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f4b5 Total Masuk  : `{fmt_rp(bal['masuk'])}`\n"
        f"\U0001f4b8 Total Keluar : `{fmt_rp(bal['keluar'])}`\n"
        f"{saldo_icon} Saldo        : `{fmt_rp(bal['saldo'])}`\n"
        f"\U0001f552 Per tanggal  : `{datetime.now().strftime('%d/%m/%Y %H:%M')}`\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
    )


# =====================
# /riwayat
# =====================
async def riwayat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    limit = 10
    if context.args:
        try:
            limit = min(int(context.args[0]), 30)
        except ValueError:
            pass

    try:
        history = get_history(user_id, limit)
    except Exception as e:
        await update.message.reply_text(f"\u274c Error: {str(e)[:100]}")
        return

    if not history:
        await update.message.reply_text("\U0001f4ed Belum ada transaksi.")
        return

    lines = [f"\U0001f4cb *RIWAYAT TRANSAKSI* (terakhir {len(history)})\n"]

    for t in history:
        if t["type"] == "keluar":
            icon = "\U0001f534"
            sign = "-"
        else:
            icon = "\U0001f7e2"
            sign = "+"

        # Parse waktu
        try:
            dt = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
            time_str = dt.strftime("%d/%m %H:%M")
        except:
            time_str = "-"

        cat = t.get("category", "")
        cat_short = cat.split(" ")[0] if cat else ""

        lines.append(
            "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
            f"{icon} {sign}`{fmt_rp(t['amount'])}` {cat_short}\n"
            f"   {t.get('description', '-')} \u2022 _{time_str}_"
        )

    lines.append("\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")

    await safe_reply(update.message, "\n".join(lines))


# =====================
# /laporan
# =====================
async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    period = "bulan"
    if context.args:
        p = context.args[0].lower()
        if p in ("hari", "minggu", "bulan"):
            period = p

    try:
        report = get_report(user_id, period)
    except Exception as e:
        await update.message.reply_text(f"\u274c Error: {str(e)[:100]}")
        return

    if report["count"] == 0:
        await update.message.reply_text(f"\U0001f4ed Tidak ada transaksi untuk periode {period}.")
        return

    # Build bar chart kategori
    cat_lines = ""
    if report["categories"]:
        cat_lines = "\n\U0001f4ca *Pengeluaran per Kategori:*\n"
        max_amount = report["categories"][0][1] if report["categories"] else 1
        for cat, amount in report["categories"]:
            if report["total_keluar"] > 0:
                pct = int(amount / report["total_keluar"] * 100)
                bar_filled = int(amount / max_amount * 8)
                bar = "\u2588" * bar_filled + "\u2591" * (8 - bar_filled)
            else:
                pct = 0
                bar = "\u2591" * 8
            cat_lines += f"{cat}: `{fmt_rp(amount)}` {bar} {pct}%\n"

    # Rata-rata per hari
    if period == "bulan":
        day_of_month = datetime.now().day
        avg = report["total_keluar"] // max(day_of_month, 1)
        avg_line = f"\U0001f4c9 Rata-rata/hari : `{fmt_rp(avg)}`\n"
    elif period == "minggu":
        avg = report["total_keluar"] // 7
        avg_line = f"\U0001f4c9 Rata-rata/hari : `{fmt_rp(avg)}`\n"
    else:
        avg_line = ""

    await safe_reply(
        update.message,
        f"\U0001f4c8 *LAPORAN {period.upper()}*\n"
        f"\U0001f4c5 {report['label']}\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f4b5 Pemasukan     : `{fmt_rp(report['total_masuk'])}`\n"
        f"\U0001f4b8 Pengeluaran   : `{fmt_rp(report['total_keluar'])}`\n"
        f"\U0001f4b0 Sisa          : `{fmt_rp(report['saldo'])}`\n"
        f"{avg_line}"
        f"\U0001f4dd Total transaksi: `{report['count']}`\n"
        f"{cat_lines}"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
    )


# =====================
# /hapus
# =====================
async def hapus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    count = 1
    if context.args:
        try:
            count = min(int(context.args[0]), 10)
        except ValueError:
            pass

    try:
        deleted = delete_last(user_id, count)
    except Exception as e:
        await update.message.reply_text(f"\u274c Error: {str(e)[:100]}")
        return

    if deleted == 0:
        await update.message.reply_text("\U0001f4ed Tidak ada transaksi untuk dihapus.")
        return

    balance = get_balance(user_id)

    await safe_reply(
        update.message,
        "\U0001f5d1 *TRANSAKSI DIHAPUS*\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f5d1 Dihapus    : `{deleted} transaksi`\n"
        f"\U0001f4b0 Sisa Saldo : `{fmt_rp(balance['saldo'])}`\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
    )


# =====================
# /kategori
# =====================
async def kategori(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat_list = get_category_list()
    await safe_reply(
        update.message,
        "\U0001f3f7 *DAFTAR KATEGORI*\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"{cat_list}\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        "\U0001f4ac _Kategori terdeteksi otomatis dari keterangan._\n"
        "_Atau tambah manual: `/k 50000 makan #makanan`_"
    )


# =====================
# /reset
# =====================
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Konfirmasi dulu
    if not context.args or context.args[0].lower() != "yakin":
        await safe_reply(
            update.message,
            "\u26a0\ufe0f *RESET SEMUA DATA?*\n"
            "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
            "Semua transaksi akan dihapus permanen.\n\n"
            "Ketik `/reset yakin` untuk konfirmasi.\n"
            "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
        )
        return

    try:
        count = reset_all(user_id)
    except Exception as e:
        await update.message.reply_text(f"\u274c Error: {str(e)[:100]}")
        return

    await safe_reply(
        update.message,
        "\u2705 *DATA DIRESET*\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f5d1 Dihapus: `{count} transaksi`\n"
        "\U0001f4b0 Saldo  : `Rp 0`\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
    )


# =====================
# HEALTH SERVER (untuk Render)
# =====================
async def health_handler(request):
    return web.json_response({
        "status": "alive",
        "bot": "Finance Bot",
        "time": str(datetime.now())
    })

async def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    app = web.Application()
    app.router.add_get("/", health_handler)
    app.router.add_get("/health", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[HEALTH] Server running on port {port}", flush=True)


# =====================
# MAIN
# =====================
def main():
    TOKEN = os.environ.get("BOT_TOKEN", "8662317575:AAExeJIl7fK1A7vYqxW3AfV7N8PyT2aisos")

    if not TOKEN:
        print("[ERROR] BOT_TOKEN tidak di-set!", flush=True)
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # Command utama
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("k", keluar))
    app.add_handler(CommandHandler("keluar", keluar))
    app.add_handler(CommandHandler("m", masuk))
    app.add_handler(CommandHandler("masuk", masuk))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("riwayat", riwayat))
    app.add_handler(CommandHandler("laporan", laporan))
    app.add_handler(CommandHandler("hapus", hapus))
    app.add_handler(CommandHandler("kategori", kategori))
    app.add_handler(CommandHandler("reset", reset))

    async def startup(app):
        await start_health_server()
        print("[BOT] Finance Bot started!", flush=True)

    app.post_init = startup
    app.run_polling()


if __name__ == "__main__":
    main()
