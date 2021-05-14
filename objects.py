import math

CHI_SQUARE = [0.4549,  1.3863,  2.3660,  3.3567,  4.3515,  5.3481,  6.3458,  7.3441,  8.3428,  9.3418,
              10.3410, 11.3403, 12.3398, 13.3393, 14.3389, 15.3385, 16.3382, 17.3379, 18.3377, 19.3374,
              20.3372, 21.3370, 22.3369, 23.3367, 24.3366, 25.3365, 26.3363, 27.3362, 28.3361, 29.3360,
              30.3359, 31.3359, 32.3358, 33.3357, 34.3356, 35.3356, 36.3355, 37.3355, 38.3354, 39.3353,
              40.3353, 41.3352, 42.3352, 43.3352, 44.3351, 45.3351, 46.3350, 47.3350, 48.3350, 49.3349]


class Queue:
    def __init__(self, number_, slice_, priority_, sw):
        self.number = number_       # номер очереди == номеру слайса
        self.priority = priority_   # приоритет очереди на коммутаторе
        self.weight = 1.0           # доля пропускной способности приоритета (omega)
        self.slice = slice_         # указать на слайс, который передает в этой очереди
        self.rho_s = 0.0            # скорость для кривой обслуживания
        self.b_s = 0.0              # задержка для кривой обслуживания
        self.flow_numbers = 0       # количество маршрутов слайса, проходящих через этот коммутатор
        self.slice_lambda = 0.0     # lambda суммарная по всем потокам в слайсе
        self.add_flow_number(sw)
        self.find_slice_input_flow()

    def add_flow_number(self, sw):
        for flow in self.slice.flows_list:
            for elem in flow.path:
                if elem == sw:
                    self.flow_numbers += 1

    def find_slice_input_flow(self):
        for flow in self.slice.flows_list:
            self.slice_lambda += flow.rho_a


class Priority:
    def __init__(self, number_, throughput_, qos_delay_, queue):
        self.priority = number_                     # значение приоритета
        self.throughput = throughput_               # пропускная способность приоритета
        self.queue_list = [queue]                   # список очередей, входящих в приоритет
        self.mean_delay = qos_delay_                # среднее требование по задержка приоритета
        self.delay = 0.0                            # суммарная задержка приоритета
        self.priority_lambda = queue.slice_lambda   # lambda суммарная по всем очередям
        self.sigma_priority = 0.0                   # сумма нагрузок вышестоящих приоритетов
        self.slice_queue = dict()                   # соотношение номер сласа и очереди

    def recalculation(self):
        self.mean_delay = 0.0
        self.priority_lambda = 0.0
        required_throughput = 0.0
        for queue in self.queue_list:
            self.mean_delay += queue.slice.qos_delay
            required_throughput += queue.slice.qos_throughput
            self.priority_lambda += queue.slice_lambda
        self.mean_delay /= len(self.queue_list)
        for queue in self.queue_list:
            queue.weight = queue.slice.qos_throughput / required_throughput
            queue.rho_s = queue.weight * self.throughput


class Switch:
    def __init__(self, number_, speed_):
        self.number = number_           # номер коммутатора
        self.priority_list = list()     # список приоритетов на коммутаторе
        self.physical_speed = speed_    # физическая пропускная способность канала
        self.remaining_bandwidth = 0.0  # остаточная пропускная способность канала
        self.slice_priorities = dict()  # соотношение номера слайса и его приоритета


class Flow:
    def __init__(self, number_, eps_, path_):
        self.number = number_   # номер потока
        self.rho_a = 0.0        # скорость поступления трафика (для кривой нагрузки)
        self.b_a = 0.0          # всплеск трафика (для кривой нагрузки)
        self.epsilon = eps_     # вероятность ошибки оценки кривой нагрузки
        self.path = path_       # список коммутатор, через которые проходит поток

# формирование кривой нагрузки. На вход подается файл со статистикой,
# распределение хи квадрат и физическая скорость канала первого коммутатора в пути потока
    def define_distribution(self, stats, rate):
        # вычисляем сколько раз встречается каждое значение x_s
        x_s = dict()
        s = 0
        for st in stats:
            elem = int(float(st[0]))
            if x_s.get(elem, -1) != -1:
                x_s[elem] += 1
            else:
                x_s[elem] = 1
                s += 1

        # находим общее число элементов - sum_n и математическое ожидание sum_xn = sum(x_s * n_s)
        sum_n = sum_xn = 0
        for key in x_s.keys():
            sum_xn += key * x_s[key]
            sum_n += x_s[key]
        lambda_medium = sum_xn / sum_n
        # print('Poisson distribution with lambda = ', lambda_medium)
        # вычисляем вероятность p_s прихода элемента x_s, слагаемое Пирсона K_s и суммарное K
        k_sum = 0
        for key in x_s.keys():
            p_s = lambda_medium ** key / math.factorial(key) * math.exp(-lambda_medium)
            k_s = (x_s[key] - sum_n * p_s) ** 2 / sum_n * p_s
            k_sum += k_s
        if s - 1 >= len(CHI_SQUARE):
            self.rho_a = lambda_medium
            sigma_a = 0
            theta = 10000
            self.b_a = sigma_a - 1 / theta * (
                    math.log(self.epsilon) + math.log(1 - math.exp(-theta * (rate - self.rho_a))))
        else:
            # print('K_критическое = ', CHI_SQUARE[s - 1], ' K_наблюдаемое = ', k_sum)
            if CHI_SQUARE[s - 1] >= k_sum:
                self.rho_a = lambda_medium
                sigma_a = 0
                theta = 1000
                self.b_a = sigma_a - 1 / theta * (
                        math.log(self.epsilon) + math.log(1 - math.exp(-theta * (rate - self.rho_a))))
                # print('rho_a = ', self.rho_a, ' b_a = ', self.b_a)
            else:
                print('Not poisson distribution')
        # print('rho_a =', self.rho_a, 'b_a =', self.b_a)


class Slice:
    def __init__(self, id_, throughput_, delay_, packet_):
        self.id = id_                       # номер слайса
        self.qos_throughput = throughput_   # требования к пропускной способности слайса
        self.qos_delay = delay_             # требования к задержке слайса
        self.estimate_delay = 0.0           # оценка задержки
        self.flows_list = list()            # список маршрутов
        self.packet_size = packet_          # размер пакетов, передаваемых в слайсе
        self.sls_sw_set = set()             # множество коммутаторв, через которые проходят потоки слайса
        self.used_sw = set()                # множество коммутаторов из sls_sw_set, на которых уже нельзя изменить qos
        self.leaves = []                    # список всех вершин времен
        self.tree = 0                       # дерево связности времен
        self.route_time_constraints = []    # список временных неравенст для потока
