import sys


class Queue:
    def __init__(self, number_):
        self.number = number_
        self.priority = 0
        self.weight = 0
        self.slice = 0
        self.rho_s = 0
        self.b_s = 0
        self.route_numbers = 0


class Priority:
    def __init__(self, number_):
        self.priority = number_
        self.throughput = 0
        self.delay = 0
        self.queue_list = list()


class Switch:
    def __init__(self, speed_):
        self.priority_list = list()
        self.physical_speed = speed_


class Topology:
    def __init__(self):
        self.switches = list()


class Route:
    def __init__(self):
        self.rho_a = 0
        self.b_a = 0
        self.epsilon = 0
        self.path = list()


class Slice:
    def __init__(self, id_, throughput_, delay_):
        self.id = id_
        self.qos_throughput = throughput_
        self.qos_delay = delay_
        self.routes_list = list()


def parse_config(argv):
    print('parse config file', argv[0])


def main(argv):
    print('start calculate estimate')
    parse_config(argv)


if __name__ == "__main__":
    main(sys.argv[1:])
