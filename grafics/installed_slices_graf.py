# соотношение количества занных виртуальных пластов к количеству установленных виртуальных пластов
import matplotlib.pyplot as plot

x = [a for a in range(1, 21)]
res = [1, 2, 3, 4, 4, 4, 6, 8, 9, 9, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20]

fig, ax = plot.subplots()
plot.xlabel('Количество заданных виртуальных пластов')
plot.ylabel('Среднее количество установленных виртуальных пластов')
# ax.plot(x, res, c='blue')
# ax.legend(loc='best')
plot.bar(x, res)
plot.xticks(x)
plot.savefig('install_slices_graf.png', dpi=300, bbox_inches='tight')
plot.show()
