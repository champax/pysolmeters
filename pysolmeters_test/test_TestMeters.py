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
import os
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

        # Bench
        self.per_loop = 10000
        self.max_ms = 2000

    def tearDown(self):
        """
        Setup (called after each test)
        """
        pass

    def test_tags_hash(self):
        """
        Test
        """

        d1 = {"a": "va", "b": "vb"}
        s1 = Meters._tags_hash_compute_and_store(d1)
        self.assertIsNotNone(s1)
        self.assertGreater(len(s1), 0)
        self.assertIn(s1, Meters._hash_meter["tags_hash"])
        self.assertEquals(d1, Meters._hash_meter["tags_hash"][s1])

        d2 = {"b": "vb", "a": "va"}
        s2 = Meters._tags_hash_compute_and_store(d2)
        self.assertIsNotNone(s2)
        self.assertGreater(len(s2), 0)
        self.assertIn(s2, Meters._hash_meter["tags_hash"])
        self.assertEquals(d2, Meters._hash_meter["tags_hash"][s2])

        d3 = {"a": "za", "b": "zb"}
        s3 = Meters._tags_hash_compute_and_store(d3)
        self.assertIsNotNone(s3)
        self.assertGreater(len(s3), 0)
        self.assertIn(s3, Meters._hash_meter["tags_hash"])
        self.assertNotEqual(s1, s3)

        self.assertEquals(s1, s2)
        self.assertEquals(len(Meters._hash_meter["tags_hash"]), 2)

        Meters.reset()
        self.assertEquals(len(Meters._hash_meter["tags_hash"]), 0)

        s_tags_1 = Meters.tags_format_for_logger(d1)
        s_tags_2 = Meters.tags_format_for_logger(d2)
        logger.info("Got s_tags_1=%s", s_tags_1)
        logger.info("Got s_tags_2=%s", s_tags_2)
        self.assertEquals(s_tags_1, s_tags_2)
        self.assertEquals(s_tags_1, " (a:va,b:vb) ")

    def test_key(self):
        """
        Test
        """

        d1 = {"a": "va", "b": "vb"}
        s1 = Meters._tags_hash_compute_and_store(d1)
        k1 = Meters._key_compute("zzz", d1)
        self.assertEquals(k1, "zzz#" + s1)

        s_key, s_sash = Meters._key_split(k1)
        self.assertEquals(s_key, "zzz")
        self.assertEquals(s_sash, s1)

        self.assertEquals(Meters._key_compute("zzz", None), "zzz#")
        self.assertEquals(Meters._key_compute("zzz", {}), "zzz#")

        s_key, s_sash = Meters._key_split("zzz#")
        self.assertEquals(s_key, "zzz")
        self.assertEquals(s_sash, None)

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

        Meters.dtci("dtc1", 0)
        Meters.dtci("dtc1", 50)
        Meters.dtci("dtc1", 100)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[0].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[50].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[100].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[500].get(), 0)

        # Write
        Meters.write_to_logger()

    def _bench(self, per_sec_multi, key, method_to_call, *args):
        """
        Internal bench
        :param per_sec_multi: Multiply per_sec (case of lists)
        :type per_sec_multi: int
        :param key: For log
        :type key: str
        :param method_to_call: Method point
        :type callable
        :param args: args
        :type args: object
        """

        if isinstance(args[0], list):
            # noinspection PyArgumentList,PyTypeChecker
            logger.debug("Using list, len=%s", len(args[0]))

        i = 0
        loop = 0
        per_loop = self.per_loop
        ms = SolBase.mscurrent()
        while SolBase.msdiff(ms) < self.max_ms:
            for _ in range(0, per_loop):
                method_to_call(*args)
            i += self.per_loop
            loop += 1
        i = i * per_sec_multi
        ms = SolBase.msdiff(ms)
        sec = ms / 1000.0
        per_sec = i / sec
        ms = round(ms, 2)
        sec = round(sec, 2)
        per_sec = round(per_sec, 2)
        logger.info("%32s, loop=%8s, i=%8s, ms=%8.2f, sec=%6.2f, per_sec=%12.2f", key, loop, i, ms, sec, per_sec)

    def test_meters_bench(self):
        """
        Test
        """

        # For logs format
        SolBase.sleep(100)
        logger.info("Bench now")

        Meters.reset()
        self._bench(1, "aii_tags_NO", Meters.aii, "aii1", 1, None)

        Meters.reset()
        self._bench(1, "aii_tags_go", Meters.aii, "aii1", 1, {"T1": "V1", "T2": "V2"})

        Meters.reset()
        self._bench(1, "dtc_tags_NO", Meters.dtci, "aii1", 0.1, 1, None)

        Meters.reset()
        self._bench(1, "dtc_tags_go", Meters.dtci, "aii1", 0.1, 1, {"T1": "V1", "T2": "V2"})

        Meters.reset()
        self._bench(1, "dtc_tags_big_NO", Meters.dtci, "aii1", 1000000000, 1, None)

        Meters.reset()
        self._bench(1, "dtc_tags_big_go", Meters.dtci, "aii1", 1000000000, 1, {"T1": "V1", "T2": "V2"})

        # For logs format
        SolBase.sleep(100)
        logger.info("Bench over")

    def test_meters_bench_chunk_udp_array_via_serialization(self):
        """
        Test
        """

        # For logs format
        SolBase.sleep(100)
        logger.info("Bench now")

        self.per_loop = 1

        self._meters_inject(count=5000)
        ar_json = Meters.meters_to_udp_format(send_pid=True, send_tags=True, send_dtc=False)
        self._bench(1, "udp_chunk_no_dtc", Meters.chunk_udp_array_via_serialization, ar_json, 60000)

        self._meters_inject(count=5000)
        ar_json = Meters.meters_to_udp_format(send_pid=True, send_tags=True, send_dtc=True)
        self._bench(1, "udp_chunk_dtc", Meters.chunk_udp_array_via_serialization, ar_json, 60000)

        # For logs format
        SolBase.sleep(100)
        logger.info("Bench over")

    def test_meters_with_tags_a_with_udp_check(self):
        """
        Test
        """

        hca = Meters._tags_hash_compute_and_store({"flag": "FA"})
        hcb = Meters._tags_hash_compute_and_store({"flag": "FB"})

        Meters.aii("ai1")
        Meters.aii("ai1", tags={"flag": "FA"})
        Meters.aii("ai1", tags={"flag": "FA"})
        Meters.aii("ai1", tags={"flag": "FB"})
        Meters.aii("ai1", tags={"flag": "FB"})
        Meters.aii("ai1", tags={"flag": "FB"})

        Meters.dtci("dtc1", 0)
        Meters.dtci("dtc1", 50)
        Meters.dtci("dtc1", 100)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[0].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[50].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[100].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[500].get(), 0)

        Meters.dtci("dtc1", 0, tags={"flag": "FA"})
        Meters.dtci("dtc1", 50, tags={"flag": "FA"})
        Meters.dtci("dtc1", 100, tags={"flag": "FA"})

        Meters.dtci("dtc1", 0, tags={"flag": "FB"})
        Meters.dtci("dtc1", 50, tags={"flag": "FB"})
        Meters.dtci("dtc1", 100, tags={"flag": "FB"})
        Meters.dtci("dtc1", 0, tags={"flag": "FB"})
        Meters.dtci("dtc1", 50, tags={"flag": "FB"})
        Meters.dtci("dtc1", 100, tags={"flag": "FB"})

        self.assertEquals(Meters._hash_meter["a_int"]["ai1#"].get(), 1)
        self.assertEquals(Meters._hash_meter["a_int"]["ai1#" + hca].get(), 2)
        self.assertEquals(Meters._hash_meter["a_int"]["ai1#" + hcb].get(), 3)

        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hca]._sorted_dict[0].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hca]._sorted_dict[50].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hca]._sorted_dict[100].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hca]._sorted_dict[500].get(), 0)

        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hcb]._sorted_dict[0].get(), 2)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hcb]._sorted_dict[50].get(), 2)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hcb]._sorted_dict[100].get(), 2)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hcb]._sorted_dict[500].get(), 0)

        # Write
        Meters.write_to_logger()

        # Upd check
        ar_udp = Meters.meters_to_udp_format(send_pid=True, send_tags=True, send_dtc=True)

        total_check = 0
        total_ok = 0
        total_ko_not_found = 0
        total_ko_multiple_found = 0
        pid = str(os.getpid())
        for s_key, d_tag, v in [
            ("ai1", {"PID": pid}, 1),
            ("ai1", {"flag": "FA", "PID": pid}, 2),
            ("ai1", {"flag": "FB", "PID": pid}, 3),

            ("dtc1_0-50", {"PID": pid}, 1),
            ("dtc1_50-100", {"PID": pid}, 1),
            ("dtc1_100-500", {"PID": pid}, 1),
            ("dtc1_500-1000", {"PID": pid}, 0),
            ("dtc1_1000-2500", {"PID": pid}, 0),
            ("dtc1_2500-5000", {"PID": pid}, 0),
            ("dtc1_5000-10000", {"PID": pid}, 0),
            ("dtc1_10000-30000", {"PID": pid}, 0),
            ("dtc1_30000-60000", {"PID": pid}, 0),
            ("dtc1_60000-MAX", {"PID": pid}, 0),

            ("dtc1_0-50", {"flag": "FA", "PID": pid}, 1),
            ("dtc1_50-100", {"flag": "FA", "PID": pid}, 1),
            ("dtc1_100-500", {"flag": "FA", "PID": pid}, 1),
            ("dtc1_500-1000", {"flag": "FA", "PID": pid}, 0),
            ("dtc1_1000-2500", {"flag": "FA", "PID": pid}, 0),
            ("dtc1_2500-5000", {"flag": "FA", "PID": pid}, 0),
            ("dtc1_5000-10000", {"flag": "FA", "PID": pid}, 0),
            ("dtc1_10000-30000", {"flag": "FA", "PID": pid}, 0),
            ("dtc1_30000-60000", {"flag": "FA", "PID": pid}, 0),
            ("dtc1_60000-MAX", {"flag": "FA", "PID": pid}, 0),

            ("dtc1_0-50", {"flag": "FB", "PID": pid}, 2),
            ("dtc1_50-100", {"flag": "FB", "PID": pid}, 2),
            ("dtc1_100-500", {"flag": "FB", "PID": pid}, 2),
            ("dtc1_500-1000", {"flag": "FB", "PID": pid}, 0),
            ("dtc1_1000-2500", {"flag": "FB", "PID": pid}, 0),
            ("dtc1_2500-5000", {"flag": "FB", "PID": pid}, 0),
            ("dtc1_5000-10000", {"flag": "FB", "PID": pid}, 0),
            ("dtc1_10000-30000", {"flag": "FB", "PID": pid}, 0),
            ("dtc1_30000-60000", {"flag": "FB", "PID": pid}, 0),
            ("dtc1_60000-MAX", {"flag": "FB", "PID": pid}, 0),

        ]:
            total_check += 1

            # Locate it
            found = 0
            for check_key, check_tag, check_v, _, _ in ar_udp:
                if check_key == s_key and check_tag == d_tag and check_v == v:
                    found += 1

            # Check
            if found == 0:
                total_ko_not_found += 1
            elif found > 1:
                total_ko_multiple_found += 1
            else:
                total_ok += 1

        # Final
        self.assertEquals(total_ko_multiple_found, 0)
        self.assertEquals(total_ko_multiple_found, 0)
        self.assertEquals(total_ok, total_check)
        self.assertEquals(len(ar_udp), total_check)

    def test_meters_with_tags_b(self):
        """
        Test
        """

        hca = Meters._tags_hash_compute_and_store({"flag1": "FA"})
        hcb = Meters._tags_hash_compute_and_store({"flag2": "FB"})

        Meters.aii("ai1")
        Meters.aii("ai1", tags={"flag1": "FA"})
        Meters.aii("ai1", tags={"flag1": "FA"})
        Meters.aii("ai1", tags={"flag2": "FB"})
        Meters.aii("ai1", tags={"flag2": "FB"})
        Meters.aii("ai1", tags={"flag2": "FB"})

        Meters.dtci("dtc1", 0)
        Meters.dtci("dtc1", 50)
        Meters.dtci("dtc1", 100)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[0].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[50].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[100].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[500].get(), 0)

        Meters.dtci("dtc1", 0, tags={"flag1": "FA"})
        Meters.dtci("dtc1", 50, tags={"flag1": "FA"})
        Meters.dtci("dtc1", 100, tags={"flag1": "FA"})

        Meters.dtci("dtc1", 0, tags={"flag2": "FB"})
        Meters.dtci("dtc1", 50, tags={"flag2": "FB"})
        Meters.dtci("dtc1", 100, tags={"flag2": "FB"})
        Meters.dtci("dtc1", 0, tags={"flag2": "FB"})
        Meters.dtci("dtc1", 50, tags={"flag2": "FB"})
        Meters.dtci("dtc1", 100, tags={"flag2": "FB"})

        self.assertEquals(Meters._hash_meter["a_int"]["ai1#"].get(), 1)
        self.assertEquals(Meters._hash_meter["a_int"]["ai1#" + hca].get(), 2)
        self.assertEquals(Meters._hash_meter["a_int"]["ai1#" + hcb].get(), 3)

        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hca]._sorted_dict[0].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hca]._sorted_dict[50].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hca]._sorted_dict[100].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hca]._sorted_dict[500].get(), 0)

        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hcb]._sorted_dict[0].get(), 2)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hcb]._sorted_dict[50].get(), 2)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hcb]._sorted_dict[100].get(), 2)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#" + hcb]._sorted_dict[500].get(), 0)

        # Write
        Meters.write_to_logger()

    @classmethod
    def _meters_inject(cls, count):
        """
        Inject meters for chunk test
        :param count: int
        :type count: int
        """

        # Inject meters
        Meters.reset()
        for i in range(0, count):

            # 10 tags each
            d_tags = dict()
            for k in range(0, 10):
                d_tags["TAG_aaaaaaaaaaaaaaaaa_%s_%s" % (i, k)] = "VAL_aaaaaaaaaaaaaaaaa_%s_%s" % (i, k)

            # Inject
            Meters.aii("k.meters.aii_udp_check_%s" % i, tags=d_tags)

            # Dtc
            for ms in [0, 10, 100, 500, 5000, 10000, 60000]:
                Meters.dtci("k.meters.dtci_udp_check_%s" % i, ms, tags=d_tags)

    def test_meters_chunk_udp_array_via_serialization(self):
        """
        Test
        """

        # ----------------------
        # Udp, no DTC
        # ----------------------
        self._meters_inject(count=5000)
        ar_json = Meters.meters_to_udp_format(
            send_pid=True,
            send_tags=True,
            send_dtc=False,
        )
        logger.info("Got ar_json.len=%s", len(ar_json))

        for max_size, _ in [
            (60000, 0.0),
            (30000, 0.0),
        ]:
            logger.info("*** CHECK, NO DTC, max_size=%s", max_size)
            ar_bin_chunk, ar_json_chunk = Meters.chunk_udp_array_via_serialization(ar_json, max_size_bytes=max_size)
            logger.info("Got chunk size=%s/%s", len(ar_bin_chunk), len(ar_json_chunk))
            for bin_buf in ar_bin_chunk:
                logger.debug("Got chunk, NO DTC, len=%s, max=%s", len(bin_buf), max_size)
                self.assertTrue(len(bin_buf) < max_size)

            logger.info("Check now")
            c = 0
            for cur_ar in ar_json_chunk:
                c += len(cur_ar)
                for cur_item in cur_ar:
                    self.assertIn(cur_item, ar_json)
            self.assertEquals(c, len(ar_json))

        # ----------------------
        # Udp, DTC
        # ----------------------
        self._meters_inject(count=500)
        ar_json = Meters.meters_to_udp_format(
            send_pid=True,
            send_tags=True,
            send_dtc=True,
        )
        logger.info("Got ar_json.len=%s", len(ar_json))

        for max_size, _ in [
            (60000, 0.0),
            (30000, 0.0),
        ]:
            logger.info("*** CHECK, DTC, max_size=%s", max_size)
            ar_bin_chunk, ar_json_chunk = Meters.chunk_udp_array_via_serialization(ar_json, max_size_bytes=max_size)
            logger.info("Got chunk size=%s/%s", len(ar_bin_chunk), len(ar_json_chunk))
            for bin_buf in ar_bin_chunk:
                logger.debug("Got chunk, DTC, len=%s, max=%s", len(bin_buf), max_size)
                self.assertTrue(len(bin_buf) < max_size)

            logger.info("Check now")
            c = 0
            for cur_ar in ar_json_chunk:
                c += len(cur_ar)
                for cur_item in cur_ar:
                    self.assertIn(cur_item, ar_json)
            self.assertEquals(c, len(ar_json))

    @unittest.skip("Need knockdaemon2")
    def test_meters_to_udp(self):
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

        Meters.dtci("dtc1", 0)
        Meters.dtci("dtc1", 50)
        Meters.dtci("dtc1", 100)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[0].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[50].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[100].get(), 1)
        self.assertEquals(Meters._hash_meter["dtc"]["dtc1#"]._sorted_dict[500].get(), 0)

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
