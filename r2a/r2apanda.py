from r2a.ir2a import IR2A
from player.parser import *
from time import perf_counter, sleep


class R2APANDA(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.prob_add_bitrate = 0.3        # w
        self.probe_convergence = 0.14   # k
        self.buffer_convergence = 0     # beta
        self.last_request_time = 0           # time of the last request
        self.last_throughput = 0        # ~x[n-1] - last TCP throughput measured
        self.last_est_throughput = 0    # ^x[n-1] - last target throughput
        self.qi = []                    # list of the available video qualities
        self.time_to_next_request = 0

    def handle_xml_request(self, msg):
        """ Sends the XML request to the ConnectionHandler. """

        self.last_request_time = perf_counter()  # used to estimate the first throughput
        self.send_down(msg)


    def handle_xml_response(self, msg):
        """ Sends the XML response to the Player. """

        # this first request is also used to set the first estimated throughput
        # although it is the actual measured throughput
        self.last_est_throughput = msg.get_bit_length() / (perf_counter() - self.last_request_time)
        self.last_throughput = self.last_est_throughput

        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()
        self.send_up(msg)


    def handle_segment_size_request(self, msg):
        """ Selects the video quality based on the PANDA algorithm
            and sends the request to the ConnetionHandler. """

        # it waits until the time to the next request 
        elapsed_time = perf_counter() - self.last_request_time
        if elapsed_time < self.time_to_next_request:
           sleep(self.time_to_next_request - elapsed_time)

        current_request_time = perf_counter()
        inter_request_time = current_request_time - self.last_request_time
        self.last_request_time = current_request_time

        # estimating the next throughput (^x[n])
        discount = max(0, self.last_est_throughput - self.last_throughput + self.prob_add_bitrate)
        throughput_variation_rate = self.probe_convergence * (self.prob_add_bitrate - discount)
        est_throughput = throughput_variation_rate * inter_request_time + self.last_est_throughput

        # selects the video quality
        selected_qi = self.qi[0]
        for i in self.qi:
            if est_throughput > i:
                selected_qi = i
            else:
                break

        msg.add_quality_id(selected_qi)
        self.last_est_throughput = est_throughput

        # scheduling the next request time
        # last_buffer_size = self.whiteboard.get_playback_buffer_size()[-1][1]
        # self.time_to_next_request = (selected_qi * msg.get_segment_size() / est_throughput 
        #        + self.buffer_convergence * (last_buffer_size - 10))
        
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.last_throughput = msg.get_bit_length() / (perf_counter() - self.request_time)
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
