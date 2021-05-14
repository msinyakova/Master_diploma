# import numpy as np
import random
import sys


NUMBER = 50000
TIME_INTERVAL = 1


def main(argv):
    p_lambda = float(argv[0])
    output_file = open(argv[1], "w")
    t = 0.0
    count = 0
    current_time = 0
    for i in range(0, NUMBER):
        t += random.expovariate(p_lambda)
        # print(t)
        if t // TIME_INTERVAL == current_time:
            count += 1
        else:
            output_file.write(str(count) + '\n')
            current_time += 1
            while current_time != t // TIME_INTERVAL:
                output_file.write(str(0) + '\n')
                current_time += 1
            count = 1
    output_file.write(str(count) + '\n')
    output_file.close()


if __name__ == "__main__":
    main(sys.argv[1:])

# генерирует количество пакетов пришедших за интервал времени t
# количество измерений равно NUMbER
# ламда 20
# poisson = np.random.poisson(20, NUMBER)
# np.savetxt("poisson.csv", poisson, delimiter=",")
