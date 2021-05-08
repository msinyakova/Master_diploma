import slicedelay


DELAY_DEVIATION = 0.05


# выбираем коммутатор, на котором будет изменяться приоритет
def find_switch(topology, sls_sw_set, used_sw):
    # TODO
    print('find_switch')
    return 0


# увеличиваем приоритет и пересчитываем rho_s и b_s для обоих приоритетов
def increase_priority(topology, sls_number, sw):
    # TODO
    print('increase_priority')


# запускаем проверку для всех слайсов у которых изменились значения rho_s и b_s
def check_slices_in_priority(slices, sw, topology, correct):
    # TODO
    print('check_slices_in_priority')
    correct = True
    return True


# возвращаем приоритет, если у одного из слайсов нарушено требование к оценке задержки
def decrease_priority(topology, sls_number, sw):
    # TODO
    print('decrease_priority')


# подбор корректных параметров для слайсов (основной алгоритм работы)
def modify_queue_parameters(slices, slices_order, topology, file_name):
    for sls_number in slices_order:
        # вычисляем оценку задержки виртуального пласта
        sls_delay = slicedelay.calculate_slice_delay(sls_number, slices, topology, file_name)
        # если полученная оценка меньше требуемой задержки, переходим к следующему слайсу
        if sls_delay < slices[sls_number].qos_delay:
            continue
        correct = False             # корректно ли состояние других слайсов
        find_parameters = False     # найдены ли параметры для текущего слайса
        while not correct and not find_parameters:
            # TODO реализовать изменение omega
            # выбираем коммутатор, на котором будет изменяться приоритет
            sw = find_switch(topology, slices[sls_number].sls_sw_set, slices[sls_number].used_sw)
            # увеличиваем приоритет и пересчитываем rho_s и b_s для обоих приоритетов
            increase_priority(topology, sls_number, sw)
            # запускаем проверку для всех слайсов у которых изменились значения rho_s и b_s
            find_parameters = check_slices_in_priority(slices, sw, topology, correct)
            if not correct:
                # возвращаем приоритет, если у одного из слайсов нарушено требование к оценке задержки
                decrease_priority(topology, sls_number, sw)
