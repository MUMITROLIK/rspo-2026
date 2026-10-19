"""Друкує таблиці для zamiry.md / vysnovky.md з protsesy_rezultaty.json (нічого не вигадує)."""
import json
from pathlib import Path

res = json.loads((Path(__file__).resolve().parent / "protsesy_rezultaty.json").read_text(encoding="utf-8"))
t_seq = res["poslidovno_ce_zapusk"]["min"]
t_baza = res["baza_tyzhden2_s"]
print(f"послідовно в цьому запуску: {[round(x, 3) for x in res['poslidovno_ce_zapusk']['prohony']]} мін {t_seq:.3f}; база тижня 2 {t_baza:.3f}\n")

print("| процесів | прогони, с | мін, с | прискорення (до послід. запуску) | ефективність | прискорення (до бази тижня 2) |")
print("|---|---|---|---|---|---|")
for k, v in res["protsesy"].items():
    n = int(k)
    pr = ' / '.join(f'{x:.2f}' for x in v['prohony'])
    print(f"| {n} | {pr} | **{v['min']:.3f}** | ×{t_seq / v['min']:.2f} | {t_seq / v['min'] / n * 100:.0f} % | ×{t_baza / v['min']:.2f} |")

print("\nпорожній пул:")
for k, v in res["porozhniy_pul"].items():
    srd = sorted(v["prohony"])[len(v["prohony"]) // 2]
    print(f"  {k} процесів: мін {v['min']:.3f}, медіана {srd:.3f}, прогони {[round(x, 3) for x in v['prohony']]}")

print("\nchunksize на 12 процесах:")
for k, v in res["chunksize"].items():
    print(f"  chunksize {k} ({v['shmatkiv']} шматків): мін {v['min']:.3f}, прискорення ×{t_seq / v['min']:.2f}, прогони {[round(x, 2) for x in v['prohony']]}")

print("\nпроцесів більше, ніж ядер:")
for k, v in res["bilshe_nizh_yader"].items():
    print(f"  {k} процесів: мін {v['min']:.3f}, прискорення ×{t_seq / v['min']:.2f}, ефективність {t_seq / v['min'] / int(k) * 100:.0f} %")
