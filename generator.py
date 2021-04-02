import sys
import json
import enum
import math
import random

T = 60
transmit = 0.5


# состояния событий
class State(enum.Enum):
    ARRIVAL = 1     # есть пакет на отправку
    SEND = 2        # освободился канал передачи


class Event:
    def __init__(self, state_, time_, packet_, number_):
        self.state = state_             # тип события ARRIVAL или SEND
        self.time = time_               # время наступления события
        self.packet = packet_           # 0 - если пакета на отправку нет, или пакет для передачи
        self.switch_number = number_    # номер коммутатора, на котором произошло событие


class Packet:
    def __init__(self, size_p, sls, start_t):
        self.size = size_p          # размер пакета
        self.slice = sls            # номер слайса, которому принадлежит пакет
        self.begin_time = start_t   # время поступления пакета в сеть
        self.end_time = 0           # время выхода пакета из сети
        self.virtual_end_time = 0   # виртуальное время окончания отправки пакета на коммутаторе


class Slice:
    def __init__(self, number_, lambda_, packet_size_, bandwidth_, path_):
        self.number = number_            # номер слайса
        self.p_lambda = lambda_          # интенсивность почтупления пакетов (параметр Пуассона)
        self.packet_size = packet_size_  # размер поступающих пакетов
        self.bandwidth = bandwidth_      # пропускная способность слайса
        self.path = path_                # маршрут передачи пакетов (последовательность линков)


class Queue:
    def __init__(self, priority_, number_, weight_):
        self.number = number_        # номер очереди
        self.weight = weight_        # вес очереди
        self.buffer = list()         # буфер с пакетами
        self.priority = priority_    # приориет

    # получение текущей заполненности буфера
    def size_of(self):
        return len(self.buffer)

    # получение пакета из очереди
    def pop(self):
        return self.buffer.pop(0)

    # положить пакет в очередь
    def push(self, packet):
        self.buffer.append(packet)


# вычисляем виртуальное время окончания отправки пакета
def calculate_virtual_end_time(queue, packet):
    # TODO
    start_time = 0  # max(F_i^(k-1), V(phisical_time_i))
    finish_time = start_time + packet.size / queue.weight
    return finish_time


class Switch:
    def __init__(self, id_, bandwidth_):
        self.id = id_                       # идентификатор коммутатора
        self.queues_info = dict()           # очереди на коммутаторе
        self.queues_send = list()           # пакеты на отправку, расположенные по приоритетам
        self.bandwidth = bandwidth_         # пропускная способность канала
        self.link_state = True              # состояние канала (занят передачей или свободен)
        self.slice_distribution = dict()    # соответствие слайсов и очередей
        self.next_switches = []             # следующие коммутаторы, на которые может быть отправлен пакет

    # по]ложить пакет в буфер очереди, которая закреплена за этим слайсом
    def push_packet_to_queue(self, queue_number, packet):
        # вычисляем вируальное время окончания отправки
        virtual_finish_time = calculate_virtual_end_time(self.queues_info[queue_number], packet)
        # получаем приоритет очереди на отправку
        priority = self.queues_info[queue_number].priority
        # print(priority, self.queues_send)
        # добавляем пакет в нужное место в списке ожидания на отправку
        packet.virtual_ebd_time = virtual_finish_time
        pos = 0
        for elem in self.queues_send[priority - 1]:
            if elem.virtual_end_time < virtual_finish_time:
                pos += 1
            else:
                break
        self.queues_send[priority - 1].insert(pos, packet)

    # получить пакет на передачу из первой непустой очереди
    def get_packet_for_transmit(self):
        for queue in self.queues_send:
            if len(queue) != 0:
                return queue.pop(0)
        return 0


class Time:
    def __init__(self):
        self.time_list = list()     # список событий
        self.pos = 0                # текущее положение указателя в списке событий

    # получить событие, которое находится по позиции pos
    def get_time(self):
        if self.pos == len(self.time_list):
            return 0
        event = self.time_list[self.pos]
        self.pos += 1
        return event

    # добавить новое событие в порядке возрастания времени
    def add_event(self, ev):
        i = 0
        if len(self.time_list) == 0:
            self.time_list.append(ev)
            return
        while i < len(self.time_list):
            if ev.time > self.time_list[i].time:
                i += 1
            else:
                break
        # print(i,':',ev.time,'-',self.time_list[i-1].time)
        self.time_list.insert(i, ev)


# TODO
class Statistics:
    def __init__(self):
        self.delay = list()


# заполняем все очерди на отправку пустыми списками (подготовка к симуляции)
def create_virtual_send(topology):
    for key in topology.keys():
        sw = topology[key]
        max_queue_priority = 0
        for queue_key in sw.queues_info.keys():
            if sw.queues_info[queue_key].priority > max_queue_priority:
                max_queue_priority = sw.queues_info[queue_key].priority
        for i in range(0, max_queue_priority):
            sw.queues_send.append(list())


# парсим входной файл
def parse_config(argv, slices, topology):
    print('Start parsing input file')
    with open(argv[0]) as json_file:
        data = json.load(json_file)

        # считываем слайсы
        slices_data = data['slices']
        for sls in slices_data:
            one_slice = Slice(sls['sls_number'], sls['lambda'], sls['packet_size'], sls['bandwidth'], sls['path'])
            slices[one_slice.number] = one_slice

        # заполняем топологию
        for sw in data['topology']['switches']:
            one_switch = Switch(sw['number'], sw['bandwidth'])

            # считываем очереди
            for qu in sw['queues']:
                one_queue = Queue(qu['priority'], qu['queue_number'], qu['weight'])
                # заполняем соответствие "слайс" - "очередь"
                for elem in qu['slices']:
                    one_switch.slice_distribution[elem] = one_queue.number
                # добавляем словарь с очередями "номер очереди" - "очередь"
                one_switch.queues_info[one_queue.number] = one_queue
            # заполняем топологию по формату "номер коммутатора" - "коммутатор"
            topology[one_switch.id] = one_switch

        # считываем каналы и устанавливаем связи между коммутаторами
        for lk in data['topology']['links']:
            topology[lk[0]].next_switches.append(lk[1])
            topology[lk[0]].links_state = True
    # формируем виртуальную очередь на отправку пакетов
    create_virtual_send(topology)
    print('Finish parsing file')


# генерация входящего потока в виде Пуассона
def generate(slices, event_time):
    print("Start generate")
    for key in slices.keys():
        sls = slices[key]
        packet_count = 1
        t = random.expovariate(sls.p_lambda)
        arrival_packet = Packet(sls.packet_size, sls.number, t)
        while t < T:
            # добавляем шейпинг
            if (packet_count * sls.packet_size) / t > sls.bandwidth:
                t += ((packet_count * sls.packet_size / sls.bandwidth) - t)
            print("sls_number", sls.number, "time = ", t)
            # добавляем событие в общий список событий
            event_time.add_event(Event(State.ARRIVAL, t, arrival_packet, sls.path[0][0]))
            # генерируем экспоненциальное значение временного интервала между событиями
            t += random.expovariate(sls.p_lambda)
    print("Finish generate")


# симуляция передачи, пока реализована на одном узле
def simulate(event_time, topology, stat):
    print('simulation')
    # берем первое событие из списка
    event = event_time.get_time()
    while event != 0:
        sw = topology[event.switch_number]
        print("time =", event.time, "switch =", sw.id)
        # если наступило событие окончания передачи пакета, освободи канал
        if event.state == State.SEND:
            sw.link_state = True

        # если пришет новый пакет, размести его в буфере соответствующей очереди
        if event.state == State.ARRIVAL and event.packet != 0:
            queue_number = sw.slice_distribution[event.packet.slice]
            sw.push_packet_to_queue(queue_number, event.packet)

        # если канал свободен, выполни передачу пакета
        if sw.link_state:
            # достаем пакет из очереди, которая имеет больший приоритет на передачу
            packet = sw.get_packet_for_transmit()
            # если нет пакета на передачу, то переходим к следующему событию
            if packet == 0:
                event = event_time.get_time()
                continue
            # вычисляем виртуальное время окончания отправки пакета
            duration = math.ceil(float(packet.size) / sw.bandwidth)
            # ставим флаг занятости канала передачи
            sw.link_state = False
            # добавляем новое событие на текущем коммутаторе
            event_time.add_event(Event(State.SEND, event.time + duration, 0, sw.id))
            # создаем событие на следующем коммутаторе
            if len(sw.next_switches) != 0:
                next_sw = sw.next_switches[0]
                event_time.add_event(Event(State.ARRIVAL, event.time + duration + transmit, event.packet, next_sw))
            else:
                stat.delay.append(event.time + duration - packet.begin_time)
        event = event_time.get_time()


# ----------------------------MAIN------------------------------------
def main(argv):
    slices = dict()
    topology = dict()
    stat = Statistics()

    # парсим конфиг файл и заполняем необходимы структуры
    parse_config(argv, slices, topology)

    # генерируем время прихода пакетов
    event_time = Time()
    generate(slices, event_time)

    # выполняем симуляцию отправки пакетов
    simulate(event_time, topology, stat)


if __name__ == "__main__":
    main(sys.argv[1:])
