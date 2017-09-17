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
from threading import Lock

from pysolmeters.AtomicFloat import AtomicFloatSafe, AtomicFloat
from pysolmeters.AtomicInt import AtomicIntSafe, AtomicInt
from pysolmeters.DelayToCount import DelayToCountSafe, DelayToCount

logger = logging.getLogger(__name__)


class Meters(object):
    """
    Static meter manager.
    """

    # Hash of meters
    _hash_meter = {
        "a_int": dict(),
        "a_float": dict(),
        "dtc": dict()
    }

    # Lock
    _locker = Lock()

    @classmethod
    def _hash(cls, d, key, c_type):
        """
        Hash if required or alloc
        :param d: dict
        :type d: dict
        :param key: str
        :type key: str
        :param c_type: Class to alloc if required
        :type c_type: type
        :return object
        :rtype object
        """

        if key not in d:
            with cls._locker:
                if key not in d:
                    if c_type == DelayToCountSafe:
                        d[key] = c_type(key)
                    else:
                        d[key] = c_type()
                    return d[key]

        return d[key]

    # =============================
    # RESET
    # =============================

    @classmethod
    def reset(cls):
        """
        Reset
        """

        with cls._locker:
            cls._hash_meter = {
                "a_int": dict(),
                "a_float": dict(),
                "dtc": dict()
            }

    # =============================
    # HASH / ALLOC
    # =============================

    @classmethod
    def ai(cls, key):
        """
        Get AtomicIntSafe from key, add it if required
        :param key: str
        :type key: str
        :return: AtomicIntSafe
        :rtype AtomicIntSafe
        """

        return cls._hash(cls._hash_meter["a_int"], key, AtomicIntSafe)

    @classmethod
    def af(cls, key):
        """
        Get AtomicFloatSafe from key, add it if required
        :param key: str
        :type key: str
        :return: AtomicFloatSafe
        :rtype AtomicFloatSafe
        """

        return cls._hash(cls._hash_meter["a_float"], key, AtomicFloatSafe)

    @classmethod
    def dtc(cls, key):
        """
        Get DelayToCount from key, add it if required
        :param key: str
        :type key: str
        :return: DelayToCountSafe
        :rtype DelayToCountSafe
        """

        return cls._hash(cls._hash_meter["dtc"], key, DelayToCountSafe)

    # =============================
    # INCREMENT HELPERS
    # =============================

    @classmethod
    def aii(cls, key, increment_value=1):
        """
        Get AtomicIntSafe from key, add it if required and increment
        :param key: str
        :type key: str
        :param increment_value: Value to increment
        :type increment_value: int
        :return: AtomicIntSafe
        :rtype AtomicIntSafe
        """

        ai = cls._hash(cls._hash_meter["a_int"], key, AtomicIntSafe)
        ai.increment(increment_value)
        return ai

    @classmethod
    def afi(cls, key, increment_value=1):
        """
        Get AtomicFloatSafe from key, add it if required and increment
        :param key: str
        :type key: str
        :param increment_value: Value to increment
        :type increment_value: int, float
        :return: AtomicFloatSafe
        :rtype AtomicFloatSafe
        """

        af = cls._hash(cls._hash_meter["a_float"], key, AtomicFloatSafe)
        af.increment(float(increment_value))
        return af

    @classmethod
    def dtci(cls, key, delay_ms, increment_value=1):
        """
        Get DelayToCount from key, add it if required and put
        :param key: str
        :type key: str
        :param delay_ms: Delay in millis
        :type delay_ms: int
        :param increment_value: Value to increment
        :type increment_value: int
        :return: DelayToCountSafe
        :rtype DelayToCountSafe
        """

        dtc = cls._hash(cls._hash_meter["dtc"], key, DelayToCountSafe)
        dtc.put(delay_ms, increment_value)
        return dtc

    # =============================
    # GETTER HELPERS
    # =============================

    @classmethod
    def aig(cls, key):
        """
        Get AtomicIntSafe from key, add it if required and return value
        :param key: str
        :type key: str
        :return: int
        :rtype int
        """

        ai = cls._hash(cls._hash_meter["a_int"], key, AtomicIntSafe)
        return ai.get()

    @classmethod
    def afg(cls, key):
        """
        Get AtomicFloatSafe from key, add it if required and return value
        :param key: str
        :type key: str
        :return: float
        :rtype float
        """

        af = cls._hash(cls._hash_meter["a_float"], key, AtomicFloatSafe)
        return af.get()

    # =============================
    # WRITE
    # =============================

    @classmethod
    def write_to_logger(cls):
        """
        Write
        """

        for k, d in cls._hash_meter.iteritems():
            for key, o in d.iteritems():
                if isinstance(o, (AtomicInt, AtomicIntSafe, AtomicFloat, AtomicFloatSafe)):
                    logger.info("k=%s, v=%s", key, o.get())
                elif isinstance(o, (DelayToCount, DelayToCountSafe)):
                    o.log()
                else:
                    logger.info("k=%s, o=%s", key, o)
