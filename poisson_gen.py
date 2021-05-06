import numpy as np


# генерирует количество пакетов пришедших за интервал времени t
# количество измерений равно 100
# ламда 0.5
poisson = np.random.poisson(0.8, 5000)

np.savetxt("poisson.csv", poisson, delimiter=",")