class Queue:
    def __init__(self, number_):
        self.number = number_       # номер очереди == номеру слайса
        self.priority = 0           # приоритет очереди на коммутаторе
        self.weight = 0             # доля пропускной способности приоритета (omega)
        self.slice = 0              # указать на слайс, который передает в этой очереди
        self.rho_s = 0              # скорость для кривой обслуживания
        self.b_s = 0                # задержка для кривой обслуживания
        self.route_numbers = 0      # количество маршрутов слайса, проходящих через этот коммутатор


class Priority:
    def __init__(self, number_):
        self.priority = number_     # значение приоритета
        self.throughput = 0         # пропускная способность приоритета
        self.delay = 0              # суммарная задержка приоритета
        self.queue_list = list()    # список очередей, входящих в приоритет


class Switch:
    def __init__(self, speed_):
        self.priority_list = list()     # список приоритетов на коммутаторе
        self.physical_speed = speed_    # физическая пропускная способность канала


class Topology:
    def __init__(self):
        self.switches = list()      # список коммутаторов
        self.links = list()         # список каналов


class Flow:
    def __init__(self):
        self.rho_a = 0          # скорость поступления трафика (для кривой нагрузки)
        self.b_a = 0            # всплеск трафика (для кривой нагрузки)
        self.epsilon = 0        # вероятность ошибки оценки кривой нагрузки
        self.path = list()      # список коммутатор, через которые проходит поток


class Slice:
    def __init__(self, id_, throughput_, delay_):
        self.id = id_                       # номер слайса
        self.qos_throughput = throughput_   # требования к пропускной способности слайса
        self.qos_delay = delay_             # требования к задержке слайса
        self.flows_list = list()            # список маршрутов
