"""
РСПО, практична 5. Виправлена копія zlamane.py (оригінал не змінено).

ЩО ЗМІНЕНО відносно zlamane.py:

  1. Додано спільний замок `zamok = mp.Lock()`, створюється в головному процесі
     й передається кожному процесу через args (новий процес не бачить змінних головного).
  2. Під замком (`with zamok:`) стоїть ОДНЕ ЗАМОВЛЕННЯ: перевірка залишку, списання,
     облік відвантаженого, а в гілці «не вистачає» ще й лічильник відмов.
     Усе це має відбутись «одним рухом»:
       - місце 1: `x.value = x.value + 1` це три дії (прочитати, додати, записати),
         між ними може втрутитись інший процес, і його внесок зникне;
       - місце 2: між `if zalyshok.value >= kilkist` і списанням залишок міг змінитись,
         тому перевірка й дія мусять бути під ОДНИМ замком, інакше два процеси
         одночасно побачать «вистачає» й спишуть удвічі (залишок піде в мінус).
  3. Поза замком лишилось те, що не торкається спільних даних: генерація замовлення
     (`rnd.randint`). Замок НЕ навколо всього циклу `for`: інакше процеси працювали б по черзі.
  4. Локальний лічильник `moi`: скільки відвантажив саме цей процес. Друкується наприкінці,
     щоб було видно, що всі процеси справді працювали (а не один за всіх).

ПАРАМЕТРИ можна змінити змінними середовища (за замовчуванням ті самі, що в оригіналі):
  RSPO_PROTSESIV, RSPO_ZAMOVLEN, RSPO_PROGONIV.

ЗАПУСК:  python vypravleno.py
"""

import multiprocessing as mp
import os
import platform
import random
import sys
import time

ZAPAS_POCHATKOVYI = 30_000
PROTSESIV = int(os.environ.get("RSPO_PROTSESIV", 4))
ZAMOVLEN_NA_PROTSES = int(os.environ.get("RSPO_ZAMOVLEN", 20_000))
MAX_U_ZAMOVLENNI = 3
PROGONIV = int(os.environ.get("RSPO_PROGONIV", 5))


def obrobyty_zamovlennya(zalyshok, vidvantazheno, vidmov, nasinnya, zamok, start):
    """Один робітник складу. Обробляє свою пачку замовлень."""
    rnd = random.Random(nasinnya)
    moi = 0                                   # скільки відвантажив саме цей процес

    # Барʼєр: на Windows процеси стартують по черзі (spawn, десятки-сотні мс кожен), і перший
    # встигає вичерпати весь запас, поки решта ще запускається (тоді розподіл 30000 / 0 / 0 / 0
    # виглядав би як «паралельність вимкнено», хоч замок тут ні до чого). Усі чекають одне одного
    # й починають цикл одночасно. На коректність інваріантів барʼєр не впливає.
    start.wait()

    for _ in range(ZAMOVLEN_NA_PROTSES):
        kilkist = rnd.randint(1, MAX_U_ZAMOVLENNI)      # не торкається спільних даних: поза замком

        with zamok:                           # критична секція: одне замовлення цілком
            # перевірка й списання під ОДНИМ замком
            if zalyshok.value >= kilkist:
                zalyshok.value = zalyshok.value - kilkist
                vidvantazheno.value = vidvantazheno.value + kilkist
                moi += kilkist
            else:
                vidmov.value = vidmov.value + 1

    print("             процес %d відвантажив %d" % (nasinnya, moi))


def pasport():
    print("=" * 68)
    print("УМОВИ ЗАПУСКУ")
    print("=" * 68)
    print("  Python        :", sys.version.split()[0])
    print("  процесор      :", platform.processor())
    print("  логічних ядер :", os.cpu_count())
    print("  ОС            :", platform.platform())
    print("  навантаження  : %d процесів x %d замовлень"
          % (PROTSESIV, ZAMOVLEN_NA_PROTSES))
    print()


def prognaty(nomer):
    zalyshok = mp.Value("i", ZAPAS_POCHATKOVYI)
    vidvantazheno = mp.Value("i", 0)
    vidmov = mp.Value("i", 0)
    zamok = mp.Lock()
    start = mp.Barrier(PROTSESIV)             # спільна стартова лінія (див. obrobyty_zamovlennya)

    procesy = [
        mp.Process(target=obrobyty_zamovlennya,
                   args=(zalyshok, vidvantazheno, vidmov, 1000 + i, zamok, start))
        for i in range(PROTSESIV)
    ]

    t0 = time.perf_counter()
    for p in procesy:
        p.start()
    for p in procesy:
        p.join()
    tryvalist = time.perf_counter() - t0

    z = zalyshok.value
    v = vidvantazheno.value
    vm = vidmov.value

    # ── перевірка інваріантів ──────────────────────────────────
    porushennya = []
    if z < 0:
        porushennya.append("залишок від'ємний: %d" % z)
    if v + z != ZAPAS_POCHATKOVYI:
        porushennya.append("баланс не сходиться: %d + %d = %d, а має бути %d"
                           % (v, z, v + z, ZAPAS_POCHATKOVYI))

    stan = "OK" if not porushennya else "ПОРУШЕНО"
    print("  прогін %d:  залишок %8d   відвантажено %8d   відмов %6d   "
          "%6.2f c   %s" % (nomer, z, v, vm, tryvalist, stan))
    for p in porushennya:
        print("             -> " + p)

    return not porushennya


if __name__ == "__main__":
    pasport()
    print("=" * 68)
    print("ПРОГОНИ.  Початковий запас:", ZAPAS_POCHATKOVYI)
    print("=" * 68)

    chysto = 0
    for i in range(1, PROGONIV + 1):
        if prognaty(i):
            chysto += 1

    print()
    print("=" * 68)
    print("  Без порушень: %d із %d" % (chysto, PROGONIV))
    print("=" * 68)
