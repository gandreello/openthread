#!/usr/bin/env python
#
#  Copyright (c) 2017, The OpenThread Authors.
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#  3. Neither the name of the copyright holder nor the
#     names of its contributors may be used to endorse or promote products
#     derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
#

import time
import unittest

import config
import mle
import network_layer
import node

LEADER = 1
ROUTER = 2

def wait_for_output(testcase, get_output, desired, timeout=10):
    testcase.simulator.go(timeout)
    current = get_output()
    testcase.assertEqual(current, desired)


class RouterAttach_fault_injection(unittest.TestCase):

    def __setUp(self):
        self.simulator = config.create_default_simulator()

        self.nodes = {}
        for i in range(1, 3):
            self.nodes[i] = node.Node(i, simulator=self.simulator)

        self.nodes[LEADER].set_panid(0xface)
        self.nodes[LEADER].set_mode('rsdn')
        self.nodes[LEADER].add_whitelist(self.nodes[ROUTER].get_addr64())
        self.nodes[LEADER].enable_whitelist()

        self.nodes[ROUTER].set_panid(0xface)
        self.nodes[ROUTER].set_mode('rsdn')
        self.nodes[ROUTER].add_whitelist(self.nodes[LEADER].get_addr64())
        self.nodes[ROUTER].enable_whitelist()
        self.nodes[ROUTER].set_router_selection_jitter(1)

    def __tearDown(self):
        for node in list(self.nodes.values()):
            node.stop()
        del self.nodes
        del self.simulator

    def test(self):

        self.__setUp()

        self.__test_body()

        leader_counters = self.nodes[LEADER].fi_print_counters()
        print "LEADER's counters: " + str(leader_counters)
        router_counters = self.nodes[ROUTER].fi_print_counters()
        print "ROUTER's counters: " + str(router_counters)

        self.__tearDown()

        self.__test_loop(LEADER, leader_counters)

        self.__test_loop(ROUTER, router_counters)

    def __test_loop(self, nodeid, counters):
        print "Iterating on node " + str(nodeid)
        for fault, num in counters.iteritems():
            for skip in range(num):
                fault_config = fault + "_s" + str(skip) + "_f1"
                self.__setUp()
                self.__test_body(nodeid, fault_config)
                self.__tearDown()

    def __test_body(self, nodeid=None, fault_config=None):
        if nodeid:
            print "Fault injection: " + str(nodeid) + " " + str(fault_config)
            self.nodes[nodeid].fi_configure(fault_config)

        self.nodes[LEADER].start()
        self.nodes[LEADER].set_state('leader')
        wait_for_output(self, self.nodes[LEADER].get_state, 'leader', 4)

        self.nodes[ROUTER].start()
        wait_for_output(self, self.nodes[ROUTER].get_state, 'router', 7)

if __name__ == '__main__':
    unittest.main()