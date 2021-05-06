import sys
import json
import csv
import math

import objects
import slicedelay

DELTA_DELAY = 0.8


# сортируем слайсы в зависимости от требования к задержке
def sort_slices(slices, order):
    for key in slices.keys():
        pos = 0
        for i in range(0, len(order)):
            if slices[order[i]].qos_delay < slices[key].qos_delay:
                pos += 1
            else:
                break
        order.insert(pos, key)


# задаем начальные значения приоритетов и весов для виртуальных пластов на каждом коммутаторе
def set_initial_parameters(slices, slices_order, topology):
    # для каждого слайса создаем множество коммутаторов, через которое проходят потоки
    for sls in slices.keys():
        for flow in slices[sls].flows_list:
            for sw in flow.path:
                slices[sls].sls_sw_set.add(sw)
        # print(slices[sls].sls_sw_set)

    # для каждоко слайса в порядке slices_order на каждом коммутаторе из sls_sw_set
    # создаем очереди о объединяем их в приоритеты
    for sls in slices_order:
        for sw in slices[sls].sls_sw_set:
            # создаем очередь для слайса
            queue = objects.Queue(sls, slices[sls], 1, sw)
            if len(topology.switches[sw].priority_list) == 0:
                # создаем приоритет для слайса
                priority = objects.Priority(1, slices[sls].qos_throughput, slices[sls].qos_delay, queue)
                topology.switches[sw].priority_list.append(priority)
            else:
                was_added = False
                for pr in topology.switches[sw].priority_list:
                    if math.fabs(pr.mean_delay - slices[sls].qos_delay) < DELTA_DELAY:
                        was_added = True
                        # добавляем очередь в существующий приоритет
                        queue.priority = pr.priority
                        pr.queue_list.append(queue)
                        pr.throughput += slices[sls].qos_throughput
                        pr.recalculation()
                if not was_added:
                    # создаем новый приоритет и туда добавляем очередь
                    number = len(topology.switches[sw].priority_list) + 1
                    priority = objects.Priority(number, slices[sls].qos_throughput, slices[sls].qos_delay, queue)
                    topology.switches[sw].priority_list.append(priority)

    # print('Start queue organization:')
    # for sw in topology.switches.keys():
    #     print('----------- switch', sw, '------------------')
    #     for pr in topology.switches[sw].priority_list:
    #         print(pr.priority, ':', 'throughput =', pr.throughput, 'mean_delay =', pr.mean_delay)
    #         for queue in pr.queue_list:
    #             print('queue', queue.number, ': weight =', queue.weight, 'flows_number =', queue.flow_numbers)


# формируем кривую обслуживания на каждом коммутаторе для начальных параметров
def create_start_service_curve(slices, topology):
    print('create_start_service_curve')
    # TODO


# подбор корректных параметров для слайсов (основной алгоритм работы)
def modify_queue_parameters(slices, slices_order, topology):
    print('modify_queue_parameters')
    for sls_number in slices_order:
        sls_delay = slicedelay.calculate_slice_delay(sls_number, slices, topology)
    # TODO


# парсим конфиг файл и заполняем необходимы структуры
def parse_config(input_file, slices, topology):
    print('Start parsing input file', input_file)
    with open(input_file) as json_file:
        data = json.load(json_file)
        chi_square = data["chi_square"]

        # считываем топологию
        topo_data = data["topology"]
        for sw_number in topo_data["switches"]:
            sw = objects.Switch(sw_number)
            topology.switches[sw_number] = sw
        for lk in topo_data["links"]:
            topology.links.append(lk["link"])
            topology.switches[lk["link"][0]].physical_speed = lk["bandwidth"]

        # считываем слайсы
        for sls_data in data["slices"]:
            correct = True
            sls = objects.Slice(sls_data["sls_number"], sls_data["qos_throughput"], sls_data["qos_delay"])
            for fl in sls_data["flows"]:
                flow = objects.Flow(fl["epsilon"], fl["path"])
                if "statistic" in fl:
                    with open(fl["statistic"], 'r') as f:
                        reader = csv.reader(f)
                        stat_list = list(reader)
                    rate = topology.switches[flow.path[0]].physical_speed
                    flow.define_distribution(stat_list, chi_square, rate)
                    if flow.rho_a == 0 and flow.b_a == 0:
                        print("Reject slice installation")
                        correct = False
                        break
                else:
                    flow.rho_a = fl["rho_a"]
                    flow.b_a = fl["b_a"]
                sls.flows_list.append(flow)
            if correct:
                slices[sls.id] = sls


# записываем результаты работы в выходной файл
def write_result(output_file):
    print('write_result')
    # TODO


def main(argv):
    slices = dict()
    topology = objects.Topology()

    # парсим конфиг файл и заполняем необходимы структуры
    parse_config(argv[0], slices, topology)

    # сортируем слайсы в зависимости от требования к задержке
    slices_order = list()       # список номеров слайсов, упорядоченный по возрастанию задержки
    sort_slices(slices, slices_order)

    # задаем начальные значения приоритетов и весов для виртуальных пластов на каждом коммутаторе
    set_initial_parameters(slices, slices_order, topology)

    # формируем кривую обслуживания на каждом коммутаторе для начальных параметров
    create_start_service_curve(slices, topology)

    # подбор корректных параметров для слайсов
    modify_queue_parameters(slices, slices_order, topology)

    # записываем результаты работы в выходной файл
    write_result(argv[1])


if __name__ == "__main__":
    main(sys.argv[1:])
