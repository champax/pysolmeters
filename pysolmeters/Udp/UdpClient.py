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
import socket

from pysolbase.SolBase import SolBase

logger = logging.getLogger(__name__)


class UdpClient(object):
    """
    Udp client
    """

    def __init__(self, max_udp_size=61440):
        """
        Constructor
        For max udp size, refer to internet (ie http://stackoverflow.com/questions/14993000/the-most-reliable-and-efficient-udp-packet-size)
        As we act mostly on localhost, and MTU localhost is 65536, we assume a default of 61440 (we take some margin)
        :param max_udp_size: int
        :type max_udp_size: int
        """

        self._max_udp_size = max_udp_size
        self._soc = None

    def connect(self, socket_name):
        """
        Connect (not available on windows)
        :param socket_name: str
        :type socket_name: str
        """

        try:
            self._soc = socket.socket(socket.AF_UNIX, type=socket.SOCK_DGRAM)
            self._soc.connect(socket_name)
        except Exception as e:
            logger.warning("connect failed, ex=%s", SolBase.extostr(e))
            raise

    def connect_inet(self, host, port):
        """
        Connect
        :param host: str
        :type host: str
        :param port: int
        :type port: int
        """

        try:
            self._soc = socket.socket(socket.AF_INET, type=socket.SOCK_DGRAM)
            self._soc.connect((host, port))
        except Exception as e:
            logger.warning("connect failed, ex=%s", SolBase.extostr(e))
            raise

    def disconnect(self):
        """
        Disconnect
        """

        if self._soc:
            SolBase.safe_close_socket(self._soc)
            self._soc = None

    def send_binary(self, bin_buf):
        """
        Send binary
        :param bin_buf: str
        :type bin_buf: str
        """

        if not self._soc:
            raise Exception("No socket")

        try:
            self._soc.sendall(bin_buf)
        except Exception as e:
            logger.warning("send failed, ex=%s", SolBase.extostr(e))
            raise
