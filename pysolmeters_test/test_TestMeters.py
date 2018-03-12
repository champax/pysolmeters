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
