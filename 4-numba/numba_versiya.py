"""Практична 06. Numba: @njit і @njit(parallel=True) + prange на задачі Мандельброта.

Запуск:  py -3.12 -u numba_versiya.py     ->   numba_rezultaty.json
Цикл той самий, що в `1-poslidovno/mandelbrot.py`, змінюється лише обгортка:
функція повертає масив H x W (int32), а не список рядків.

Що входить у замір: тільки виконання функції. Перший виклик = компіляція (JIT) міряється
ОКРЕМО і в замір не входить (cache=False, щоб компіляція справді відбулась у цьому процесі).
"""
import json
import sys
import time
from pathlib import Path
from time import perf_counter

import numba
import numpy as np
from numba import njit, prange

PAPKA = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPKA.parent / "1-poslidovno"))
import mandelbrot as m
from mandelbrot import zamir

PROHONIV = 5
PAUZA_S = 5


@njit
def mandelbrot_numba(W, H, MAX_ITER, X_MIN, DX, Y_MIN, DY):
    out = np.empty((H, W), dtype=np.int32)
    for j in range(H):
        cy = Y_MIN + j * DY
        for i in range(W):
            cx = X_MIN + i * DX
            x = 0.0
            y = 0.0
            n = 0
            while n < MAX_ITER and x * x + y * y <= 4.0:
                x, y = x * x - y * y + cx, 2.0 * x * y + cy
                n += 1
            out[j, i] = n
    return out


@njit(parallel=True)
def mandelbrot_prange(W, H, MAX_ITER, X_MIN, DX, Y_MIN, DY):
    out = np.empty((H, W), dtype=np.int32)
    for j in prange(H):                    # було range: ітерації незалежні, Numba роздає їх потокам
        cy = Y_MIN + j * DY
        for i in range(W):
            cx = X_MIN + i * DX
            x = 0.0
            y = 0.0
            n = 0
            while n < MAX_ITER and x * x + y * y <= 4.0:
                x, y = x * x - y * y + cx, 2.0 * x * y + cy
                n += 1
            out[j, i] = n
    return out


ARGS = (m.W, m.H, m.MAX_ITER, m.X_MIN, m.DX, m.Y_MIN, m.DY)


def poslidovno():
    return [m.ryadok(j) for j in range(m.H)]


def main():
    mashyna = m.mashyna()
    mashyna.update(numba=numba.__version__, numpy=np.__version__, numba_potokiv=numba.get_num_threads())
    print("Машина:", mashyna, flush=True)
    print(f"Задача: Мандельброт {m.W}x{m.H}, max_iter={m.MAX_ITER}, прогонів={PROHONIV}", flush=True)

    baza = json.loads((PAPKA.parent / "1-poslidovno" / "baza.json").read_text(encoding="utf-8"))
    t_baza = baza["obchyslennya_min_s"]
    res = {"mashyna": mashyna, "baza_tyzhden2_s": t_baza, "prohoniv": PROHONIV}

    # еталон: чистий Python цього запуску (3 прогони, довго)
    t_seq, chasy_seq, rows = zamir(poslidovno, prohoniv=3)
    m.perevirka(rows)
    base = np.array(rows, dtype=np.int32)
    res["poslidovno_ce_zapusk"] = {"prohony": chasy_seq, "min": t_seq}
    print("послідовно (цей запуск)", [round(c, 3) for c in chasy_seq], "мінімум", round(t_seq, 3), flush=True)

    for nazva, fn in (("njit", mandelbrot_numba), ("prange", mandelbrot_prange)):
        # 1) перший виклик = компіляція + одне виконання; міряємо окремо
        t0 = perf_counter()
        r0 = fn(*ARGS)
        t_pershyi = perf_counter() - t0
        assert np.array_equal(r0, base), "результат розійшовся з еталоном"
        # 2) прогрітa функція: звичайний замір
        time.sleep(PAUZA_S)
        t, chasy, r = zamir(fn, *ARGS, prohoniv=PROHONIV)
        assert np.array_equal(r, base), "результат розійшовся з еталоном"
        rozbizhnykh = int((r != base).sum())
        res[nazva] = {"pershyi_vyklyk_s": t_pershyi, "prohony": chasy, "min": t,
                      "pryskorennya_do_poslid_zapusku": t_seq / t, "pryskorennya_do_bazy": t_baza / t,
                      "rozbizhnykh_tochok": rozbizhnykh}
        print(f"@{nazva}: перший виклик (компіляція + виконання) {t_pershyi:.3f} с; "
              f"прогрітa {[round(c, 4) for c in chasy]} мінімум {t:.4f} с; "
              f"прискорення ×{t_seq / t:.1f} (до послід. запуску), ×{t_baza / t:.1f} (до бази 02); "
              f"розбіжних точок {rozbizhnykh}", flush=True)
    # оцінка чистої компіляції: перший виклик мінус прогрітий виклик
    for nazva in ("njit", "prange"):
        res[nazva]["kompilyatsiya_otsinka_s"] = res[nazva]["pershyi_vyklyk_s"] - res[nazva]["min"]
        print(f"компіляція @{nazva} ≈ {res[nazva]['kompilyatsiya_otsinka_s']:.3f} с", flush=True)

    # прскорення prange понад njit
    res["prange_nad_njit"] = res["njit"]["min"] / res["prange"]["min"]
    print(f"prange понад njit: ×{res['prange_nad_njit']:.2f}", flush=True)

    (PAPKA / "numba_rezultaty.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Збережено numba_rezultaty.json", flush=True)


if __name__ == "__main__":
    main()
