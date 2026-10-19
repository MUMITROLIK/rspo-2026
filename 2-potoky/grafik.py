"""Графік прискорення: дві криві на одному полотні (обчислення і очікування).

Бере числа з potoky_rezultaty.json (їх робить potoky.py), нічого не вигадує.
Запуск:  py -3.12 grafik.py   ->   grafik.png
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PAPKA = Path(__file__).resolve().parent
res = json.loads((PAPKA / "potoky_rezultaty.json").read_text(encoding="utf-8"))

ob = res["obchyslennya"]["potoky"]
ok = res["ochikuvannya"]["potoky"]
x_ob = [1] + [int(n) for n in ob]
y_ob = [1.0] + [ob[n]["pryskorennya"] for n in ob]
x_ok = [1] + [int(n) for n in ok]
y_ok = [1.0] + [ok[n]["pryskorennya"] for n in ok]

mash = res["mashyna"]
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x_ob, y_ob, "o-", label="обчислення (Мандельброт 1200×800)")
ax.plot(x_ok, y_ok, "s-", label="очікування (32 × 0,5 с)")
ax.plot([1, 32], [1, 32], ":", color="gray", label="ідеал ×N")
ax.set_xscale("log", base=2)
ax.set_yscale("log", base=2)
ax.set_xticks(x_ok)
ax.set_xticklabels([str(v) for v in x_ok])
ax.set_yticks([0.5, 1, 2, 4, 8, 16, 32])
ax.set_yticklabels(["0,5", "1", "2", "4", "8", "16", "32"])
ax.set_xlabel("кількість потоків")
ax.set_ylabel("прискорення, разів")
ax.set_title(f"Потоки, Python {mash['python']}, GIL "
             f"{'увімкнено' if mash['gil_enabled'] else 'вимкнено'}; "
             f"{mash['logical_cores']} логічних ядер")
ax.grid(True, alpha=0.3, which="both")
ax.legend()
fig.tight_layout()
fig.savefig(PAPKA / "grafik.png", dpi=120)
print("збережено grafik.png")
