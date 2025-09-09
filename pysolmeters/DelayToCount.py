"""
# -*- coding: utf-8 -*-
# ===============================================================================
#
# Copyright (C) 2013/2025 Laurent Labatut / Laurent Champagnac
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
import sys
from collections import OrderedDict

from threading import Lock
from pysolbase.SolBase import SolBase
from pysolmeters.AtomicInt import AtomicInt

import logging

logger = logging.getLogger(__name__)


class DelayToCount(object):
    """
    A class that associate delay intervals to occurrence count.
    Low level class without any lock.
    [0-100ms  ] => x hits
    [100-200ms] => y hits
    [...-...  ] => z hits
    """

    def __init__(self, instance_name, ar_delay=None):
        """
        Init
        :param ar_delay: Delay array to handle in millis (must finish with max int value, value in increasing order)
        :type ar_delay: list,tuple,None
        :param instance_name: Instance name
        :type instance_name: str
        :return Nothing
        """

        # Default is required
        if not ar_delay:
            ar_delay = [0, 50, 100, 500, 1000, 2500, 5000, 10000, 30000, 60000, sys.maxsize]

        # Name
        self._instance_name = instance_name

        # Hash (ordered)
        self._sorted_dict = OrderedDict()

        # Validate max int at the end (otherwise we may not be able to process and store some values)
        if ar_delay[len(ar_delay) - 1] != sys.maxsize:
            raise Exception("sys.maxsize required in last ar_delay item")

        # Validate order and prepare the hash
        prev = None
        for ms in ar_delay:
            if not prev:
                prev = ms
            elif prev >= ms:
                raise Exception("Not increasing value, prev={0}, ms={1}".format(prev, ms))

            # Hash it
            self._sorted_dict[ms] = AtomicInt()

    def put(self, delay_ms, increment_value=1):
        """
        Put a value for specified delay.
        :param delay_ms: Delay in millis
        :type delay_ms: int
        :param increment_value: Value to increment
        :type increment_value: int
        :return Nothing
        """

        # Found the good one
        aif = self._sorted_dict[sys.maxsize]
        for ms, ai in self._sorted_dict.items():
            if ms <= delay_ms and ms != sys.maxsize:
                aif = ai
            else:
                break

        # Go
        aif.increment(increment_value)

    def log(self, s_tags):
        """
        Write to logger
        :param s_tags: str
        :type s_tags: str
        """

        if logger.level <= logging.DEBUG:
            ar = list(self._sorted_dict.keys())
            for i in range(0, len(ar) - 1):
                ms1 = ar[i]
                ms2 = ar[i + 1]
                if ms2 == sys.maxsize:
                    ms2 = "MAX"
                ai = self._sorted_dict[ms1]
                v = ai.get()
                if v == 0:
                    continue
                # Too many log in info level
                logger.debug("%s%s [%s-%s], c=%s", self._instance_name, s_tags, ms1, ms2, v)

    def to_dict(self):
        """
        To dict
        :return OrderedDict
        :rtype: OrderedDict
        """

        d = OrderedDict()
        ar = list(self._sorted_dict.keys())
        for i in range(0, len(ar) - 1):
            ms1 = ar[i]
            ms2 = ar[i + 1]
            if ms2 == sys.maxsize:
                ms2 = "MAX"
            ai = self._sorted_dict[ms1]
            out_k = "{0}|{1}-{2}".format(self._instance_name, ms1, ms2)
            out_v = ai.get()
            d[out_k] = out_v
        return d

    def to_udp_list(self, d_tag=None, d_opt_tag=None):
        """
        To dict
        :param d_tag: dict,None
        :type d_tag: dict,None
        :param d_opt_tag: dict,None
        :type d_opt_tag: dict,None
        :return list
        :rtype: list
        """

        if not d_tag:
            d_tag = {}
        if not d_opt_tag:
            d_opt_tag = {}
        ar_out = list()
        ar = list(self._sorted_dict.keys())
        for i in range(0, len(ar) - 1):
            # Build key
            ms1 = ar[i]
            ms2 = ar[i + 1]
            if ms2 == sys.maxsize:
                ms2 = "MAX"
            out_k = "{0}_{1}-{2}".format(self._instance_name, ms1, ms2)
            # Get value
            ai = self._sorted_dict[ms1]
            out_v = ai.get()
            # Build local array
            ar_local = [
                # probe name
                out_k,
                # tag dict
                d_tag,
                # value
                out_v,
                # epoch
                SolBase.dt_to_epoch(SolBase.datecurrent()),
                # additional tags
                d_opt_tag
            ]
            # Add to output
            ar_out.append(ar_local)
        # Over
        return ar_out


class DelayToCountSafe(DelayToCount):
    """
    A class that associate delay intervals to occurrence count.
    This class use lock on put.
    [0-100ms  ] => x hits
    [100-200ms] => y hits
    [...-...  ] => z hits
    """

    def __init__(self, instance_name, ar_delay=None):
        """
        Init
        :param ar_delay: Delay array to handle in millis (must finish with max int value, value in increasing order)
        :type ar_delay: list,tuple,None
        :param instance_name: Instance name
        :type instance_name: str
        :return Nothing
        """

        self._lock = Lock()
        with self._lock:
            DelayToCount.__init__(self, instance_name, ar_delay)

    def put(self, delay_ms, increment_value=1):
        """
        Put a value for specified delay.
        :param delay_ms: Delay in millis
        :type delay_ms: int
        :param increment_value: Value to increment
        :type increment_value: int
        :return Nothing
        """

        with self._lock:
            DelayToCount.put(self, delay_ms, increment_value)

    def log(self, s_tags):
        """
        Write to logger
        :param s_tags: dict,None
        :type s_tags: dict,None
        """
        with self._lock:
            DelayToCount.log(self, s_tags)

    def to_dict(self):
        """
        To dict
        :return OrderedDict
        :rtype: OrderedDict
        """
        with self._lock:
            DelayToCount.to_dict(self)
