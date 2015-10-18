import zmq
import time


class HightQuarter(object):
    """The main hight quarter that will receive informations from the turrets
    and send the start message

    :param publish_port int: the port for publishing information to turrets
    :param rc_port int: the result collector port for collecting results from the turrets
    :param results_writer ResultsWriter: the results writer
    :param config dict: the configuration of the test
    """
    def __init__(self, publish_port, rc_port, results_writer, config):
        context = zmq.Context()

        self.poller = zmq.Poller()

        self.result_collector = context.socket(zmq.PULL)
        self.result_collector.bind("tcp://*:{}".format(rc_port))

        self.publisher = context.socket(zmq.PUB)
        self.publisher.bind("tcp://*:{}".format(publish_port))

        self.poller.register(self.result_collector, zmq.POLLIN)

        self.results_writer = results_writer
        self.config = config

    def run(self):
        """Run the hight quarter, lunch the turrets and wait for results
        """
        elapsed = 0
        start_time = time.time()
        self.publisher.send_json({'command': 'start', 'msg': 'open fire'})
        while elapsed < (self.config['run_time'] + 1):
            try:
                socks = dict(self.poller.poll(1000))
                if self.result_collector in socks:
                    data = self.result_collector.recv_json()
                    self.results_writer.write_result(data)
                print('elapsed: {}   transactions: {}  timers: {}  errors: {}\r'.format(round(elapsed),
                                                                                        self.results_writer.trans_count,
                                                                                        self.results_writer.timer_count,
                                                                                        self.results_writer.error_count),end=' ')
                elapsed = time.time() - start_time
            except (Exception, KeyboardInterrupt) as e:
                print("\nStopping test, sending stop command to turrets")
                self.publisher.send_json({'command': 'stop', 'msg': 'premature stop'})
                print(e)
                break
        self.publisher.send_json({'command': 'stop', 'msg': 'stopping fire'})
