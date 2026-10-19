"""Графік закону Амдала S(N) = 1 / (s + (1 - s) / N) для кількох s."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SHARES = [0.01, 0.05, 0.1]
NS = list(range(1, 1025))


def amdahl(s, n):
    return 1 / (s + (1 - s) / n)


fig, ax = plt.subplots(figsize=(8, 5))
for s in SHARES:
    ax.plot(NS, [amdahl(s, n) for n in NS], label=f"s = {s:g} (стеля ×{1 / s:g})")
ax.axvline(12, color="gray", linestyle="--", linewidth=1)
ax.text(13, 2, "N = 12 (мої логічні ядра)", color="gray")
ax.set_xscale("log", base=2)
ax.set_xlabel("кількість ядер N")
ax.set_ylabel("прискорення S(N)")
ax.set_title("Закон Амдала")
ax.grid(True, alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig("prognoz_amdahl.png", dpi=150)

for s in SHARES:
    print(f"s={s}: S(6)={amdahl(s, 6):.2f}  S(12)={amdahl(s, 12):.2f}  S(1024)={amdahl(s, 1024):.2f}")
