from r2a.ir2a import IR2A
from player.parser import *
from time import perf_counter


class R2APANDA(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.p_add_bitrate = 0          # w
        self.probe_convergence = 0      # k
        self.request_time = 0
        self.last_throughput = 0        # ~x[n-1]
        self.last_est_throughput = 0    # ^x[n-1]
        self.qi = []

    def handle_xml_request(self, msg):
        """ Sends the xml request down to the transport layer. """

        self.request_time = perf_counter()
        self.send_down(msg)


    def handle_xml_response(self, msg):
        """ Receives the XML, calculates the throughtput """
        self.last_est_throughput = msg.get_bit_length() / (perf_counter() - self.request_time)
        self.last_throughput = self.last_est_throughput
        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()
        self.send_up(msg)


    def handle_segment_size_request(self, msg):
        request_time_atual = perf_counter()
        inter_request_time = request_time_atual- self.request_time
        self.request_time = request_time_atual

        taxa_mudanca_throughput = self.probe_convergence * (self.p_add_bitrate
                - max(0, self.last_est_throughput - self.last_throughput + self.p_add_bitrate))
        est_throughput = taxa_mudanca_throughput * inter_request_time + self.last_est_throughput

        selected_qi = self.qi[0]
        for i in self.qi:
            if est_throughput > i:
                selected_qi = i

        msg.add_quality_id(selected_qi)
        self.last_est_throughput = est_throughput

        print(msg.get_segment_size())

        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.last_throughput = msg.get_bit_length() / (perf_counter() - self.request_time)
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
