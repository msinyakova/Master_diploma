import sys
import json
import csv

import objects
import slicedelay


# сортируем слайсы в зависимости от требования к задержке
def sort_slices(slices, order):
    print('sort slices by delay')
    # TODO


# задаем начальные значения приоритетов и весов для виртуальных пластов на каждом коммутаторе
def set_initial_parameters(slices, slices_order, topology):
    print('set_initial_parameters')
    # TODO


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
            sls = objects.Slice(sls_data["sls_number"], sls_data["qos_throughput"], sls_data["qos_delay"])
            for fl in sls_data["flows"]:
                flow = objects.Flow(fl["epsilon"], fl["path"])
                if "statistic" in fl:
                    with open(fl["statistic"], 'r') as f:
                        reader = csv.reader(f)
                        stat_list = list(reader)
                    flow.define_distribution(stat_list, chi_square)
                else:
                    flow.rho_a = fl["rho_a"]
                    flow.b_a = fl["b_a"]
                sls.flows_list.append(flow)
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
    slices_order = list()
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
