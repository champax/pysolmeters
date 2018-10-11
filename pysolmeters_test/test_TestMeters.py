"""
# -*- coding: utf-8 -*-
# ===============================================================================
#
# Copyright (C) 2013/2017 Laurent Labatut / Laurent Champagnac
#
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
# ===============================================================================
"""

import logging
import unittest

from pysolbase.SolBase import SolBase

from pysolmeters.AtomicFloat import AtomicFloatSafe
from pysolmeters.AtomicInt import AtomicIntSafe
from pysolmeters.DelayToCount import DelayToCountSafe
from pysolmeters.Meters import Meters

logger = logging.getLogger(__name__)


class TestMeters(unittest.TestCase):
    """
    Test description
    """

    def setUp(self):
        """
        Setup (called before each test)
        """

        # Initialize asap
        SolBase.voodoo_init()
        SolBase.set_compo_name("CompoNotSet")
        self.assertTrue(SolBase._voodoo_initialized)
        self.assertTrue(SolBase._logging_initialized)

        # Reset
        Meters.reset()

    def tearDown(self):
        """
        Setup (called after each test)
        """
        pass

    def test_meters(self):
        """
        Test
        """

        ai1a = Meters.ai("ai1")
        self.assertIsInstance(ai1a, AtomicIntSafe)
        ai1b = Meters.ai("ai1")
        self.assertEqual(id(ai1a), id(ai1b))

        ai1a = Meters.aii("ai1")
        self.assertEqual(ai1a.get(), 1)
        ai1a = Meters.aii("ai1", 2)
        self.assertEqual(ai1a.get(), 3)
        self.assertEqual(ai1a.get(), Meters.aig("ai1"))

        af1a = Meters.af("af1")
        self.assertIsInstance(af1a, AtomicFloatSafe)
        af1b = Meters.af("af1")
        self.assertEqual(id(af1a), id(af1b))

        af1a = Meters.afi("af1")
        self.assertEqual(af1a.get(), 1.0)
        af1a = Meters.afi("af1", 2.0)
        self.assertEqual(af1a.get(), 3.0)
        self.assertEqual(af1a.get(), Meters.afg("af1"))

        dtc1a = Meters.dtc("dtc1")
        self.assertIsInstance(dtc1a, DelayToCountSafe)
        dtc1b = Meters.dtc("dtc1")
        self.assertEqual(id(dtc1a), id(dtc1b))

        # Write
        Meters.write_to_logger()

        # Serialize
        ar_json = Meters.meters_to_udp_format(send_pid=True, send_dtc=True)
        logger.info("Got ar_json=%s", ar_json)
        for cur_ar in ar_json:
            logger.info("Got cur_ar=%s", cur_ar)

        # Serialize, no dtc
        ar_json = Meters.meters_to_udp_format(send_pid=True, send_dtc=False)
        logger.info("Got ar_json=%s", ar_json)
        for cur_ar in ar_json:
            logger.info("Got cur_ar=%s", cur_ar)

        # Send to daemon (assuming its up locally)
        Meters.send_udp_to_knockdaemon()
        Meters.send_udp_to_knockdaemon(send_dtc=True)
        Meters.send_udp_to_knockdaemon(send_dtc=False)

        # ------------------------
        # UDP Scheduler test
        # ------------------------

        # Check
        self.assertIsNone(Meters.UDP_SCHEDULER_GREENLET)
        self.assertFalse(Meters.UDP_SCHEDULER_STARTED)

        # Start
        Meters.udp_scheduler_start(send_interval_ms=500)

        # Check
        self.assertIsNotNone(Meters.UDP_SCHEDULER_GREENLET)
        self.assertTrue(Meters.UDP_SCHEDULER_STARTED)

        # Start again
        Meters.udp_scheduler_start(send_interval_ms=500)

        # Check again
        self.assertIsNotNone(Meters.UDP_SCHEDULER_GREENLET)
        self.assertTrue(Meters.UDP_SCHEDULER_STARTED)

        # Interval is 500 => we sleep 3.250 sec, we assume we must have at least 500, 1000, 1500, 2000, 2500, 3000 run => 6 runs
        SolBase.sleep(3250)

        # Check
        self.assertGreaterEqual(Meters.aig("k.meters.udp.run.ok"), 6)
        self.assertEqual(Meters.aig("k.meters.udp.run.ex"), 0)
        self.assertIsNotNone(Meters.UDP_SCHEDULER_GREENLET)
        self.assertTrue(Meters.UDP_SCHEDULER_STARTED)

        # We stop
        Meters.udp_scheduler_stop()
        self.assertIsNone(Meters.UDP_SCHEDULER_GREENLET)
        self.assertFalse(Meters.UDP_SCHEDULER_STARTED)

        # Sleep again and check no more running
        cur_run = Meters.aig("k.meters.udp.run.ok")
        SolBase.sleep(2000)
        self.assertEqual(cur_run, Meters.aig("k.meters.udp.run.ok"))





