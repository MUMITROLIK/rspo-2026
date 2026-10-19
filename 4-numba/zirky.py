"""Практична 06, завдання зі зірочкою.

⭐1 коли компіляція окупається (100×60); ⭐2 fastmath; ⭐3 NumPy проти Numba на матрицях 400×400;
⭐4 з якого розміру prange виграє.
Запуск:  py -3.12 -u zirky.py     ->   zirky_rezultaty.json
"""
import json
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
from numba import njit, prange

PAPKA = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPKA.parent / "1-poslidovno"))
import mandelbrot as m
from mandelbrot import MAX_ITER


def krok(velychyna, n):
    return (m.X_MAX - m.X_MIN) / (n - 1) if velychyna == "x" else (m.Y_MAX - m.Y_MIN) / (n - 1)


def python_chysto(W, H):
    dx, dy = krok("x", W), krok("y", H)
    rez = []
    for j in range(H):
        cy = m.Y_MIN + j * dy
        row = []
        for i in range(W):
            cx = m.X_MIN + i * dx
            x = y = 0.0
            n = 0
            while n < MAX_ITER and x * x + y * y <= 4.0:
                x, y = x * x - y * y + cx, 2.0 * x * y + cy
                n += 1
            row.append(n)
        rez.append(row)
    return np.array(rez, dtype=np.int32)


@njit
def k_njit(W, H, MAX_ITER, X_MIN, DX, Y_MIN, DY):
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
def k_prange(W, H, MAX_ITER, X_MIN, DX, Y_MIN, DY):
    out = np.empty((H, W), dtype=np.int32)
    for j in prange(H):
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


@njit(fastmath=True)
def k_fastmath(W, H, MAX_ITER, X_MIN, DX, Y_MIN, DY):
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


@njit
def matmul_njit(a, b):
    n = a.shape[0]
    c = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            s = 0.0
            for k in range(n):
                s += a[i, k] * b[k, j]
            c[i, j] = s
    return c


def args(W, H):
    return (W, H, MAX_ITER, m.X_MIN, krok("x", W), m.Y_MIN, krok("y", H))


def min_chas(fn, a, povtoriv):
    best = float("inf")
    for _ in range(povtoriv):
        t0 = perf_counter()
        fn(*a)
        best = min(best, perf_counter() - t0)
    return best


def main():
    res = {}

    # ---------- ⭐1: коли компіляція окупається ----------
    W, H = 100, 60
    a = args(W, H)
    t_py = min_chas(python_chysto, (W, H), 5)
    t0 = perf_counter()
    r0 = k_njit(*a)                                   # компіляція + виконання
    t_first = perf_counter() - t0
    t_njit = min_chas(k_njit, a, 200)
    assert np.array_equal(r0, python_chysto(W, H)), "100x60: розбіжність з чистим Python"
    kompilyatsiya = t_first - t_njit
    vyklykiv = kompilyatsiya / (t_py - t_njit)
    res["zirka1"] = {"rozmir": [W, H], "python_s": t_py, "njit_s": t_njit, "pershyi_vyklyk_s": t_first,
                     "kompilyatsiya_s": kompilyatsiya, "vyklykiv_shchob_okupylos": vyklykiv}
    print(f"⭐1 {W}x{H}: чистий Python {t_py * 1000:.2f} мс, @njit {t_njit * 1000:.3f} мс, перший виклик "
          f"{t_first:.3f} с, компіляція ≈ {kompilyatsiya:.3f} с => окупається за {vyklykiv:.0f} викликів", flush=True)
    # на робочому розмірі: Python 8.5 с, njit 0.169 с: компіляція окупається вже в першому виклику
    t_py_big, t_njit_big = 8.492, 0.1688       # з numba_log.txt того ж дня (чистий Python і @njit, 1200x800)
    res["zirka1"]["na_1200x800_vyklykiv"] = kompilyatsiya / (t_py_big - t_njit_big)
    print(f"   на 1200x800 (Python {t_py_big} с, @njit {t_njit_big} с): {res['zirka1']['na_1200x800_vyklykiv']:.2f} виклику",
          flush=True)

    # ---------- ⭐2: fastmath ----------
    base = k_njit(*args(m.W, m.H))
    k_fastmath(*args(m.W, m.H))                       # компіляція
    t_fm = min_chas(k_fastmath, args(m.W, m.H), 5)
    t_nj = min_chas(k_njit, args(m.W, m.H), 5)
    r_fm = k_fastmath(*args(m.W, m.H))
    rozb = int((r_fm != base).sum())
    res["zirka2"] = {"njit_s": t_nj, "fastmath_s": t_fm, "rozbizhnykh_tochok": rozb}
    print(f"⭐2 @njit {t_nj:.4f} с, fastmath {t_fm:.4f} с (×{t_nj / t_fm:.2f}); розбіжних точок {rozb} із {base.size}", flush=True)

    # ---------- ⭐3: матриці 400x400 ----------
    rng = np.random.default_rng(0)
    A = rng.random((400, 400))
    B = rng.random((400, 400))
    matmul_njit(A, B)                                  # компіляція
    t_np = min_chas(lambda x, y: x @ y, (A, B), 20)
    t_nb = min_chas(matmul_njit, (A, B), 5)
    maxrizn = float(np.abs(A @ B - matmul_njit(A, B)).max())
    res["zirka3"] = {"numpy_s": t_np, "njit_s": t_nb, "max_riznytsya": maxrizn}
    print(f"⭐3 400x400: NumPy a@b {t_np * 1000:.2f} мс, @njit потрійний цикл {t_nb * 1000:.1f} мс (NumPy швидший у "
          f"{t_nb / t_np:.0f} разів); макс. різниця {maxrizn:.2e}", flush=True)

    # ---------- ⭐4: з якого розміру prange виграє ----------
    k_prange(*args(300, 200))                          # компіляція prange
    res["zirka4"] = []
    print("⭐4 розмір, @njit, prange, prange/njit:", flush=True)
    for W, H in ((2, 2), (4, 3), (10, 6), (30, 20), (300, 200), (1200, 800)):
        a = args(W, H)
        povt = 3000 if W * H < 100 else 300 if W * H < 1000 else 30 if W * H < 100000 else 5
        t1 = min_chas(k_njit, a, povt)
        t2 = min_chas(k_prange, a, povt)
        res["zirka4"].append({"rozmir": [W, H], "njit_s": t1, "prange_s": t2, "povtoriv": povt})
        print(f"   {W}x{H}: {t1 * 1e6:.1f} мкс, {t2 * 1e6:.1f} мкс, prange {'швидший' if t2 < t1 else 'повільніший'} "
              f"(×{t1 / t2:.2f})", flush=True)

    (PAPKA / "zirky_rezultaty.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Збережено zirky_rezultaty.json", flush=True)


if __name__ == "__main__":
    main()
