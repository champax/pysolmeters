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
import logging
from threading import Lock

import gevent
# noinspection PyUnresolvedReferences
import ujson
from pysolbase.Assert import Assert
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
    TODO : for aii etc... check that tags is a dict in input.
    """

    # Hash of meters
    _hash_meter = {
        "a_int": dict(),
        "a_float": dict(),
        "dtc": dict(),
        # Store tags hash => tags dict
        "tags_hash": dict(),
    }

    # Lock
    _locker = Lock()

    # ====================================
    # TAGS
    # ====================================

    @classmethod
    def _tags_hash_compute_and_store(cls, d):
        """
        Compute tags hash from a dict
        Also store hash => dict into "tag_hash" dict
        :param d: dict
        :type d: dict
        :return str
        :rtype str
        """

        s_hash = str(hash(ujson.dumps(d, sort_keys=True)))

        # Store if required
        if s_hash not in cls._hash_meter:
            with cls._locker:
                if s_hash not in cls._hash_meter:
                    cls._hash_meter["tags_hash"][s_hash] = d

        # Over
        return s_hash

    @classmethod
    def _tags_hash_get(cls, tags_hash):
        """
        Get tags dict from a tag hash
        :param tags_hash: str
        :type tags_hash: str
        :return dict
        :rtype dict
        """

        return cls._hash_meter["tags_hash"][tags_hash]

    @classmethod
    def _key_compute(cls, key, tags):
        """
        Compute key based on key name and tags

        Format is :
        <key_value>#<tags_hash> with <tags_hash> optional

        :param key: str
        :type key: str
        :param tags: dict,None
        :type tags: dict,None
        :return: str
        :rtype: str
        """

        if tags is None or len(tags) == 0:
            # Key only, with # appended
            return key + "#"
        else:
            # Compute tags hash and return "key_hash"
            return "#".join([key, cls._tags_hash_compute_and_store(tags)])

    @classmethod
    def _key_split(cls, k):
        """
        Split a key into key_value and tags_hash
        :param k: str, format is <key_value>#<tags_hash> with <tags_hash> optional
        :type k; str
        :return tuple key_value, tags_hash (may be None)
        :rtype tuple
        """

        idx = k.rfind("#")
        s_tag = k[idx + 1:]
        if len(s_tag) == 0:
            return k[:idx], None
        else:
            return k[:idx], s_tag

    @classmethod
    def _hash(cls, d, key, tags, c_type):
        """
        Hash if required or alloc
        :param d: dict
        :type d: dict
        :param key: str
        :type key: str
        :param tags: dict,None
        :type tags: dict,None
        :param c_type: Class to alloc if required
        :type c_type: type
        :return object
        :rtype object
        """

        # Compute key using key and tags
        k = cls._key_compute(key, tags)

        # Check
        if k not in d:
            with cls._locker:
                if k not in d:
                    if c_type == DelayToCountSafe or c_type == DelayToCount:
                        d[k] = c_type(key)
                    else:
                        d[k] = c_type()
                    return d[k]

        # Over
        return d[k]

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
                "dtc": dict(),
                "tags_hash": dict(),
            }
            Meters.UDP_SCHEDULER_STARTED = False
            Meters.UDP_SCHEDULER_GREENLET = None

    # =============================
    # HASH / ALLOC
    # =============================

    @classmethod
    def ai(cls, key, tags=None):
        """
        Get AtomicIntSafe from key, add it if required
        :param key: str
        :type key: str
        :param tags: dict,None
        :type tags: dict,None
        :return: AtomicIntSafe
        :rtype AtomicIntSafe
        """

        return cls._hash(cls._hash_meter["a_int"], key, tags, AtomicIntSafe)

    @classmethod
    def af(cls, key, tags=None):
        """
        Get AtomicFloatSafe from key, add it if required
        :param key: str
        :type key: str
        :param tags: dict,None
        :type tags: dict,None
        :return: AtomicFloatSafe
        :rtype AtomicFloatSafe
        """

        return cls._hash(cls._hash_meter["a_float"], key, tags, AtomicFloatSafe)

    @classmethod
    def dtc(cls, key, tags=None):
        """
        Get DelayToCount from key, add it if required
        :param key: str
        :type key: str
        :param tags: dict,None
        :type tags: dict,None
        :return: DelayToCountSafe
        :rtype DelayToCountSafe
        """

        return cls._hash(cls._hash_meter["dtc"], key, tags, DelayToCountSafe)

    # =============================
    # INCREMENT HELPERS
    # =============================

    @classmethod
    def aii(cls, key, increment_value=1, tags=None):
        """
        Get AtomicIntSafe from key, add it if required and increment
        :param key: str
        :type key: str
        :param increment_value: Value to increment
        :type increment_value: int
        :param tags: dict,None
        :type tags: dict,None
        :return: AtomicIntSafe
        :rtype AtomicIntSafe
        """

        ai = cls._hash(cls._hash_meter["a_int"], key, tags, AtomicIntSafe)
        ai.increment(increment_value)
        return ai

    @classmethod
    def afi(cls, key, increment_value=1, tags=None):
        """
        Get AtomicFloatSafe from key, add it if required and increment
        :param key: str
        :type key: str
        :param increment_value: Value to increment
        :type increment_value: int, float
        :param tags: dict,None
        :type tags: dict,None
        :return: AtomicFloatSafe
        :rtype AtomicFloatSafe
        """

        af = cls._hash(cls._hash_meter["a_float"], key, tags, AtomicFloatSafe)
        af.increment(float(increment_value))
        return af

    @classmethod
    def dtci(cls, key, delay_ms, increment_value=1, tags=None):
        """
        Get DelayToCount from key, add it if required and put
        :param key: str
        :type key: str
        :param delay_ms: Delay in millis
        :type delay_ms: int
        :param increment_value: Value to increment
        :type increment_value: int
        :param tags: dict,None
        :type tags: dict,None
        :return: DelayToCountSafe
        :rtype DelayToCountSafe
        """

        dtc = cls._hash(cls._hash_meter["dtc"], key, tags, DelayToCountSafe)
        dtc.put(delay_ms, increment_value)
        return dtc

    # =============================
    # GETTER HELPERS
    # =============================

    @classmethod
    def aig(cls, key, tags=None):
        """
        Get AtomicIntSafe from key, add it if required and return value
        :param key: str
        :type key: str
        :param tags: dict,None
        :type tags: dict,None
        :return: int
        :rtype int
        """

        ai = cls._hash(cls._hash_meter["a_int"], key, tags, AtomicIntSafe)
        return ai.get()

    @classmethod
    def afg(cls, key, tags=None):
        """
        Get AtomicFloatSafe from key, add it if required and return value
        :param key: str
        :type key: str
        :param tags: dict,None
        :type tags: dict,None
        :return: float
        :rtype float
        """

        af = cls._hash(cls._hash_meter["a_float"], key, tags, AtomicFloatSafe)
        return af.get()

    # =============================
    # WRITE
    # =============================

    @classmethod
    def tags_format_for_logger(cls, tags):
        """
        Format tags for logger
        :param tags: dict
        :type tags: dict
        :return str
        :rtype str
        """

        if not tags:
            return ""
        elif len(tags) == 0:
            return ""
        else:
            ar_tags = list()
            for k in sorted(tags.keys()):
                v = tags[k]
                ar_tags.append("%s:%s" % (k, v))
            s_tags = " (%s) " % ",".join(ar_tags)
            return s_tags

    @classmethod
    def write_to_logger(cls):
        """
        Write
        """

        for k in reversed(sorted(cls._hash_meter.keys())):
            # Skip tags
            if k in ["tags_hash"]:
                continue

            # Ok
            d = cls._hash_meter[k]
            for key in sorted(d.keys()):
                # Get object
                o = d[key]

                # Split key and tags
                cur_key, cur_tags_hash = cls._key_split(key)

                # Get tags
                if cur_tags_hash:
                    d_tags = cls._tags_hash_get(cur_tags_hash)
                    s_tags = cls.tags_format_for_logger(d_tags)
                else:
                    s_tags = ""

                # Atomic
                if isinstance(o, (AtomicInt, AtomicIntSafe, AtomicFloat, AtomicFloatSafe)):
                    logger.debug("k=%s%s, v=%s", cur_key, s_tags, o.get())
                # DelayToCount
                elif isinstance(o, (DelayToCount, DelayToCountSafe)):
                    o.log(s_tags)
                # Other
                else:
                    logger.debug("k=%s%s, o=%s", cur_key, s_tags, o)

    # =============================
    # SEND TO KNOCK DAEMON
    # =============================

    # noinspection PyUnusedLocal
    @classmethod
    def meters_to_udp_format(cls, send_pid=True, send_tags=True, send_dtc=False):
        """
        Meter to udp
        :param send_pid: bool (DEPRECATED)
        :type send_pid: bool
        :param send_tags : bool
        :type send_tags : bool
        :param send_dtc: If true, send DelayToCount. Disabled by default (not efficient histogram push).
        :param send_dtc: bool
        :return list
        :rtype list
        """

        # ---------------------------
        # SERIALIZE
        # ---------------------------

        # List to serialize
        ar_json = list()

        # We do NOT sent anymore PID (daemon will kick it)
        d_tag = {}

        # Browse and build ar_json
        for k, d in cls._hash_meter.items():
            # Skip tags
            if k in ["tags_hash"]:
                continue

            for key, o in d.items():

                # Split key / tags_hash
                cur_key, cur_tags_hash = cls._key_split(key)

                # If tags : update d_tag
                if send_tags and cur_tags_hash:
                    d_cur_tags = cls._tags_hash_get(cur_tags_hash)
                    d_cur_tags.update(d_tag)
                else:
                    d_cur_tags = dict()
                    d_cur_tags.update(d_tag)

                if isinstance(o, (AtomicInt, AtomicIntSafe, AtomicFloat, AtomicFloatSafe)):
                    v = o.get()
                    ar_local = [
                        # probe name
                        cur_key,
                        # tag dict
                        d_cur_tags,
                        # value
                        v,
                        # epoch
                        SolBase.dt_to_epoch(SolBase.datecurrent()),
                        # additional tags
                        {}
                    ]
                    ar_json.append(ar_local)
                elif isinstance(o, (DelayToCount, DelayToCountSafe)):
                    if send_dtc:
                        ar_dtc = o.to_udp_list(d_cur_tags)
                        ar_json.extend(ar_dtc)
                else:
                    logger.warning("Not handled class=%s, o=%s", SolBase.get_classname(o), o)

        # Debug
        for cur_ar in ar_json:
            logger.debug("Meters serialized, cur_ar=%s", cur_ar)

        # Over
        return ar_json

    # =================================
    # UDP SEND
    # =================================

    @classmethod
    def chunk_udp_array_via_serialization(cls, ar_json, max_size_bytes):
        """
        Chunk a daemon udp list (list of list) toward a list of binary buffer, ready for udp send
        This method uses per item serialization with manual concatenations.
        :param ar_json: list of list
        :type ar_json: list
        :param max_size_bytes: int (max size of each binary buffer)
        :type max_size_bytes: int
        :return: list of binary buffer, list of chunked ar_json inner items (list of list of list)
        :rtype tuple
        """

        # Check
        if ar_json is None or len(ar_json) == 0:
            return list(), list()

        # We are going to serialize as :
        # [
        #   [...],
        #   [...]
        # ]

        ar_bin_out = list()
        ar_json_out = list()

        # Temp array
        ar_temp_s = list()
        ar_temp_ar = list()

        # Current temp bytes (with opening [ and closing ] and a margin for "," => so init to 3)
        cur_temp_bytes = 3

        # Browse
        for cur_ar in ar_json:
            # Serialize this one
            s_cur_ar = ujson.dumps(cur_ar)
            cur_len = len(s_cur_ar)

            # Check
            if cur_temp_bytes + cur_len > max_size_bytes:
                # -----------------------------
                # Got overload => close this one and initialize a new one
                # -----------------------------
                s_final = "[" + ",".join(ar_temp_s) + "]"
                b_final = SolBase.unicode_to_binary(s_final, "utf8")
                Assert.check(len(b_final) <= max_size_bytes, "Got overload, cur=%s, max=%s" % (len(b_final), max_size_bytes))

                # Push output
                ar_bin_out.append(b_final)
                ar_json_out.append(ar_temp_ar)

                # Re-init with current item
                cur_temp_bytes = 3 + cur_len
                ar_temp_s = [s_cur_ar]
                ar_temp_ar = [cur_ar]
            else:
                # -----------------------------
                # Accumulate
                # -----------------------------

                # +1 for the ","
                cur_temp_bytes += cur_len + 1
                ar_temp_s.append(s_cur_ar)
                ar_temp_ar.append(cur_ar)

        # -----------------------------
        # Finish it if we have pending
        # -----------------------------
        if len(ar_temp_s) > 0:
            s_final = "[" + ",".join(ar_temp_s) + "]"
            b_final = SolBase.unicode_to_binary(s_final, "utf8")
            Assert.check(len(b_final) < max_size_bytes, "Got overload, cur=%s, max=%s" % (len(b_final), max_size_bytes))

            # Push
            ar_bin_out.append(b_final)
            ar_json_out.append(ar_temp_ar)

        # -----------------------------
        # Over
        # -----------------------------
        return ar_bin_out, ar_json_out

    # noinspection PyProtectedMember
    @classmethod
    def send_udp_to_knockdaemon(
            cls,
            send_pid=True,
            send_tags=True,
            send_dtc=False,
            linux_socket_name="/var/run/knockdaemon2.udp.socket",
            windows_host="127.0.0.1",
            windows_port=63184):
        """
        Send all meters to knock daemon via upd.
        :param send_pid: If true, send current pid as tag (default)
        :type send_pid: bool
        :param send_tags: Send custom tags (default True)
        :type send_tags: bool
        :param send_dtc: If true, send DelayToCount. Disabled by default (not efficient histogram push).
        :param send_dtc: bool
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
        ar_json = cls.meters_to_udp_format(
            send_pid=send_pid,
            send_tags=send_tags,
            send_dtc=send_dtc,
        )

        # ---------------------------
        # UDP PUSH
        # ---------------------------
        u = None
        try:
            # Alloc
            u = UdpClient()

            # ar_json is a list of list
            # we have a maximum size, we must chunk it....
            ar_bin_chunk, _ = cls.chunk_udp_array_via_serialization(
                ar_json=ar_json,
                max_size_bytes=u._max_udp_size,
            )

            # Connect
            if PlatformTools.get_distribution_type() == "windows":
                u.connect_inet(windows_host, windows_port)
            else:
                u.connect(linux_socket_name)

            # Fire
            i = 0
            for b_buf in ar_bin_chunk:
                i += 1
                if len(b_buf) > u._max_udp_size:
                    logger.warning("Udp size overload (possible lost), b_buf.len=%s, udp_max=%s", len(b_buf), u._max_udp_size)

                # Send
                logger.debug("Sending meters to udp (chunked), b_buf.len=%s, chunks=%s/%s, udp_max=%s", len(b_buf), i, len(ar_bin_chunk), u._max_udp_size)

                u.send_binary(b_buf)

                # Switch
                SolBase.sleep(0)
        finally:
            if u:
                u.disconnect()

    # =================================
    # UDP SCHEDULER
    # =================================

    UDP_SCHEDULER_LOCK = Lock()
    UDP_SCHEDULER_STARTED = False
    UDP_SCHEDULER_GREENLET = None

    @classmethod
    def udp_scheduler_start(
            cls,
            send_interval_ms=60000,
            send_pid=True,
            send_tags=True,
            send_dtc=False,
            linux_socket_name="/var/run/knockdaemon2.udp.socket",
            windows_host="127.0.0.1",
            windows_port=63184):
        """
        Start udp send scheduler to daemon.
        :param send_interval_ms: int
        :type send_interval_ms: int
        :param send_pid: If true, send current pid as tag (default)
        :type send_pid: bool
        :param send_tags: Send custom tags (default True)
        :type send_tags: bool
        :param send_dtc: If true, send DelayToCount. Disabled by default (not efficient histogram push).
        :param send_dtc: bool
        :param linux_socket_name: str
        :type linux_socket_name: str
        :param windows_host: str
        :type windows_host: str
        :param windows_port: int
        :type windows_port: int
        """

        with Meters.UDP_SCHEDULER_LOCK:
            if Meters.UDP_SCHEDULER_STARTED:
                logger.warning("Already started, exiting")
                return

            # Schedule
            Meters.UDP_SCHEDULER_GREENLET = gevent.spawn_later(
                send_interval_ms * 0.001,
                cls.udp_scheduler_run,
                send_interval_ms,
                send_pid,
                send_tags,
                send_dtc,
                linux_socket_name,
                windows_host,
                windows_port,
            )

            # Ok
            Meters.UDP_SCHEDULER_STARTED = True
            logger.info("Udp scheduler started")

    @classmethod
    def udp_scheduler_stop(cls):
        """
        Stop udp scheduler
        """
        with Meters.UDP_SCHEDULER_LOCK:
            # Reset greenlet in all cases
            Meters.UDP_SCHEDULER_GREENLET = None

            # Check
            if not Meters.UDP_SCHEDULER_STARTED:
                logger.warning("Already stopped, exiting")
                return

            Meters.UDP_SCHEDULER_STARTED = False
            logger.info("Udp scheduler stopped")

    @classmethod
    def udp_scheduler_run(
            cls,
            send_interval_ms=60000,
            send_pid=True,
            send_tags=True,
            send_dtc=False,
            linux_socket_name="/var/run/knockdaemon2.udp.socket",
            windows_host="127.0.0.1",
            windows_port=63184):
        """
        Udp scheduler run (push to daemon and re-schedule if required.
        :param send_interval_ms: int
        :type send_interval_ms: int
        :param send_pid: If true, send current pid as tag (default)
        :type send_pid: bool
        :param send_tags: Send custom tags (default True)
        :type send_tags: bool
        :param send_dtc: If true, send DelayToCount. Disabled by default (not efficient histogram push).
        :param send_dtc: bool
        :param linux_socket_name: str
        :type linux_socket_name: str
        :param windows_host: str
        :type windows_host: str
        :param windows_port: int
        :type windows_port: int
        """

        try:
            # If not started, exit
            if not Meters.UDP_SCHEDULER_STARTED:
                return

            # Push to daemon
            cls.send_udp_to_knockdaemon(
                send_pid,
                send_tags,
                send_dtc,
                linux_socket_name,
                windows_host,
                windows_port
            )

            # Stat
            logger.debug("Udp scheduler push ok")
            Meters.aii("k.meters.udp.run.ok")
        except Exception as e:
            logger.warning("Ex=%s", SolBase.extostr(e))
            Meters.aii("k.meters.udp.run.ex")
        finally:
            # Re-schedule if required
            if Meters.UDP_SCHEDULER_STARTED:
                Meters.UDP_SCHEDULER_GREENLET = gevent.spawn_later(
                    send_interval_ms * 0.001,
                    cls.udp_scheduler_run,
                    send_interval_ms,
                    send_pid,
                    send_tags,
                    send_dtc,
                    linux_socket_name,
                    windows_host,
                    windows_port,
                )
