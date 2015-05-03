#!/usr/bin/python
"""
This module provides some basic helper/formatting utilities,
specifically targeted at decoding ReadHistoryData data.

"""
import io
from binascii import hexlify

import lib
from records import *

_remote_ids = [
  bytearray([ 0x01, 0xe2, 0x40 ]),
  bytearray([ 0x03, 0x42, 0x2a ]),
  bytearray([ 0x0c, 0x89, 0x92 ]),
]

def decode_remote_id(msg):
  """
  practice decoding some remote ids:

  | 0x27
  | 0x01 0xe2 0x40
  | 0x03 0x42 0x2a
  | 0x28 0x0c 0x89
  | 0x92 0x00 0x00 0x00

  >>> decode_remote_id(_remote_ids[0])
  '123456'

  >>> decode_remote_id(_remote_ids[1])
  '213546'

  >>> decode_remote_id(_remote_ids[2])
  '821650'



  """
  high   = msg[ 0 ] * 256 * 256
  middle = msg[ 1 ] * 256
  low    = msg[ 2 ]
  return str(high + middle + low)

class NoDelivery(KnownRecord):
  opcode = 0x06
  head_length = 4
#class ResultTotals(KnownRecord):
class MResultTotals(InvalidRecord):
  """On 722 this seems like two records."""
  opcode = 0x07
  #head_length = 5
  head_length = 5
  date_length = 2
  #body_length = 37 + 4
  #body_length = 2
  def __init__(self, head, larger=False):
    super(type(self), self).__init__(head, larger)
    if self.larger:
      self.body_length = 3
  def parse_time(self):
    date = parse_midnight(self.date)
    self.datetime = date
    if not hasattr(date, 'isoformat'):
      self.datetime = None
    return date


  def date_str(self):
    result = 'unknown'
    if self.datetime is not None:
      result = self.datetime.isoformat( )
    else:
      if len(self.date) >=2:
        result = "{}".format(unmask_m_midnight(self.date))
    return result

class ChangeBasalProfile_old_profile (KnownRecord):
  opcode = 0x08
  # old/bad
  # body_length = 46
  # XXX: on LeDanaScott's, 522, this seems right
  body_length = 145
  # head_length = 3 # XXX: # for 554!?
  def __init__(self, head, larger=False):
    super(type(self), self).__init__(head, larger)
    if self.larger:
      self.body_length = 145
  def decode (self):
    self.parse_time( )
    rates = [ ]
    i = 0
    for x in range(47):
      start = x * 3
      end = start + 3
      (offset, rate, q) = self.body[start:end]
      if [offset, rate, q] == [ 0x00, 0x00, 0x00]:
        break
      try:
        rates.append(describe_rate(offset, rate, q))
      except TypeError, e:
        remainder = [ offset, rate, q ]
        rates.append(remainder)
    return rates

def describe_rate (offset, rate, q):
  return (dict(offset=(30*1000*60)*offset, rate=rate*0.025))


class ChangeBasalProfile_new_profile (KnownRecord):
  opcode = 0x09
  body_length = 145
  # body_length = 144 # XXX: # for 554!?
  # head_length = 3 # XXX: # for 554!?
  def decode (self):
    self.parse_time( )
    rates = [ ]
    i = 0
    for x in range(47):
      start = x * 3
      end = start + 3
      (offset, rate, q) = self.body[start:end]
      if [offset, rate, q] == [ 0x00, 0x00, 0x00]:
        break
      rates.append(describe_rate(offset, rate, q))
    return rates
class ClearAlarm(KnownRecord):
  opcode = 0x0C
class SelectBasalProfile(KnownRecord):
  opcode = 0x14
class ChangeTime(KnownRecord):
  opcode = 0x17
class NewTimeSet(KnownRecord):
  opcode = 0x18
class LowBattery(KnownRecord):
  opcode = 0x19
class Battery(KnownRecord):
  opcode = 0x1a
class PumpSuspend(KnownRecord):
  opcode = 0x1e
class PumpResume(KnownRecord):
  opcode = 0x1f

class Rewind(KnownRecord):
  opcode = 0x21

class EnableDisableRemote(KnownRecord):
  opcode = 0x26
  # body_length = 14
  # head_length = 3 # XXX: for 554
  body_length = 14
class ChangeRemoteID(KnownRecord):
  opcode = 0x27

class TempBasalDuration(KnownRecord):
  opcode = 0x16
  _test_1 = bytearray([ ])
  def decode(self):
    self.parse_time( )
    basal = { 'duration (min)': self.head[1] * 30, }
    return basal
class TempBasal(KnownRecord):
  opcode = 0x33
  body_length = 1
  _test_1 = bytearray([ ])
  def decode(self):
    self.parse_time( )
    basal = { 'rate': self.head[1] / 40.0, }
    return basal

class LowReservoir(KnownRecord):
  """
  >>> rec = LowReservoir( LowReservoir._test_1[:2] )
  >>> decoded = rec.parse(LowReservoir._test_1)
  >>> print str(rec)
  LowReservoir 2012-12-07T11:02:43 head[2], body[0] op[0x34]

  >>> print pformat(decoded)
  {'amount': 20.0}
  """
  opcode = 0x34
  _test_1 = bytearray([ 0x34, 0xc8,
                        0xeb, 0x02, 0x0b, 0x07, 0x0c, ])
  def decode(self):
    self.parse_time( )
    reservoir = {'amount' : int(self.head[1]) / 10.0 }
    return reservoir


class ChangeUtility(KnownRecord):
  opcode = 0x63
class ChangeTimeDisplay(KnownRecord):
  opcode = 0x64

_confirmed = [ Bolus, Prime, NoDelivery, MResultTotals,
               ChangeBasalProfile_old_profile,
               ChangeBasalProfile_new_profile,
               ClearAlarm, SelectBasalProfile, TempBasalDuration, ChangeTime,
               NewTimeSet, LowBattery, Battery, PumpSuspend,
               PumpResume, CalBGForPH, Rewind, EnableDisableRemote,
               ChangeRemoteID, TempBasal, LowReservoir, BolusWizard,
               UnabsorbedInsulinBolus, ChangeUtility, ChangeTimeDisplay ]

# _confirmed.append(DanaScott0x09)

class Ian69(KnownRecord):
  opcode = 0x69
  body_length = 2
_confirmed.append(Ian69)

class Ian50(KnownRecord):
  opcode = 0x50
  body_length = 34
_confirmed.append(Ian50)

class Ian54(KnownRecord):
  opcode = 0x54
  body_length = 34 + 23
  body_length = 57
_confirmed.append(Ian54)

class SensorAlert (KnownRecord):
  opcode = 0x0B
  head_length = 3
  def decode (self):
    self.parse_time( )
    amount = self.head[2]
    return dict(alarm_type=self.head[1], amount_maybe=amount)
_confirmed.append(SensorAlert)

class BGReceived (KnownRecord):
  opcode = 0x3F
  body_length = 3
  def decode (self):
    self.parse_time( )
    return dict(link=str(self.body).encode('hex'), amount='???')
_confirmed.append(BGReceived)

class IanA8(KnownRecord):
  opcode = 0xA8
  head_length = 10
_confirmed.append(IanA8)

class BasalProfileStart(KnownRecord):
  opcode = 0x7b
  body_length = 3
  def __init__(self, head, larger=False):
    super(type(self), self).__init__(head, larger)
    if self.larger:
      # body_length = 1
      pass
      # self.body_length = 48
  def decode (self):
    self.parse_time( )
    if (len(self.body) % 3 == 0):
      return describe_rate(*self.body)
    else:
      return dict(raw=hexlify(self.body))
_confirmed.append(BasalProfileStart)

# 123, 143
class OldBolusWizardChange (KnownRecord):
  opcode = 0x5a
  body_length = 117
  def __init__(self, head, larger=False):
    super(type(self), self).__init__(head, larger)
    if self.larger:
      self.body_length = 117 + 17 + 3
      pass
  def decode (self):
    self.parse_time( )
    half = (self.body_length - 1) / 2
    stale = self.body[0:half]
    changed = self.body[half:-1]
    tail = self.body[-1]
    return dict(stale=decode_wizard_settings(stale)
    # , _changed=changed
    , changed=decode_wizard_settings(changed)
    , tail=tail
    )

_confirmed.append(OldBolusWizardChange)
def decode_wizard_settings (data, num=8):
  head = data[0:2]
  tail = data[len(head):]
  carb_ratios = tail[0:num*3]
  tail = tail[num*3:]
  insulin_sensitivies = tail[0:(num*2)]
  tail = tail[num*2:]
  isMg = head[0] & 0b00000100
  isMmol = head[0] & 0b00001000
  bg_units = 1
  if isMmol and not isMg:
    bg_units = 2
  bg_targets = tail[0:(num*3)+2]
  return dict(head=str(head).encode('hex')
  , carb_ratios=decode_carb_ratios(carb_ratios)
  # , _carb_ratios=str(carb_ratios).encode('hex')
  # , cr_len=len(carb_ratios)
  , insulin_sensitivies=decode_insulin_sensitivies(insulin_sensitivies)
  # , _insulin_sensitivies=str(insulin_sensitivies).encode('hex')
  # , is_len=len(insulin_sensitivies)
  # , bg_len=len(bg_targets)
  , bg_targets=decode_bg_targets(bg_targets, bg_units)
  # , _o_len=len(data)
  # , _bg_targets=str(bg_targets).encode('hex')
  , _head = "{0:#010b} {1:#010b}".format(*head)
  )

def decode_carb_ratios (data):
  ratios = [ ]
  for x in range(8):
    start = x * 3
    end = start + 3
    (offset, q, r) = data[start:end]
    ratio = r/10.0
    if q:
      ratio = lib.BangInt([q, r]) / 1000.0
    ratios.append(dict(i=x, offset=offset*30, q=q, _offset=offset,
                       ratio=ratio, r=r))
  return ratios

def decode_insulin_sensitivies (data):
  sensitivities = [ ]
  for x in range(8):
    start = x * 2
    end = start + 2
    (offset, sensitivity) = data[start:end]
    sensitivities.append(dict(i=x, offset=offset*30, _offset=offset,
                       sensitivity=sensitivity))
  return sensitivities

def decode_bg_targets (data, bg_units):
  data = data[2:]
  targets = [ ]
  for x in range(8):
    start = x * 3
    end = start + 3
    # (low, high, offset) = data[start:end]
    (offset, low, high) = data[start:end]
    if bg_units is 2:
      low = low / 10.0
      high = high / 10.0
    targets.append(dict( #i=x,
                       offset=offset*30, _offset=offset,
                       # _raw=str(data[start:end]).encode('hex'),
                       low=low, high=high))
  return targets 

class BigBolusWizardChange (KnownRecord):
  opcode = 0x5a
  body_length = 143

class SetAutoOff (KnownRecord):
  opcode = 0x1b
_confirmed.append(SetAutoOff)

class SetEasyBolusEnabled (KnownRecord):
  opcode = 0x5f
_confirmed.append(SetEasyBolusEnabled)

class hack83 (KnownRecord):
  opcode = 0x83
  # body_length = 1
_confirmed.append(hack83)

class hack53 (KnownRecord):
  opcode = 0x53
  body_length = 1
_confirmed.append(hack53)

class hack52 (KnownRecord):
  opcode = 0x52
  # body_length = 1
_confirmed.append(hack52)

class hack51 (KnownRecord):
  opcode = 0x51
  # body_length = 1
_confirmed.append(hack51)

class hack55 (KnownRecord):
  opcode = 0x55
  # body_length = 1 + 47
  # body_length = 2 + 46
  def __init__(self, head, larger=False):
    super(type(self), self).__init__(head, larger)
    # self.larger = larger
    self.body_length = (self.head[1] - 1) * 3
_confirmed.append(hack55)


class hack56 (KnownRecord):
  opcode = 0x56
  body_length = 5
_confirmed.append(hack56)

class hack82 (KnownRecord):
  opcode = 0x82
  body_length = 5
_confirmed.append(hack82)

class hack7d (KnownRecord):
  opcode = 0x7d
  body_length = 30
_confirmed.append(hack7d)

class SetBolusWizardEnabled (KnownRecord):
  opcode = 0x2d
  def decode (self):
    self.parse_time( )
    return dict(enabled=self.head[1] is 1)
_confirmed.append(SetBolusWizardEnabled)


class SettingSomething57 (KnownRecord):
  opcode = 0x57
  # body_length = 1
_confirmed.append(SettingSomething57)

class questionable2c (KnownRecord):
  opcode = 0x2c
_confirmed.append(questionable2c)

class questionable22 (KnownRecord):
  opcode = 0x22
_confirmed.append(questionable22)

class questionable23 (KnownRecord):
  opcode = 0x23
_confirmed.append(questionable23)

class questionable24 (KnownRecord):
  opcode = 0x24
_confirmed.append(questionable24)

class questionable60 (KnownRecord):
  opcode = 0x60
_confirmed.append(questionable60)

class questionable61 (KnownRecord):
  opcode = 0x61
_confirmed.append(questionable61)

class hack62 (KnownRecord):
  opcode = 0x62
  # body_length = 1
_confirmed.append(hack62)

class questionable65 (KnownRecord):
  opcode = 0x65
_confirmed.append(questionable65)

class questionable66 (KnownRecord):
  opcode = 0x66
_confirmed.append(questionable66)

class questionable6f (KnownRecord):
  opcode = 0x6f
_confirmed.append(questionable6f)

class questionable5e (KnownRecord):
  opcode = 0x5e
_confirmed.append(questionable5e)

class questionable3c (KnownRecord):
  opcode = 0x3c
  body_length = 14
_confirmed.append(questionable3c)


class questionable7c (KnownRecord):
  opcode = 0x7c
_confirmed.append(questionable7c)

class Model522ResultTotals(KnownRecord):
  opcode = 0x6d
  head_length = 1
  date_length = 2
  body_length = 40
  def parse_time(self):
    date = parse_midnight(self.date)
    self.datetime = date
    if not hasattr(date, 'isoformat'):
      self.datetime = None
    return date

  def date_str(self):
    result = 'unknown'
    if self.datetime is not None:
      result = self.datetime.isoformat( )
    else:
      if len(self.date) >=2:
        result = "{}".format(unmask_m_midnight(self.date))
    return result

# class Model522ResultTotals(KnownRecord):
class old6c(Model522ResultTotals):
  opcode = 0x6c
  #head_length = 45
  #xxx non 515
  # body_length = 38
  # body_length = 34
  # XXX: 515 only?
  # body_length = 31
  def __init__ (self, head, model, **kwds):
    super(old6c, self).__init__(head, model, **kwds)
    self.body_length = model.old6cBody + 3
_confirmed.append(old6c)

class questionable3b (KnownRecord):
  opcode = 0x3b
_confirmed.append(questionable3b)


from dateutil.relativedelta import relativedelta
def parse_midnight (data):
    mid = unmask_m_midnight(data)
    oneday = relativedelta(days=1)
    try:
      date = datetime(*mid) + oneday
      return date
    except ValueError, e:
      print "ERROR", e, lib.hexdump(data)
      pass
    return mid

def unmask_m_midnight(data):
  """
  Extract date values from a series of bytes.
  Always returns tuple given a bytearray of at least 3 bytes.

  Returns 6-tuple of scalar values year, month, day, hours, minutes,
  seconds.

  """
  data = data[:]
  seconds = 0
  minutes = 0
  hours   = 0

  day     = parse_day(data[0])

  high = data[0] >> 4
  low  = data[0] & 0x1F

  year_high = data[1] >> 4
  # month = int(high) #+ year_high
  # month   = parse_months( data[0], data[1] )
  mhigh = (data[0] & 0xE0) >> 4
  mlow  = (data[1] & 0x80) >> 7
  month =  int(mhigh + mlow)
  day = int(low)

  year = parse_years(data[1])
  return (year, month, day, hours, minutes, seconds)

_confirmed.append(Model522ResultTotals)

class Sara6E(Model522ResultTotals):
  """Seems specific to 722?"""
  opcode = 0x6e
  #head_length = 52 - 5
  # body_length = 1
  body_length = 48
  #body_length = 0
  def __init__(self, head, larger=False):
    super(type(self), self).__init__(head, larger)
    if self.larger:
      self.body_length = 48
_confirmed.append(Sara6E)

_known = { }

_variant = { }

for x in _confirmed:
  _known[x.opcode] = x

del x

def suggest(head, larger=False, model=None):
  """
  Look in the known table of commands to find a suitable record type
  for this opcode.
  """
  klass = _known.get(head[0], Base)
  record = klass(head, model)
  return record

def parse_record(fd, head=bytearray( ), larger=False, model=None):
  """
  Given a file-like object, and the head of a record, parse the rest
  of the record.
  Look up the type of record, read in just enough data to parse it,
  return the result.
  """
  # head    = bytearray(fd.read(2))
  date    = bytearray( )
  body    = bytearray( )
  record  = suggest(head, larger, model=model)
  remaining = record.head_length - len(head)
  if remaining > 0:
    head.extend(bytearray(fd.read(remaining)))
  if record.date_length > 0:
    date.extend(bytearray(fd.read(record.date_length)))
  if record.body_length > 0:
    body.extend(bytearray(fd.read(record.body_length)))
  record.parse( head + date + body )
  # print str(record)
  # print record.pformat(prefix=str(record) )
  return record


def describe( ):
  keys = _known.keys( )
  out  = [ ]
  for k in keys:
    out.append(_known[k].describe( ))
  return out

class PagedData (object):
  """
    PagedData - context for parsing a page of cgm data.
  """

  def __init__ (self, raw, model):
    self.model = model
    data, crc = raw[0:1022], raw[1022:]
    computed = lib.CRC16CCITT.compute(bytearray(data))
    if lib.BangInt(crc) != computed:
      assert lib.BangInt(crc) == computed, "CRC does not match page data"

    self.raw = raw
    self.clean(data)

  def clean (self, data):
    data.reverse( )
    self.data = self.eat_nulls(data)
    self.stream = io.BufferedReader(io.BytesIO(self.data))

  def eat_nulls (self, data):
    i = 0
    while data[i] == 0x00:
      i = i+1
    return data[i:]

class HistoryPage (PagedData):
  def clean (self, data):
    # data.reverse( )
    # self.data = self.eat_nulls(data)
    #self.data.reverse( )
    self.data = data[:]
    # XXX: under some circumstances, zero is the correct value and
    # eat_nulls actually eats valid data.  This ugly hack restores two
    # nulls back ot the end.
    """
    self.data.append(0x00)
    self.data.append(0x00)
    self.data.append(0x00)
    self.data.append(0x00)
    self.data.append(0x00)
    """
    self.stream = io.BufferedReader(io.BytesIO(self.data))
  def decode (self, larger=False):
    records = [ ]
    skipped = [ ]
    for B in iter(lambda: bytearray(self.stream.read(2)), bytearray("")):
      if B == bytearray( [ 0x00, 0x00 ] ):
        if skipped:
          records.extend(skipped)
          skipped = [ ]
        break
      record = parse_record(self.stream, B, larger=larger, model=self.model)
      data = record.decode( )
      if record.datetime:
        rec = dict(timestamp=record.datetime.isoformat( ),
                   date=lib.epochize(record.datetime),
                   _type=str(record.__class__.__name__),
                   _body=lib.hexlify(record.body),
                   _head=lib.hexlify(record.head),
                   _date=lib.hexlify(record.date),
                   _description=str(record))
        if data is not None:
          rec.update(data)
          if skipped:
            rec.update(appended=skipped)
            skipped = [ ]
        records.append(rec)
      else:
        rec = dict(_type=str(record.__class__.__name__),
                   _body=lib.hexlify(record.body),
                   _head=lib.hexlify(record.head),
                   _date=lib.hexlify(record.date),
                   _description=str(record))
        data = record.decode( )
        if data is not None:
          rec.update(data=data)
        skipped.append(rec)
    records.reverse( )
    return records

if __name__ == '__main__':
  import doctest
  doctest.testmod( )

#####
# EOF
