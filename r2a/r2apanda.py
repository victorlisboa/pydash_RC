from r2a.ir2a import IR2A
from player.parser import *
from time import perf_counter, sleep


class R2APANDA(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.p_add_bitrate = 0.3        # w
        self.probe_convergence = 0.14   # k
        self.buffer_convergence = 0     # beta
        self.request_time = 0
        self.last_throughput = 0        # ~x[n-1]
        self.last_est_throughput = 0    # ^x[n-1]
        self.qi = []
        self.time_to_next_request = 0

    def handle_xml_request(self, msg):
        """Sends the XML request to the ConnectionHandler"""

        self.request_time = perf_counter()
        self.send_down(msg)


    def handle_xml_response(self, msg):
        """Sends the XML response to the Player"""
        self.last_est_throughput = msg.get_bit_length() / (perf_counter() - self.request_time)
        self.last_throughput = self.last_est_throughput
        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()
        self.send_up(msg)


    def handle_segment_size_request(self, msg):
        #tempo_passado = perf_counter() - self.request_time
        #if tempo_passado < self.time_to_next_request:
        #    sleep(self.time_to_next_request - tempo_passado)

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

        #last_buffer_size = self.whiteboard.get_playback_buffer_size()[-1][1]
        #self.time_to_next_request = (selected_qi * msg.get_segment_size() / est_throughput 
        #        + self.buffer_convergence * (last_buffer_size - 10))
        
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.last_throughput = msg.get_bit_length() / (perf_counter() - self.request_time)
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
