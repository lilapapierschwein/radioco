from pytz.exceptions import NonExistentTimeError
from recurrence import Recurrence
import datetime

from django.utils import timezone


"""
Monkey patch to deal with various date/time issues in origin Recurrence
implementation.
 """


def init(self, *args, **kwargs):
    self.___init__(*args, **kwargs)

    # hacky workaround, remove after upstream bug is solved
    # https://github.com/django-recurrence/django-recurrence/issues/94
    def fix_date(rdate):
        return datetime.datetime.combine(
            rdate,
            datetime.time(self.dtstart.hour,
                          self.dtstart.minute,
                          self.dtstart.second,
                          self.dtstart.microsecond,
                          self.dtstart.tzinfo))
    self.rdates = [fix_date(dt) for dt in self.rdates]
    self.exdates = [fix_date(dt) for dt in self.exdates]

    if self.dtstart and timezone.is_aware(self.dtstart):
        self.dtstart = timezone.make_naive(self.dtstart)


def before(self, dt, **kwargs):
    if timezone.is_aware(dt):
        dt = timezone.make_naive(dt)

    _dt = self._before(dt, **kwargs)
    if _dt:
        return timezone.make_aware(_dt)
    return None


def after(self, dt, **kwargs):
    if timezone.is_aware(dt):
        dt = timezone.make_naive(dt)

    _dt = self._after(dt, **kwargs)
    if _dt:
        return timezone.make_aware(_dt)
    return None


def between(self, after, before, **kwargs):
    if timezone.is_aware(after):
        after = timezone.make_naive(after)

    if timezone.is_aware(before):
        before = timezone.make_naive(before)

    for dt in self._between(after, before, **kwargs):
        try:
            yield timezone.make_aware(dt)
        except NonExistentTimeError:
            pass


def patch():
    Recurrence.___init__ = Recurrence.__init__
    Recurrence.__init__ = init
    Recurrence._before = Recurrence.before
    Recurrence.before = before
    Recurrence._after = Recurrence.after
    Recurrence.after = after
    Recurrence._between = Recurrence.between
    Recurrence.between = between
