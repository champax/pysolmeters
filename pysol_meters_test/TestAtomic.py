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

from pysol_base.SolBase import SolBase

from pysol_meters.AtomicFloat import AtomicFloat, AtomicFloatSafe
from pysol_meters.AtomicInt import AtomicInt, AtomicIntSafe

logger = logging.getLogger(__name__)


class TestAtomic(unittest.TestCase):
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

    def test_true(self):
        """
        Test
        """
        self.assertTrue(True)

    def _go_atomic(self, ai_class):
        """
        Test
        :param ai_class: AtomicInt
        :type ai_class: AtomicInt,AtomicIntSafe
        """

        # Misc
        logger.info("Class=%s", ai_class)
        ai = ai_class()
        self.assertEqual(ai.get(), 0)
        self.assertEqual(ai.set(10), 10)
        self.assertEqual(ai.get(), 10)
        self.assertEqual(ai.set(-5), -5)
        self.assertEqual(ai.get(), -5)
        self.assertEqual(ai.increment(1), -4)
        self.assertEqual(ai.increment(-1), -5)
        self.assertEqual(ai.increment(10), 5)
        self.assertEqual(ai.increment(-10), -5)

        # Initial value
        ai = ai_class(initial_value=99)
        self.assertEqual(ai.get(), 99)

        # Max value
        ai = ai_class(initial_value=9, maximum_value=10)
        self.assertEqual(ai.get(), 9)
        self.assertEqual(ai.increment(), 10)
        self.assertEqual(ai.increment(), 1)

    def test_atomic_int(self):
        """
        Test
        """

        self._go_atomic(AtomicInt)

    def test_atomic_int_safe(self):
        """
        Test
        """

        self._go_atomic(AtomicIntSafe)

    def test_atomic_float(self):
        """
        Test
        """

        self._go_atomic(AtomicFloat)

    def test_atomic_float_safe(self):
        """
        Test
        """

        self._go_atomic(AtomicFloatSafe)
