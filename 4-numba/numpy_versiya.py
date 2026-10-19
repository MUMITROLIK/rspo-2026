"""Практична 06. Векторизація NumPy: Мандельброт без циклу по пікселях.

Запуск:  py -3.12 -u numpy_versiya.py     ->   numpy_rezultaty.json

Дві версії:
  mandelbrot_numpy        - з інструкції: усі пікселі рахуються на кожній із MAX_ITER ітерацій,
                            вилетілі лише «заморожуються» через np.where (робота дарма);
  mandelbrot_numpy_maska  - з демо: вилетілі точки викидаються з масивів, масив щоітерації менший.
Сітка: `linspace(..., endpoint=True)` має той самий крок (X_MAX - X_MIN) / (W - 1), що й ядро
з тижня 2. `endpoint=False` дає крок / W і зсуває сітку: це перша пастка векторизації.
"""
import json
import sys
import time
from pathlib import Path
from time import perf_counter

import numpy as np

PAPKA = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPKA.parent / "1-poslidovno"))
import mandelbrot as m
from mandelbrot import H, MAX_ITER, W, zamir

PROHONIV = 5
PAUZA_S = 5


def sitka(endpoint):
    return np.meshgrid(np.linspace(m.X_MIN, m.X_MAX, W, endpoint=endpoint),
                       np.linspace(m.Y_MIN, m.Y_MAX, H, endpoint=endpoint))


def mandelbrot_numpy(endpoint=True):
    """Версія з інструкції (маска лише «заморожує» вилетілі точки)."""
    cx, cy = sitka(endpoint)
    zx = np.zeros((H, W))
    zy = np.zeros((H, W))
    out = np.full((H, W), MAX_ITER, dtype=np.int32)
    aktyvni = np.ones((H, W), dtype=bool)
    for n in range(MAX_ITER):
        zx_n = zx * zx - zy * zy + cx
        zy_n = 2.0 * zx * zy + cy
        zx = np.where(aktyvni, zx_n, zx)
        zy = np.where(aktyvni, zy_n, zy)
        vyletily = aktyvni & (zx * zx + zy * zy > 4.0)
        out[vyletily] = n + 1
        aktyvni &= ~vyletily
        if not aktyvni.any():
            break
    return out


def mandelbrot_numpy_maska(endpoint=True):
    """Версія з викиданням вилетілих точок: на кожній ітерації рахуємо лише ті, що ще живі."""
    cx, cy = sitka(endpoint)
    cxa = cx.ravel().copy()
    cya = cy.ravel().copy()
    zx = np.zeros(H * W)
    zy = np.zeros(H * W)
    idx = np.arange(H * W)
    out = np.full(H * W, MAX_ITER, dtype=np.int32)
    for n in range(MAX_ITER):
        zx_n = zx * zx - zy * zy + cxa
        zy = 2.0 * zx * zy + cya
        zx = zx_n
        vyletily = zx * zx + zy * zy > 4.0
        if vyletily.any():
            out[idx[vyletily]] = n + 1
            zhyvi = ~vyletily
            idx, zx, zy, cxa, cya = idx[zhyvi], zx[zhyvi], zy[zhyvi], cxa[zhyvi], cya[zhyvi]
            if idx.size == 0:
                break
    return out.reshape(H, W)


def poslidovno():
    return [m.ryadok(j) for j in range(H)]


def main():
    mashyna = m.mashyna()
    mashyna.update(numpy=np.__version__)
    print("Машина:", mashyna, flush=True)
    print(f"Задача: Мандельброт {W}x{H}, max_iter={MAX_ITER}, прогонів={PROHONIV}", flush=True)

    baza = json.loads((PAPKA.parent / "1-poslidovno" / "baza.json").read_text(encoding="utf-8"))
    t_baza = baza["obchyslennya_min_s"]
    res = {"mashyna": mashyna, "baza_tyzhden2_s": t_baza, "prohoniv": PROHONIV}

    t_seq, chasy_seq, rows = zamir(poslidovno, prohoniv=3)
    m.perevirka(rows)
    base = np.array(rows, dtype=np.int32)
    res["poslidovno_ce_zapusk"] = {"prohony": chasy_seq, "min": t_seq}
    print("послідовно (цей запуск)", [round(c, 3) for c in chasy_seq], "мінімум", round(t_seq, 3), flush=True)

    # ---- пастка 1: сітка без endpoint (лише підрахунок розбіжних точок, швидка версія) ----
    r_zle = mandelbrot_numpy_maska(endpoint=False)
    res["rozbizhnykh_endpoint_false"] = int((r_zle != base).sum())
    print(f"сітка endpoint=False: розбіжних точок {res['rozbizhnykh_endpoint_false']} із {base.size} "
          f"({res['rozbizhnykh_endpoint_false'] / base.size * 100:.2f} %)", flush=True)

    # ---- пастка 2: правильна сітка, але інша арифметика ----
    for nazva, fn in (("numpy_naivna", mandelbrot_numpy), ("numpy_maska", mandelbrot_numpy_maska)):
        time.sleep(PAUZA_S)
        t, chasy, r = zamir(fn, True, prohoniv=PROHONIV)
        rozb = int((r != base).sum())
        res[nazva] = {"prohony": chasy, "min": t, "pryskorennya_do_poslid_zapusku": t_seq / t,
                      "pryskorennya_do_bazy": t_baza / t, "rozbizhnykh_tochok": rozb}
        print(f"{nazva}: {[round(c, 3) for c in chasy]} мінімум {t:.3f} с; ×{t_seq / t:.2f} (до послід. запуску), "
              f"×{t_baza / t:.2f} (до бази 02); розбіжних точок {rozb}", flush=True)
        if rozb:
            ys, xs = np.nonzero(r != base)
            for y, x in list(zip(ys, xs))[:5]:
                print(f"    розбіжність: піксель (x={x}, y={y}): еталон {base[y, x]}, NumPy {r[y, x]}", flush=True)

    (PAPKA / "numpy_rezultaty.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Збережено numpy_rezultaty.json", flush=True)


if __name__ == "__main__":
    main()
