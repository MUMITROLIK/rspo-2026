"""⭐1 (уточнення): скільки коштує пул потоків, коли потоки справді стартували.

`with ThreadPoolExecutor(16) as ex: pass` міряє майже нуль: потоки створюються
лише з першим завданням. Тому тут кожен потік мусить виконати завдання.
Запуск:  py -3.12 pul_potokiv.py   ->   pul_potokiv_rezultaty.json
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PAPKA = Path(__file__).resolve().parent
sys.path.insert(0, str(PAPKA.parent / "1-poslidovno"))
from mandelbrot import zamir


def pul_z_robotoyu(n):
    with ThreadPoolExecutor(max_workers=n) as ex:
        list(ex.map(abs, range(n)))


res = {}
for n in (2, 16):
    # прогонів багато: тривалість мікро-/мілісекунди, мінімум із 200 стабільніший за 3
    t, chasy, _ = zamir(pul_z_robotoyu, n, prohoniv=200)
    res[n] = {"min_s": t, "mediana_s": sorted(chasy)[len(chasy) // 2], "max_s": max(chasy)}
    print(f"пул потоків, {n} потоків стартують: мінімум {t * 1000:.3f} мс, "
          f"медіана {res[n]['mediana_s'] * 1000:.3f} мс, максимум {max(chasy) * 1000:.3f} мс")
(PAPKA / "pul_potokiv_rezultaty.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
