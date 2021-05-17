# соотношение трех видов задержек (qos_delay, estimate_delay, simulation_delay) для 10-ти слайсов
import matplotlib.pyplot as plot

file = open("result", 'r')
text = file.readlines()

x = [a for a in range(1, 21)]
res_qos = [0.0 for m in range(1, 21)]
res_math = [0.0 for j in range(1, 21)]
res_sim = [0.0 for k in range(1, 21)]

i = 0
while i < len(text) - 1:
    sim_str = text[i].split()
    qos_str = text[i+1].split()
    math_str = text[i+2].split()
    # print(int(sim_str[3]), float(sim_str[len(sim_str) - 1]))
    res_sim[int(sim_str[3]) - 1] = float(sim_str[len(sim_str) - 1])
    res_qos[int(sim_str[3]) - 1] = float(qos_str[len(qos_str) - 1])
    res_math[int(sim_str[3]) - 1] = float(math_str[len(math_str) - 1])
    i += 5


fig, ax = plot.subplots()
plot.title('Соотношения задержек для 20-ти виртуальых пластов')
plot.xlabel('Номер виртуального пласта')
plot.ylabel('Задержка, (с)')
ax.plot(x, res_qos, c='g', linestyle='--', marker='.', label='Требование задержки')
ax.plot(x, res_math, c='c', linestyle='-', marker='.', label='Математическая оценка задержки')
ax.plot(x, res_sim, c='b', linestyle=':', marker='.', label='Задрежка симуляции')
ax.legend(loc='best')
ax.axvline(x=6.5, c='red', linestyle='--')
ax.axvline(x=13.5, c='red', linestyle='--')
plot.savefig('all_delays_graf.png', dpi=300, bbox_inches='tight')
plot.show()
