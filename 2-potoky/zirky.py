"""Практична 03, завдання зі зірочкою: ⭐1 вартість пулу, ⭐2 інтервал перемикання GIL, ⭐3 asyncio.

Запуск:  py -3.12 -u zirky.py   ->   zirky_rezultaty.json
Запускати окремо від potoky.py, коли машина вільна.
"""
import asyncio
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import perf_counter

PAPKA = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPKA.parent / "1-poslidovno"))
import mandelbrot as m
from mandelbrot import H, ryadok, zamir
from potoky import ZAPYTIV, PAUZA, ochikuvannya_potokamy

PROHONIV = 3


def porozhniy_pul(n):
    with ThreadPoolExecutor(max_workers=n) as ex:
        pass


def potokamy(n):
    with ThreadPoolExecutor(max_workers=n) as ex:
        return list(ex.map(ryadok, range(H)))


async def zapyt_async(i):
    await asyncio.sleep(PAUZA)
    return i


async def ochikuvannya_asyncio():
    # active_count міряємо всередині: скільки потоків живе, поки «запити» чекають
    zadachi = [zapyt_async(i) for i in range(ZAPYTIV)]
    potokiv_pid_chas = threading.active_count()
    return await asyncio.gather(*zadachi), potokiv_pid_chas


def asyncio_pryhid():
    return asyncio.run(ochikuvannya_asyncio())


def main():
    res = {}

    # ⭐1: скільки коштує пул
    t, chasy, _ = zamir(porozhniy_pul, 16, prohoniv=PROHONIV)
    res["pul_16_porozhniy"] = {"prohony": chasy, "min": t}
    print("порожній пул із 16 потоків", [f"{c * 1000:.2f} мс" for c in chasy], flush=True)

    # ⭐2: інтервал перемикання GIL, 8 потоків на обчисленнях
    res["setswitchinterval"] = {"za_zamovchuvannyam": sys.getswitchinterval()}
    for interval in (0.0001, 0.005, 0.1):
        sys.setswitchinterval(interval)
        t, chasy, _ = zamir(potokamy, 8, prohoniv=PROHONIV)
        res["setswitchinterval"][str(interval)] = {"prohony": chasy, "min": t}
        print(f"switchinterval {interval}: 8 потоків", [round(c, 3) for c in chasy], "мінімум", round(t, 3), flush=True)
    sys.setswitchinterval(res["setswitchinterval"]["za_zamovchuvannyam"])

    # ⭐3: очікування без потоків (asyncio)
    chasy_a = []
    n_potokiv = None
    for _ in range(PROHONIV):
        t0 = perf_counter()
        _, n_potokiv = asyncio_pryhid()
        chasy_a.append(perf_counter() - t0)
    res["asyncio"] = {"prohony": chasy_a, "min": min(chasy_a), "active_count": n_potokiv}
    print("asyncio, 32 × 0,5 с", [round(c, 3) for c in chasy_a], "threading.active_count() =", n_potokiv, flush=True)

    (PAPKA / "zirky_rezultaty.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Збережено zirky_rezultaty.json", flush=True)


if __name__ == "__main__":
    main()
