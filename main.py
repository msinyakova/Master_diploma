import sys
import json
import csv
import math

import objects
import algorithm
import mytopology
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


# печатаем параметры устройства очередей на коммутаторах
def print_queue_organization(topology):
    print('Queue organization:')
    for sw in topology.switches.keys():
        print('----------- switch', sw, '------------------')
        for pr in topology.switches[sw].priority_list:
            print('priority', pr.priority, ':', 'throughput =', pr.throughput,
                  'mean_delay =', pr.mean_delay, 'delay = ', pr.delay)
            for queue in pr.queue_list:
                print('\t queue', queue.number, ': weight =', queue.weight, 'rho_s =', queue.rho_s,
                      'b_s =', queue.b_s, 'flows_number =', queue.flow_numbers)


# для каждого слайса создаем множество коммутаторов, через которое проходят потоки
def build_slice_cross_switches_set(slices):
    for sls in slices.keys():
        for flow in slices[sls].flows_list:
            for sw in flow.path:
                slices[sls].sls_sw_set.add(sw)
        # print(slices[sls].sls_sw_set)


# для каждоко слайса в порядке возрастания требований к задержке на каждом коммутаторе из множества коммутаторов,
# через которое проходят потоки слайса, создаем очереди и объединяем их в приоритеты
def create_queue_start_organization(slices, slices_order, topology):
    for sls in slices_order:
        for sw in slices[sls].sls_sw_set:
            # создаем очередь для слайса
            queue = objects.Queue(sls, slices[sls], 1, sw)
            if len(topology.switches[sw].priority_list) == 0:
                # создаем приоритет для слайса
                priority = objects.Priority(1, slices[sls].qos_throughput, slices[sls].qos_delay, queue)
                priority.slice_queue[sls] = queue
                queue.rho_s = queue.weight * priority.throughput
                topology.switches[sw].priority_list.append(priority)
                topology.switches[sw].slice_priorities[sls] = priority.priority
            else:
                was_added = False
                for pr in topology.switches[sw].priority_list:
                    if math.fabs(pr.mean_delay - slices[sls].qos_delay) < DELTA_DELAY:
                        was_added = True
                        # добавляем очередь в существующий приоритет
                        queue.priority = pr.priority
                        pr.queue_list.append(queue)
                        pr.slice_queue[sls] = queue
                        pr.throughput += slices[sls].qos_throughput
                        pr.recalculation()
                        topology.switches[sw].slice_priorities[sls] = pr.priority
                if not was_added:
                    # создаем новый приоритет и туда добавляем очередь
                    number = len(topology.switches[sw].priority_list) + 1
                    priority = objects.Priority(number, slices[sls].qos_throughput, slices[sls].qos_delay, queue)
                    priority.slice_queue[sls] = queue
                    queue.rho_s = queue.weight * priority.throughput
                    topology.switches[sw].priority_list.append(priority)
                    topology.switches[sw].slice_priorities[sls] = priority.priority


# задаем начальные значения приоритетов и весов для виртуальных пластов на каждом коммутаторе
def set_initial_parameters(slices, slices_order, topology):
    # для каждого слайса создаем множество коммутаторов, через которое проходят потоки
    build_slice_cross_switches_set(slices)

    # для каждоко слайса в порядке slices_order на каждом коммутаторе из sls_sw_set
    # создаем очереди и объединяем их в приоритеты
    create_queue_start_organization(slices, slices_order, topology)
    # print_queue_organization(topology)

    # перераспределем остаточную пропускную способность канала
    flag = mytopology.redistribute_residual_channel_capacity(topology)
    # print_queue_organization(topology)
    return flag


# формируем кривую обслуживания на каждом коммутаторе для начальных параметров
def create_start_service_curve(topology):
    # на каждом коммутаторе вычисляем задержку приоритета
    for sw in topology.switches.keys():
        slicedelay.calculate_priority_delay(topology, sw)

    # вычисляем задержку для каждой очереди
    for sw in topology.switches.keys():
        for pr in topology.switches[sw].priority_list:
            slicedelay.calculate_queue_delay(pr)
    # print_queue_organization(topology)


# парсим конфиг файл и заполняем необходимы структуры
def parse_config(input_file, slices, topology):
    print('Start parsing input file:', input_file)
    with open(input_file) as json_file:
        data = json.load(json_file)
        chi_square = data["chi_square"]

        # считываем топологию
        topo_data = data["topology"]
        for sw_data in topo_data["switches"]:
            sw = objects.Switch(sw_data["number"], sw_data["throughput"])
            topology.switches[sw_data["number"]] = sw
        topology.links = topo_data["links"]

        # считываем слайсы
        for sls_data in data["slices"]:
            correct = True
            sls = objects.Slice(sls_data["sls_number"], sls_data["qos_throughput"],
                                sls_data["qos_delay"], sls_data["packet_size"])
            i = 1
            for fl in sls_data["flows"]:
                flow = objects.Flow(i, fl["epsilon"], fl["path"])
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
                i += 1
            if correct:
                slices[sls.id] = sls


# записываем результаты работы в выходной файл
def write_result(output_file, slices, topology):
    file = open(output_file, "w")
    file.write('{\n')
    file.write("\t\"slices\" : [\n")
    # записываем информацию о слайсах
    slice_numbers = len(slices.keys())
    for sls in slices.keys():
        file.write("\t\t{\n \t\t\t\"sls_number\" : " + str(sls) + ",\n")
        file.write("\t\t\t\"packet_size\" : " + str(slices[sls].packet_size) + ",\n")
        file.write("\t\t\t\"bandwidth\" : " + str(slices[sls].qos_throughput) + ",\n")
        file.write("\t\t\t\"flows\" : [\n")
        # записываем информацию о потоках
        flow_count = len(slices[sls].flows_list)
        for flow in slices[sls].flows_list:
            file.write("\t\t\t\t{\n")
            file.write("\t\t\t\t\t\"lambda\" : " + str(flow.rho_a) + ",\n")
            file.write("\t\t\t\t\t\"path\" : [")
            path_len = len(flow.path)
            for elem in flow.path:
                file.write(str(elem))
                path_len -= 1
                if path_len != 0:
                    file.write(", ")
            file.write("]\n\t\t\t\t}")
            flow_count -= 1
            if flow_count != 0:
                file.write(",\n")
            else:
                file.write("\n")
        file.write("\t\t\t]\n\t\t}")
        slice_numbers -= 1
        if slice_numbers != 0:
            file.write(",\n")
    file.write("\n\t],\n \t\"topology\" : { \n \t\t\"switches\" : [\n")
    # записываем информацию о коммутаторах
    sw_numbers = len(topology.switches.keys())
    for sw in topology.switches.keys():
        file.write("\t\t\t{\n \t\t\t\t\"number\" : " + str(sw) + ",\n")
        file.write("\t\t\t\t\"bandwidth\" : " + str(topology.switches[sw].physical_speed) + ",\n")
        file.write("\t\t\t\t\"queues\" : [\n")
        # записываем информацию о каждой очереди
        queues_count = 0
        pr_count = len(topology.switches[sw].priority_list)
        for pr in topology.switches[sw].priority_list:
            pr_count -= 1
            queues_count += len(pr.queue_list)
            for queue in pr.queue_list:
                file.write("\t\t\t\t\t{\n \t\t\t\t\t\t\"priority\" : " + str(pr.priority) + ",\n")
                file.write("\t\t\t\t\t\t\"queue_number\" : " + str(queue.number) + ",\n")
                file.write("\t\t\t\t\t\t\"slice\" : " + str(queue.slice.id) + ",\n")
                file.write("\t\t\t\t\t\t\"weight\" : " + str(queue.weight) + "\n")
                file.write("\t\t\t\t\t}")
                queues_count -= 1
                if pr_count != 0 or queues_count != 0:
                    file.write(",\n")
                else:
                    file.write("\n")
        file.write("\t\t\t\t]\n \t\t\t}")
        sw_numbers -= 1
        if sw_numbers != 0:
            file.write(",\n")
    file.write("\n\t\t],\n \t\t \"links\" : [\n")
    # записываем информацию о каналах
    lk_count = 0
    for lk in topology.links:
        file.write("\t\t\t[" + str(lk[0]) + ", " + str(lk[1]) + "]")
        lk_count += 1
        if lk_count != len(topology.links):
            file.write(",\n")
    file.write("\n\t\t] \n \t}\n }\n")


def main(argv):
    slices = dict()
    topology = mytopology.Topology()

    # парсим конфиг файл и заполняем необходимы структуры
    parse_config(argv[0], slices, topology)
    file_name = argv[0][5:len(argv[0])-5]

    # сортируем слайсы в зависимости от требования к задержке
    slices_order = list()       # список номеров слайсов, упорядоченный по возрастанию задержки
    sort_slices(slices, slices_order)

    # задаем начальные значения приоритетов и весов для виртуальных пластов на каждом коммутаторе
    flag = set_initial_parameters(slices, slices_order, topology)
    if flag:
        print('Impossible to continue calculation. Stop working')
        return

    # формируем кривую обслуживания на каждом коммутаторе для начальных параметров
    create_start_service_curve(topology)

    # подбор корректных параметров для слайсов
    algorithm.modify_queue_parameters(slices, slices_order, topology, file_name)

    # записываем результаты работы в выходной файл
    write_result(argv[1], slices, topology)


if __name__ == "__main__":
    main(sys.argv[1:])
