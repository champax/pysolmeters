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
from threading import Lock

# noinspection PyUnresolvedReferences
import ujson
from pysolbase.PlatformTools import PlatformTools
from pysolbase.SolBase import SolBase

from pysolmeters.AtomicFloat import AtomicFloatSafe, AtomicFloat
from pysolmeters.AtomicInt import AtomicIntSafe, AtomicInt
from pysolmeters.DelayToCount import DelayToCountSafe, DelayToCount
from pysolmeters.Udp.UdpClient import UdpClient

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

        for k in reversed(sorted(cls._hash_meter.keys())):
            d = cls._hash_meter[k]
            for key in sorted(d.keys()):
                o = d[key]
                if isinstance(o, (AtomicInt, AtomicIntSafe, AtomicFloat, AtomicFloatSafe)):
                    logger.info("k=%s, v=%s", key, o.get())
                elif isinstance(o, (DelayToCount, DelayToCountSafe)):
                    o.log()
                else:
                    logger.info("k=%s, o=%s", key, o)

    # =============================
    # SEND TO KNOCK DAEMON
    # =============================

    @classmethod
    def meters_to_udp_format(cls, send_pid=True):
        """
        Meter to udp
        :param send_pid: bool
        :type send_pid: bool
        :return list
        :rtype list
        """

        # ---------------------------
        # SERIALIZE
        # ---------------------------

        # List to serialize
        ar_json = list()

        # Pid
        if send_pid:
            d_tag = {"PID": str(os.getpid())}
        else:
            d_tag = {}

        # Browse and build ar_json
        for k, d in cls._hash_meter.items():
            for key, o in d.items():
                if isinstance(o, (AtomicInt, AtomicIntSafe, AtomicFloat, AtomicFloatSafe)):
                    v = o.get()
                    ar_local = [
                        # probe name
                        key,
                        # tag dict
                        d_tag,
                        # value
                        v,
                        # epoch
                        SolBase.dt_to_epoch(SolBase.datecurrent()),
                        # additional tags
                        {}
                    ]
                    ar_json.append(ar_local)
                elif isinstance(o, (DelayToCount, DelayToCountSafe)):
                    ar_dtc = o.to_udp_list(d_tag)
                    ar_json.extend(ar_dtc)
                else:
                    logger.warning("Not handled class=%s, o=%s", SolBase.get_classname(o), o)

        # Debug
        for cur_ar in ar_json:
            logger.debug("Meters serialized, cur_ar=%s", cur_ar)

        # Over
        return ar_json

    # noinspection PyProtectedMember
    @classmethod
    def send_udp_to_knockdaemon(cls, send_pid=True,
                                linux_socket_name="/var/run/knockdaemon2.udp.socket",
                                windows_host="127.0.0.1",
                                windows_port=63184):
        """
        Send all meters to knock daemon via upd.
        :param send_pid: If true, send current pid as tag (default)
        :type send_pid: bool
        :param linux_socket_name: str
        :type linux_socket_name: str
        :param windows_host: str
        :type windows_host: str
        :param windows_port: int
        :type windows_port: int
        """

        # ---------------------------
        # Serialize
        # ---------------------------
        ar_json = cls.meters_to_udp_format(send_pid)
        b_buf = SolBase.unicode_to_binary(ujson.dumps(ar_json, ensure_ascii=False), "utf-8")

        # ---------------------------
        # UDP PUSH
        # ---------------------------
        u = None
        try:
            # Alloc
            u = UdpClient()
            logger.info("Sending meters to udp, b_buf.len=%s, udp_max=%s", len(b_buf), u._max_udp_size)

            if len(b_buf) > u._max_udp_size:
                # TODO : Split ar_json in case of overload
                logger.warning("Udp size overload (possible lost), b_buf.len=%s, udp_max=%s", len(b_buf), u._max_udp_size)

            # Connect
            if PlatformTools.get_distribution_type() == "windows":
                u.connect_inet(windows_host, windows_port)
            else:
                u.connect(linux_socket_name)

            # Send
            u.send_binary(b_buf)
        finally:
            if u:
                u.disconnect()
