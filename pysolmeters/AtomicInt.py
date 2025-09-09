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
from threading import Lock


class AtomicInt(object):
    """
    Atomic integer without lock.
    """

    UINT64_MAX = 18446744073709551615

    def __init__(self, initial_value=0, maximum_value=UINT64_MAX):
        """
        Init
        :param initial_value: Initial value
        :type initial_value: int
        :param maximum_value: Maximum value (default : UINT64)
        :type maximum_value: int
        :return Nothing
        """

        self._current_value = initial_value
        self.maximum_value = maximum_value
        self._process_max_value()

    def increment(self, increment_value=1):
        """
        Increment and return current value
        :param increment_value: Increment value
        :type increment_value: int
        :return Current value
        :rtype int
        """

        self._current_value += increment_value
        self._process_max_value()
        return self._current_value

    def set(self, current_value):
        """
        Set current value
        :param current_value: New current value
        :type current_value: int
        :return Current value
        :rtype int
        """

        self._current_value = current_value
        self._process_max_value()
        return self._current_value

    def get(self):
        """
        Get current value
        :return Current value
        :rtype int
        """
        return self._current_value

    def _process_max_value(self):
        """
        Process max value if required
        :return Nothing
        """

        if self.maximum_value and self._current_value > self.maximum_value:
            # Compute & reset with reminder if maximum value reached
            div = int(self._current_value / self.maximum_value)
            reminder = self._current_value % self.maximum_value
            if div > 0:
                if reminder == 0:
                    self._current_value = self.maximum_value
                else:
                    self._current_value = reminder
            else:
                self._current_value = reminder


class AtomicIntSafe(AtomicInt):
    """
    Safe atomic integer with lock.
    """

    def __init__(self, initial_value=0, maximum_value=AtomicInt.UINT64_MAX):
        """
        Init
        :param initial_value: Initial value
        :type initial_value: int
        :param maximum_value: Maximum value (default : UINT64)
        :type maximum_value: int
        :return Nothing
        """

        self._lock = Lock()
        with self._lock:
            AtomicInt.__init__(self, initial_value, maximum_value)

    def increment(self, increment_value=1):
        """
        Increment and return current value
        :param increment_value: Increment value
        :type increment_value: int
        :return Current value
        :rtype int
        """

        with self._lock:
            return AtomicInt.increment(self, increment_value)

    def set(self, current_value):
        """
        Set current value
        :param current_value: New current value
        :type current_value: int
        :return Current value
        :rtype int
        """

        with self._lock:
            return AtomicInt.set(self, current_value)

    def get(self):
        """
        Get current value
        :return Current value
        :rtype int
        """
        with self._lock:
            return AtomicInt.get(self)
