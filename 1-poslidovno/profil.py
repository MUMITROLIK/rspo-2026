"""Профіль послідовної версії: cProfile, вивід у profil.txt (сортування за tottime).

Профіль сповільнює програму (службові дії на кожен виклик), тому його час
не є результатом заміру - з нього беремо лише пропорції: хто скільки з'їв.
Запуск:  py -3.12 profil.py
"""
import cProfile
import io
import pstats
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mandelbrot as m
from poslidovno import poslidovno


def main():
    pr = cProfile.Profile()
    pr.enable()
    rows = poslidovno()
    pr.disable()
    m.perevirka(rows)

    buf = io.StringIO()
    buf.write("Профіль послідовної версії (cProfile, один прогін, сортування за tottime)\n")
    buf.write(f"Машина: {m.mashyna()}\n")
    buf.write(f"Задача: {m.W}x{m.H}, max_iter={m.MAX_ITER}\n\n")
    pstats.Stats(pr, stream=buf).sort_stats("tottime").print_stats(8)
    text = buf.getvalue()
    (m.PAPKA / "profil.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
