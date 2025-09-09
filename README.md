pysolmeters
============

Welcome to pysol

Copyright (C) 2013/2025 Laurent Labatut / Laurent Champagnac

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

