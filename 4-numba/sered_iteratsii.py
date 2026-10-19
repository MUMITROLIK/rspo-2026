"""Скільки роботи справді потрібно: середня кількість ітерацій на піксель (для пояснення, чому наївний NumPy повільний)."""
import numba_versiya as nv

r = nv.mandelbrot_numba(*nv.ARGS)
print("середнє ітерацій на піксель", r.mean(), "із", nv.m.MAX_ITER)
print("частка пікселів, що вилетіли за <= 10 ітерацій", (r <= 10).mean(), "; всередині множини", (r == nv.m.MAX_ITER).mean())
print("робота наївної / потрібна:", nv.m.MAX_ITER * r.size / r.sum())
