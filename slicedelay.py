import subprocess
import time


def calculate_priority_delay(topology, sw):
    # вычисляем числитель
    numerator = 0
    for pr in topology.switches[sw].priority_list:
        numerator += pr.priority_lambda / (topology.switches[sw].physical_speed ** 2)
    # вычисляем знаменатель
    for i in range(0, len(topology.switches[sw].priority_list)):
        sigma_prev = topology.switches[sw].priority_list[i - 1].sigma_priority
        pr = topology.switches[sw].priority_list[i]
        if pr.priority == 1:
            pr.sigma_priority = pr.priority_lambda / topology.switches[sw].physical_speed
            # if i != 0:
            #     print('pr.priority_lambda =', pr.priority_lambda, 'throughput =', topology.switches[sw].physical_speed)
        else:
            pr.sigma_priority = sigma_prev + pr.priority_lambda / topology.switches[sw].physical_speed
            # if i != 0:
            #     print('sigma_prev =', sigma_prev, 'pr.priority_lambda =', pr.priority_lambda, 'throughput =', topology.switches[sw].physical_speed)
        denominator = 2 * (1 - sigma_prev) * (1 - pr.sigma_priority)
        # if i != 0:
        #     print('sigma_prev =', sigma_prev, 'pr.sigma_priority =', pr.sigma_priority)
        # итоговая задержка для приоритета
        # if i != 0:
        #     print('numerator =', numerator, 'denominator', denominator)
        pr.delay = numerator / denominator


def calculate_queue_delay(pr):
    # вычисляем сумму минимальных требуемых скоростей для слайсов
    sum_r_k = 0
    for i in range(0, len(pr.queue_list)):
        sum_r_k += pr.queue_list[i].slice.qos_throughput

    for k in range(0, len(pr.queue_list)):
        # вычисляем знаменатель
        lambda_k = pr.queue_list[k].slice_lambda
        r_k = pr.queue_list[k].slice.qos_throughput
        denominator = 1 - (lambda_k * sum_r_k) / (pr.throughput * r_k)
        # print("lambda_k =", lambda_k, "sum_r_k =", sum_r_k, "pr.throughput =", pr.throughput, "r_k =", r_k)
        # вычислем числитель
        numerator = 0.5 * pr.priority_lambda / (pr.throughput ** 2)
        for j in range(0, len(pr.queue_list)):
            if k == j:
                continue
            r_j = pr.queue_list[j].slice.qos_throughput
            l_j = pr.queue_list[j].slice.packet_size
            lambda_j = pr.queue_list[j].slice_lambda
            rho_j = lambda_j * l_j / r_j
            # print('r_j =', r_j, 'l_j =', l_j, 'lambda_j =', lambda_j, 'rho_j =', rho_j)
            numerator += (r_j / r_k + rho_j * l_j) / pr.throughput
        # итоговая задержка для
        # print('numerator =', numerator, 'denominator', denominator)
        pr.queue_list[k].b_s = pr.delay + numerator / denominator


def create_flow_time(sls, topology, route_time, time_routes_switches):
    for i in range(len(sls.flows_list)):
        # создаем множество времен для потока, который вычисляем
        main_time = topology.form_flow_time(sls.flows_list[i], sls)
        # создаем множества времен для каждого потока и внутри для каждого свитча
        time_routes_switches[i] = topology.form_switches_time(main_time, sls.flows_list)
        # формируем список возможных задач для вычисляеого потока
        route_time[i] = topology.time_constraints(main_time, sls)


def calculate_slice_delay(sls_number, slices, topology, file_name):
    total_time_start = time.time()
    sls = slices[sls_number]
    # создаем всевозможные временные ограничения для потока
    route_time = dict()
    time_routes_switches = dict()
    create_flow_time(sls, topology, route_time, time_routes_switches)

    all_constraints_number = 0
    max_file_constraints_number = 0
    files_number = 0
    max_delay = 0.0
    time_lp_solver_finish = 0.0
    for key in route_time.keys():
        flow_max_delay = 0.0
        # для одного и того же потока перебираем варианты задач
        for task in route_time[key]:
            # создаем все неравенства без учета положения задержки для одной задачи
            help_str = topology.create_lp(task, time_routes_switches[key], sls.flows_list, sls)
            # print(task)
            based_constraints_number = topology.lengthLP
            # перебираем позицию для задержки
            for i in range(1, len(task)):
                # time_write1 = time.time()
                file_lp = "LP/lp_file" + file_name + ".txt"
                lp_file = open(file_lp, "w")
                files_number += 1
                # вписываем в файл всю информацию о задержке
                topology.write_delay_constraints(task, i, sls.flows_list[key], lp_file)
                # переписываем остальные неравенства для данной задачи
                lp_file.write(help_str)
                lp_file.close()
                # time_write = time.time() - time_write1
                # print("Time for write LP_file:", time_write)

                # отправляем на вычислени в lp_solver
                time_lp_solver_start = time.time()
                args = ["./lp_solver/lp_solve", file_lp]
                process = subprocess.Popen(args, stdout=subprocess.PIPE)
                data = process.communicate()
                time_lp_solver_finish = max(time_lp_solver_finish, time.time() - time_lp_solver_start)

                # time_read_proc1 = time.time()
                words = data[0].split()
                if len(words) <= 4:
                    print('flow = ', key, ' : ', data[0])
                    continue
                if float(words[4]) > flow_max_delay:
                    flow_max_delay = float(words[4])
                all_constraints_number += topology.lengthLP
                max_file_constraints_number = max(max_file_constraints_number, topology.lengthLP)
                topology.lengthLP = based_constraints_number
                # time_read_proc = time.time() - time_read_proc1
                # print("Time after work:", time_read_proc)
                # break
            topology.lengthLP = 0
            # break
        if flow_max_delay > max_delay:
            max_delay = flow_max_delay
        # break
    print("Max delay in slice", sls.id, '-', max_delay)
    # print("Number of files in linear programming : ", files_number)
    # print("Time for calculating one file in lp_solver : ", time_lp_solver_finish)
    # print("Max number of linear constraints in one file : ", max_file_constraints_number)
    # print("Number of linear constraints in general: ", all_constraints_number)
    total_time_finish = time.time() - total_time_start
    print("Total time: ", total_time_finish)
    return max_delay
