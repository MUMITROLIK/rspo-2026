"""Спільне ядро задачі семестру: множина Мандельброта.

Цей модуль не змінюється до кінця семестру: усі реалізації (потоки, процеси,
Numba, GPU) беруть звідси ті самі параметри, ту саму функцію рядка,
той самий вимірювальний прилад `zamir` і ту саму перевірку правильності.
Інакше числа різних тижнів не можна порівнювати.

Одиниця роботи - один рядок зображення (не піксель): для процесів
пересилання одного пікселя коштувало б у сотні разів більше за саму роботу.
"""
import hashlib
import platform
import os
import sys
import time
import zlib
from array import array
from pathlib import Path

# ---- параметри задачі (однакові на весь семестр) ----
W, H = 1200, 800                  # розмір зображення, пікселів
MAX_ITER = 300                    # максимум ітерацій на піксель
X_MIN, X_MAX = -2.2, 0.8          # область комплексної площини
Y_MIN, Y_MAX = -1.0, 1.0
DX = (X_MAX - X_MIN) / (W - 1)
DY = (Y_MAX - Y_MIN) / (H - 1)

PAPKA = Path(__file__).resolve().parent
ETALON_SHA256 = PAPKA / "etalon.sha256"


def ryadok(j):
    """Порахувати рядок j: для кожного пікселя - скільки ітерацій витримав.

    Умова виходу x*x + y*y > 4 замість |z| > 2: те саме питання без кореня,
    а цикл найглибший, виконується мільйони разів.
    """
    cy = Y_MIN + j * DY
    rez = []
    for i in range(W):
        cx = X_MIN + i * DX
        x = 0.0
        y = 0.0
        n = 0
        while n < MAX_ITER and x * x + y * y <= 4.0:
            x, y = x * x - y * y + cx, 2.0 * x * y + cy
            n += 1
        rez.append(n)
    return rez


def zamir(fn, *args, prohoniv=3):
    """Виміряти fn(*args) через perf_counter. Повертає (мінімум, усі прогони, результат).

    Мінімум із прогонів - найближче до чистої вартості коду: шум
    (браузер, антивірус, частота процесора) час тільки додає.
    """
    chasy = []
    rez = None
    for _ in range(prohoniv):
        t0 = time.perf_counter()
        rez = fn(*args)
        chasy.append(time.perf_counter() - t0)
    return min(chasy), chasy, rez


def rozkid_vidsotkiv(chasy):
    """Розкид між прогонами, % від мінімуму: (максимум - мінімум) / мінімум * 100."""
    return (max(chasy) - min(chasy)) / min(chasy) * 100


# ---- збирання результату і запис (послідовна частина) ----

def zibraty_baity(rows):
    """Рядки з лічильниками ітерацій -> байти яскравості 0..255 (всередині множини чорне)."""
    buf = bytearray()
    for r in rows:
        buf.extend(0 if n == MAX_ITER else 255 * n // MAX_ITER for n in r)
    return bytes(buf)


def zberehty_pgm(rows, imya):
    """Записати зображення у файл PGM (P5): текстовий заголовок і байти пікселів."""
    data = zibraty_baity(rows)
    with open(imya, "wb") as f:
        f.write(f"P5\n{W} {H}\n255\n".encode("ascii"))
        f.write(data)


GAMMA_LUT = bytes(0 if n == MAX_ITER else int(255 * (n / MAX_ITER) ** 0.3) for n in range(MAX_ITER + 1))


def zberehty_png(rows, imya):
    """Те саме зображення у PNG (лише стандартна бібліотека), щоб відкривалося скрізь.

    Тільки для очей: яскравість із гамма-корекцією (інакше картинка майже чорна).
    Запис PGM, який міряється як послідовна частина, лишається лінійним.
    """
    data = bytes(GAMMA_LUT[n] for r in rows for n in r)
    raw = b"".join(b"\x00" + data[j * W:(j + 1) * W] for j in range(H))

    def chunk(tag, body):
        c = tag + body
        return len(body).to_bytes(4, "big") + c + zlib.crc32(c).to_bytes(4, "big")

    ihdr = W.to_bytes(4, "big") + H.to_bytes(4, "big") + bytes([8, 0, 0, 0, 0])
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    with open(imya, "wb") as f:
        f.write(png)


# ---- перевірка правильності ----

def kontrolna_suma(rows):
    """SHA-256 від усіх лічильників ітерацій (порядок рядків важливий)."""
    flat = array("H")
    for r in rows:
        flat.extend(r)
    return hashlib.sha256(flat.tobytes()).hexdigest()


def perevirka(rows):
    """Порівняти результат з еталоном (послідовною версією) за контрольною сумою.

    Ловить втрачений рядок, зсув на піксель і переплутаний порядок рядків
    (паралельна версія, що повертає в порядку завершення, а не запуску).
    """
    assert len(rows) == H and all(len(r) == W for r in rows), "неправильний розмір результату"
    etalon = ETALON_SHA256.read_text().strip()
    assert kontrolna_suma(rows) == etalon, "результат розійшовся з послідовним"


# ---- характеристики машини: перший рядок кожного звіту ----

def mashyna():
    return {
        "processor": platform.processor(),
        "logical_cores": os.cpu_count(),
        "python": sys.version.split()[0],
        "os": platform.platform(),
    }
