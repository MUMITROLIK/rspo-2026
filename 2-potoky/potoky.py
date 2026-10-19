"""Практична 03. Потоки і GIL: Мандельброт на потоках (обчислення) і 32 запити по 0,5 с (очікування).

Запуск:  py -3.12 -u potoky.py
Результати: potoky_rezultaty.json (для графіка і zamiry.md).
Що входить у замір: обчислення всіх рядків + створення і закриття пулу потоків
(`with ThreadPoolExecutor`), без запису файлу. Ядро, `zamir` і перевірка -
спільні з тижня 2 (`1-poslidovno/mandelbrot.py`).
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import perf_counter, process_time

PAPKA = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPKA.parent / "1-poslidovno"))
import mandelbrot as m
from mandelbrot import H, ryadok, zamir

PROHONIV = 3
POTOKY_OBCHYSLENNYA = (2, 4, 8, os.cpu_count())
POTOKY_OCHIKUVANNYA = (2, 4, 8, 16, 32)
ZAPYTIV = 32
PAUZA = 0.5


# ---- обчислення ----

def poslidovno():
    return [ryadok(j) for j in range(H)]


def potokamy(n):
    # ex.map повертає результати в порядку номерів рядків, а не в порядку завершення
    with ThreadPoolExecutor(max_workers=n) as ex:
        return list(ex.map(ryadok, range(H)))


def navantazhennya(fn, *a):
    """Процесорний час усіх потоків / настінний = скільки ядер працювало в середньому."""
    c0, t0 = process_time(), perf_counter()
    fn(*a)
    return (process_time() - c0) / (perf_counter() - t0)


# ---- очікування ----

def zapyt(nomer):
    time.sleep(PAUZA)        # «запит у мережу»: процесор вільний, GIL відпущено
    return nomer


def ochikuvannya_poslidovno():
    return [zapyt(i) for i in range(ZAPYTIV)]


def ochikuvannya_potokamy(n):
    with ThreadPoolExecutor(max_workers=n) as ex:
        return list(ex.map(zapyt, range(ZAPYTIV)))


def gil_uvimknenyi():
    return sys._is_gil_enabled() if hasattr(sys, "_is_gil_enabled") else True


def main():
    mashyna = m.mashyna()
    mashyna["gil_enabled"] = gil_uvimknenyi()
    print("Машина:", mashyna, flush=True)
    print(f"Задача: Мандельброт {m.W}x{m.H}, max_iter={m.MAX_ITER}, прогонів={PROHONIV}", flush=True)

    baza = json.loads((PAPKA.parent / "1-poslidovno" / "baza.json").read_text(encoding="utf-8"))
    t_baza = baza["obchyslennya_min_s"]
    print(f"База з тижня 2: {t_baza:.3f} с", flush=True)

    res = {"mashyna": mashyna, "baza_tyzhden2_s": t_baza}

    # ---------- обчислення ----------
    t_seq, chasy_seq, base = zamir(poslidovno, prohoniv=PROHONIV)
    m.perevirka(base)
    print("послідовно (цей запуск)", [round(c, 3) for c in chasy_seq], "мінімум", round(t_seq, 3),
          "відхилення від бази тижня 2:", f"{(t_seq / t_baza - 1) * 100:+.1f} %", flush=True)
    res["obchyslennya"] = {"poslidovno_ce_zapusk": {"prohony": chasy_seq, "min": t_seq}, "potoky": {}}

    for n in POTOKY_OBCHYSLENNYA:
        t, chasy, r = zamir(potokamy, n, prohoniv=PROHONIV)
        assert r == base, "результат розійшовся з послідовним"
        m.perevirka(r)
        res["obchyslennya"]["potoky"][n] = {"prohony": chasy, "min": t, "pryskorennya": t_baza / t}
        print("потоків", n, [round(c, 3) for c in chasy], "мінімум", round(t, 3),
              "прискорення", round(t_baza / t, 2), flush=True)

    res["obchyslennya"]["navantazhennya"] = {}
    for n in (8, os.cpu_count()):
        v = navantazhennya(potokamy, n)
        res["obchyslennya"]["navantazhennya"][n] = v
        print(f"процесорний / настінний, {n} потоків:", round(v, 2), flush=True)

    # ---------- очікування ----------
    chasy_o = []
    for _ in range(PROHONIV):
        t0 = perf_counter()
        base_o = ochikuvannya_poslidovno()
        chasy_o.append(perf_counter() - t0)
    t_base_o = min(chasy_o)
    print("очікування послідовно", [round(c, 3) for c in chasy_o], "мінімум", round(t_base_o, 3), flush=True)
    res["ochikuvannya"] = {"poslidovno": {"prohony": chasy_o, "min": t_base_o}, "potoky": {}}

    for n in POTOKY_OCHIKUVANNYA:
        t, chasy, r = zamir(ochikuvannya_potokamy, n, prohoniv=PROHONIV)
        assert r == base_o, "результат розійшовся з послідовним"
        res["ochikuvannya"]["potoky"][n] = {"prohony": chasy, "min": t, "pryskorennya": t_base_o / t}
        print("очікування, потоків", n, [round(c, 3) for c in chasy], "мінімум", round(t, 3),
              "прискорення", round(t_base_o / t, 1), flush=True)

    (PAPKA / "potoky_rezultaty.json").write_text(
        json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Збережено potoky_rezultaty.json", flush=True)


if __name__ == "__main__":
    main()
