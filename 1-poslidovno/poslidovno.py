"""Практична 02. Послідовна реалізація множини Мандельброта і її заміри.

Запуск:  py -3.12 poslidovno.py
Що входить у замір: обчислення всіх рядків зображення (без запису у файл).
Послідовна частина (збирання рядків у байти + запис PGM) міряється окремо.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mandelbrot as m

PAPKA = m.PAPKA
PROHONIV = 3


def poslidovno():
    return [m.ryadok(j) for j in range(m.H)]


def poslidovna_chastyna(rows):
    """Те, що не ділиться між ядрами: збирання результату і запис файлу."""
    m.zberehty_pgm(rows, PAPKA / "mandelbrot.pgm")


def main():
    print("Машина:", m.mashyna())
    print(f"Задача: Мандельброт {m.W}x{m.H}, max_iter={m.MAX_ITER}, прогонів={PROHONIV}")

    t_min, chasy, rows = m.zamir(poslidovno, prohoniv=PROHONIV)
    print("Обчислення, прогони, с:", [round(t, 3) for t in chasy])
    print(f"Мінімум: {t_min:.3f} с, розкид: {m.rozkid_vidsotkiv(chasy):.1f} %")

    # перший запуск створює еталон, наступні (і всі інші реалізації) з ним звіряються
    suma = m.kontrolna_suma(rows)
    if not m.ETALON_SHA256.exists():
        m.ETALON_SHA256.write_text(suma + "\n")
    m.perevirka(rows)

    s_min, s_chasy, _ = m.zamir(poslidovna_chastyna, rows, prohoniv=PROHONIV)
    chastka = s_min / (t_min + s_min) * 100
    print("Послідовна частина, прогони, с:", [round(t, 4) for t in s_chasy])
    print(f"Послідовна частина (мінімум): {s_min:.4f} с = {chastka:.2f} % від (обчислення + запис)")

    m.zberehty_png(rows, PAPKA / "mandelbrot.png")

    baza = {
        "mashyna": m.mashyna(),
        "zadacha": {"W": m.W, "H": m.H, "max_iter": m.MAX_ITER},
        "obchyslennya_prohony_s": chasy,
        "obchyslennya_min_s": t_min,
        "rozkid_vidsotkiv": m.rozkid_vidsotkiv(chasy),
        "poslidovna_prohony_s": s_chasy,
        "poslidovna_min_s": s_min,
        "poslidovna_chastka_vidsotkiv": chastka,
        "etalon_sha256": suma,
        "kolis": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (PAPKA / "baza.json").write_text(json.dumps(baza, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Збережено: mandelbrot.pgm, mandelbrot.png, baza.json")


if __name__ == "__main__":
    main()
