import sys
import json
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
def parse_config(input_file, chi_square, slices, topology):
    print('Start parsing input file', input_file)
    with open(input_file) as json_file:
        data = json.load(json_file)
        # TODO


# записываем результаты работы в выходной файл
def write_result(output_file):
    print('write_result')
    # TODO


def main(argv):
    chi_square = list()
    slices = dict()
    topology = objects.Topology()

    # парсим конфиг файл и заполняем необходимы структуры
    parse_config(argv[0], chi_square, slices, topology)

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
