"""Графік практичної 04: ліворуч прискорення (з лінією ідеалу ×N), праворуч ефективність.

Числа беруться з protsesy_rezultaty.json (його робить protsesy.py).
Запуск:  py -3.12 grafik.py   ->   grafik.png
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PAPKA = Path(__file__).resolve().parent
res = json.loads((PAPKA / "protsesy_rezultaty.json").read_text(encoding="utf-8"))
pr = res["protsesy"]
fiz, log = res["fizychni_yadra"], res["logichni_yadra"]

n = [int(k) for k in pr]
s = [pr[k]["pryskorennya"] for k in pr]
e = [pr[k]["efektyvnist"] * 100 for k in pr]
mash = res["mashyna"]

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4))
a1.plot(n, s, "o-", label="виміряне")
a1.plot([1, log], [1, log], "--", color="gray", label="ідеал ×N")
a1.axvline(fiz, color="tab:red", linestyle=":", label=f"{fiz} фізичних ядер")
a1.set_xlabel("процесів")
a1.set_ylabel("прискорення, разів")
a1.set_title("Прискорення")
a1.set_xticks(n)
a1.grid(True, alpha=0.3)
a1.legend()

a2.plot(n, e, "s-", color="tab:orange")
a2.axhline(80, color="gray", linestyle="--", linewidth=1)
a2.text(n[-1], 81, "80 %", ha="right", color="gray")
a2.axvline(fiz, color="tab:red", linestyle=":")
a2.set_xlabel("процесів")
a2.set_ylabel("ефективність, %")
a2.set_title("Ефективність = прискорення / N")
a2.set_ylim(0, 110)
a2.set_xticks(n)
a2.grid(True, alpha=0.3)

fig.suptitle(f"Процеси, Python {mash['python']}, {fiz} фізичних / {log} логічних ядер, "
             f"Мандельброт 1200×800, chunksize={res['chunksize']}")
fig.tight_layout()
fig.savefig(PAPKA / "grafik.png", dpi=110)
print("збережено grafik.png")
