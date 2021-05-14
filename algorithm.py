import slicedelay


# выбираем коммутатор, на котором будет изменяться приоритет
def find_switch(topology, sls_sw_set, used_sw, sls_id):
    available_sw = sls_sw_set.difference(used_sw)
    min_queue_in_pr = 4000
    res_sw = 0
    for sw in available_sw:
        # если слайс находится в 0 приоритете, то увеличить приоритет на этом коммутаторе нельзя
        if sls_id in topology.switches[sw].priority_list[0].slice_queue.keys():
            used_sw.add(sw)
        # выбираем коммутатор, у которого наименьшее кол-во очередей в приоритете выше
        pr = topology.switches[sw].slice_priorities[sls_id] - 1
        if sls_id in topology.switches[sw].priority_list[pr].slice_queue.keys():
            if min_queue_in_pr < len(topology.switches[sw].priority_list[pr-1].queue_list):
                min_queue_in_pr = topology.switches[sw].priority_list[pr-1].queue_list
                res_sw = sw
    print('find_switch', res_sw)
    return res_sw


# увеличиваем приоритет и пересчитываем rho_s и b_s для обоих приоритетов
def increase_priority(topology, sls_number, sw_number):
    for i in range(1, len(topology.switches[sw_number].priority_list)):
        high_priority = topology.switches[sw_number].priority_list[i-1]
        curr_priority = topology.switches[sw_number].priority_list[i]
        for j in range(0, len(curr_priority.queue_list)):
            if curr_priority.queue_list[j].number == sls_number:
                # удаляем очередь из низшего приоритета
                queue = curr_priority.queue_list.pop(j)
                # добавляем в высший приоритет
                high_priority.queue_list.append(queue)
                # выполняем пересчет параметров приоритетов
                high_priority.recalculation()
                curr_priority.recalculation()
                # выполняем пересчет задержки приоритетов
                slicedelay.calculate_priority_delay(topology, sw_number)
                # выполняем пересчет задержки для очередей внутри приоритетов
                slicedelay.calculate_queue_delay(curr_priority)
                slicedelay.calculate_queue_delay(high_priority)
    print('increase_priority')


# запускаем проверку для всех слайсов у которых изменились значения rho_s и b_s
def check_slices_in_priority(slices, sw, topology, sls_number, file_name):
    find_parameters = False
    priority = topology.switches[sw].slice_priorities[sls_number] - 1
    for queue in topology.switches[sw].priority_list[priority].queue_list:
        sls_delay = slicedelay.calculate_slice_delay(queue.number, slices, topology, file_name)
        if sls_number == queue.number:
            if sls_delay > slices[sls_number].qos_delay:
                find_parameters = False
            else:
                slices[sls_number].estimate_delay = sls_delay
                find_parameters = True
        else:
            if sls_delay > slices[queue.number].qos_delay:
                return {False, find_parameters}
            else:
                slices[sls_number].estimate_delay = sls_delay
    return {True, find_parameters}


# возвращаем приоритет, если у одного из слайсов нарушено требование к оценке задержки
def decrease_priority(topology, sls_number, sw_number):
    for i in range(0, len(topology.switches[sw_number].priority_list) - 1):
        low_priority = topology.switches[sw_number].priority_list[i+1]
        curr_priority = topology.switches[sw_number].priority_list[i]
        for j in range(0, len(curr_priority.queue_list)):
            if curr_priority.queue_list[j].number == sls_number:
                # удаляем очередь из высшего приоритета
                queue = curr_priority.queue_list.pop(j)
                # добавляем в низший приоритет
                low_priority.queue_list.append(queue)
                # выполняем пересчет параметров приоритетов
                low_priority.recalculation()
                curr_priority.recalculation()
                # выполняем пересчет задержки приоритетов
                slicedelay.calculate_priority_delay(topology, sw_number)
                # выполняем пересчет задержки для очередей внутри приоритетов
                slicedelay.calculate_queue_delay(curr_priority)
                slicedelay.calculate_queue_delay(low_priority)
    print('decrease_priority')


# подбор корректных параметров для слайсов (основной алгоритм работы)
def modify_queue_parameters(slices, slices_order, topology, file_name):
    for sls_number in slices_order:
        # вычисляем оценку задержки виртуального пласта
        sls_delay = slicedelay.calculate_slice_delay(sls_number, slices, topology, file_name)
        # если полученная оценка меньше требуемой задержки, переходим к следующему слайсу
        if sls_delay < slices[sls_number].qos_delay:
            slices[sls_number].estimate_delay = sls_delay
            continue
        correct = False             # корректно ли состояние других слайсов
        find_parameters = False     # найдены ли параметры для текущего слайса
        while not correct and not find_parameters:
            # выбираем коммутатор, на котором будет изменяться приоритет
            sw = find_switch(topology, slices[sls_number].sls_sw_set, slices[sls_number].used_sw, slices[sls_number].id)
            if sw == 0:
                break
            # увеличиваем приоритет и пересчитываем rho_s и b_s для обоих приоритетов
            increase_priority(topology, sls_number, sw)
            # запускаем проверку для всех слайсов у которых изменились значения rho_s и b_s
            correct, find_parameters = check_slices_in_priority(slices, sw, topology, sls_number, file_name)
            if not correct:
                # возвращаем приоритет, если у одного из слайсов нарушено требование к оценке задержки
                decrease_priority(topology, sls_number, sw)
        if not correct and not find_parameters:
            print("Impossible to install slice :", sls_number)
            # удаляем слайс из всех структур
            topology.delete_slice(slices.pop(sls_number))
