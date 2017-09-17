pysolmeters
============

Welcome to pysol

Copyright (C) 2013/2017 Laurent Labatut / Laurent Champagnac

pysolmeters is a set of python helpers to populate and get counters, anywhere in the code.

It can be used to instrument low-level APIs and validate stuff with unit testing or push counters toward some monitoring softwares.

Internally, it uses AtomicIntSafe, AtomicFloatSafe and DelayToCountSafe classes, wrapped by a static class Meters, which exposes helper methods.

Usage
===============

To increment integers and floats :

```
Meters.aii("int_counter")
Meters.afi("float_counter")
```

To get integers and floats :

```
vi = Meters.aig("int_counter")
vf = Meters.afg("float_counter")
```

To put millis toward DelayToCount :

```
Meters.dtci("dtc1", 0.5)
```

To get DelayToCount instance

```
dtc1 = Meters.dtcg("dtc1")
```

To write all counters to logger :

```
Meters.write_to_logger()
```

To reset all counters :

```
Meters.reset()
```

Source code
===============

- We are pep8 compliant (as far as we can, with some exemptions)
- We use a right margin of 360 characters (please don't talk me about 80 chars)
- All unittest files must begin with `test_` or `Test`, should implement setUp and tearDown methods
- All tests must adapt to any running directory
- The whole project is backed by gevent (http://www.gevent.org/)
- We use docstring (:return, :rtype, :param, :type etc..), they are mandatory
- We use PyCharm "noinspection", feel free to use them

Requirements
===============

- Debian 8 Jessie or greater, x64, Python 2.7

Unittests
===============

To run unittests, you will need:

- nothing special except python and dependencies requirements.

License
===============

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA


