"""Практична 04. Процеси і межа масштабування: Мандельброт на ProcessPoolExecutor.

Запуск:  py -3.12 -u protsesy.py      (обов'язково з терміналу, не з IDLE/Jupyter)
Результати: protsesy_rezultaty.json (для графіка і zamiry.md).

Що входить у замір: створення пулу + обчислення всіх рядків + збирання результату
від процесів (без запису файлу). Тобто вартість пулу ВХОДИТЬ у замір: це і є
реальна ціна процесів. Окремо міряється порожній пул.

Windows (spawn): увесь запуск під `if __name__ == "__main__"`, `ryadok` лежить
на верхньому рівні модуля, усе, що летить у процес і назад, копіюється через pickle.
"""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from time import perf_counter

PAPKA = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPKA.parent / "1-poslidovno"))
import mandelbrot as m
from mandelbrot import H, ryadok, zamir

PROHONIV = 3
CHUNKSIZE = 8
LOGICHNI = os.cpu_count()
# 1, 2, 4, 8, max - вимога практичної; 3, 6, 10 додано для ⭐3 (де ефективність падає нижче 80 %);
# 6 це кількість моїх фізичних ядер, тому важлива точка
KILKIST_PROTSESIV = (1, 2, 3, 4, 6, 8, 10, LOGICHNI)


def poslidovno():
    return [ryadok(j) for j in range(H)]


def protsesamy(n, chunksize=CHUNKSIZE):
    with ProcessPoolExecutor(max_workers=n) as ex:
        return list(ex.map(ryadok, range(H), chunksize=chunksize))


def porozhniy_pul(n):
    # pass дав би майже нуль: пул стартує процеси лише з першим завданням
    with ProcessPoolExecutor(max_workers=n) as ex:
        list(ex.map(abs, range(n)))      # кожен процес мусить реально стартувати


def main():
    mashyna = m.mashyna()
    print("Машина:", mashyna, flush=True)
    print(f"Задача: Мандельброт {m.W}x{m.H}, max_iter={m.MAX_ITER}, прогонів={PROHONIV}, "
          f"chunksize={CHUNKSIZE}", flush=True)

    baza = json.loads((PAPKA.parent / "1-poslidovno" / "baza.json").read_text(encoding="utf-8"))
    t_baza = baza["obchyslennya_min_s"]
    print(f"База з тижня 2: {t_baza:.3f} с", flush=True)
    res = {"mashyna": mashyna, "baza_tyzhden2_s": t_baza, "chunksize": CHUNKSIZE,
           "fizychni_yadra": 6, "logichni_yadra": LOGICHNI}

    # ---- контроль: послідовна версія в цьому запуску ----
    t_seq, chasy_seq, base = zamir(poslidovno, prohoniv=PROHONIV)
    m.perevirka(base)
    res["poslidovno_ce_zapusk"] = {"prohony": chasy_seq, "min": t_seq}
    print("послідовно (цей запуск)", [round(c, 3) for c in chasy_seq], "мінімум", round(t_seq, 3),
          f"відхилення від бази: {(t_seq / t_baza - 1) * 100:+.1f} %", flush=True)

    # ---- основна таблиця ----
    res["protsesy"] = {}
    for n in KILKIST_PROTSESIV:
        t, chasy, r = zamir(protsesamy, n, prohoniv=PROHONIV)
        assert r == base, "результат розійшовся з послідовним"
        m.perevirka(r)
        s = t_baza / t
        res["protsesy"][n] = {"prohony": chasy, "min": t, "pryskorennya": s, "efektyvnist": s / n}
        print("процесів", n, [round(c, 3) for c in chasy], "мінімум", round(t, 3),
              "прискорення", round(s, 2), "ефективність", round(s / n * 100), "%", flush=True)

    # ---- вартість порожнього пулу ----
    res["porozhniy_pul"] = {}
    for n in (1, 2, 6, LOGICHNI):
        t, chasy, _ = zamir(porozhniy_pul, n, prohoniv=PROHONIV)
        res["porozhniy_pul"][n] = {"prohony": chasy, "min": t}
        print("порожній пул,", n, "процесів:", [round(c, 3) for c in chasy], "мінімум", round(t, 3), "с", flush=True)

    # ---- ⭐1: chunksize на LOGICHNI процесах ----
    res["chunksize"] = {}
    for cs in (1, 8, 50, 200):
        t, chasy, r = zamir(protsesamy, LOGICHNI, cs, prohoniv=PROHONIV)
        assert r == base, "результат розійшовся з послідовним"
        res["chunksize"][cs] = {"prohony": chasy, "min": t, "pryskorennya": t_baza / t,
                                "shmatkiv": -(-H // cs)}
        print(f"chunksize {cs}: шматків {-(-H // cs)}", [round(c, 3) for c in chasy], "мінімум", round(t, 3),
              "прискорення", round(t_baza / t, 2), flush=True)

    # ---- ⭐2: процесів більше, ніж ядер ----
    res["bilshe_nizh_yader"] = {}
    for n in (2 * LOGICHNI,):
        t, chasy, r = zamir(protsesamy, n, prohoniv=PROHONIV)
        assert r == base, "результат розійшовся з послідовним"
        s = t_baza / t
        res["bilshe_nizh_yader"][n] = {"prohony": chasy, "min": t, "pryskorennya": s, "efektyvnist": s / n}
        print("процесів", n, [round(c, 3) for c in chasy], "мінімум", round(t, 3),
              "прискорення", round(s, 2), "ефективність", round(s / n * 100), "%", flush=True)

    (PAPKA / "protsesy_rezultaty.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Збережено protsesy_rezultaty.json", flush=True)


if __name__ == "__main__":
    main()
