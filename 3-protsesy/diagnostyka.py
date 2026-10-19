"""Діагностика: скільки процесорного часу потрібно воркеру на ОДНУ Й ТУ САМУ роботу,
коли поруч працюють 1, 6 або 12 процесів.

Кожен воркер рахує ті самі 40 рядків (300..339). Якщо процесорний час воркера росте
з кількістю процесів при незмінній роботі, то ядра стають повільнішими (частота,
спільні ресурси ядра при SMT, спільний кеш і пам'ять), а не просто «процеси заважають».

Запуск:  py -3.12 -u diagnostyka.py      (3 серії)   ->   diagnostyka_log.txt
"""
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "1-poslidovno"))
from mandelbrot import ryadok


def robota(k):
    c0, t0 = time.process_time(), time.perf_counter()
    for j in range(300, 340):
        ryadok(j)
    return k, time.perf_counter() - t0, time.process_time() - c0     # настінний, процесорний


def main():
    for seriya in (1, 2, 3):
        for n in (1, 6, 12):
            with ProcessPoolExecutor(max_workers=n) as ex:
                list(ex.map(abs, range(n)))          # прогрів: процеси стартували
                res = list(ex.map(robota, range(n), chunksize=1))
            cpu = [c for _, _, c in res]
            wall = [w for _, w, _ in res]
            print(f"серія {seriya}, процесів {n:>2}: процесорний час воркера (мін / середнє / макс), с: "
                  f"{min(cpu):.2f} / {sum(cpu) / n:.2f} / {max(cpu):.2f}   "
                  f"настінний (середнє): {sum(wall) / n:.2f}", flush=True)
        time.sleep(8)


if __name__ == "__main__":
    main()
