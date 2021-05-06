import slicedelay


# подбор корректных параметров для слайсов (основной алгоритм работы)
def modify_queue_parameters(slices, slices_order, topology):
    print('modify_queue_parameters')
    for sls_number in slices_order:
        sls_delay = slicedelay.calculate_slice_delay(sls_number, slices, topology)
    # TODO
