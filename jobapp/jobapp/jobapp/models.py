import logging
import abc
import time
import enum
import django.contrib.postgres.fields as postgres_fields
from django.db import transaction

from django.utils import timezone
from datetime import datetime, timedelta
from django.db import models
from typing import Type
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group


logger = logging.getLogger(__name__)


def now():
    return timezone.now()


class JobStatus(enum.IntEnum):
    PENDING = 1
    REQUEST_ACK = 2
    RUNNING = 3
    FAILED = 5
    ERRORED = 6
    SUCCESS = 7
    SUCCESS_WITH_WARNING = 8


class UiStatus(models.TextChoices):
    PENDING = 'Pending'
    REQUEST_ACK = 'Acknowledged'
    RUNNING = 'Running'
    FAILED = 'Failed'
    ERRORED = 'Errored'
    SUCCESS = 'Success'
    SUCCESS_WITH_WARNING = 'Success with warning(s)'


class Severity(enum.IntEnum):
    INFO = 1
    WARNING = 2
    MINOR = 3
    MAJOR = 4
    CRITICAL = 5
    FATAL = 6


ALL_STATUSES = tuple(JobStatus)
FINAL_STATUSES = (
    JobStatus.FAILED,
    JobStatus.ERRORED,
    JobStatus.SUCCESS,
    JobStatus.SUCCESS_WITH_WARNING
)
GOOD_STATUSES = (JobStatus.SUCCESS, JobStatus.SUCCESS_WITH_WARNING)
BAD_STATUSES = (JobStatus.FAILED, JobStatus.ERRORED)


class JobFailedError(Exception):
    pass


class AbstractDiagnostic(models.Model):
    
    class Meta:
        abstract = True

    severity = models.IntegerField(default=Severity.INFO.value)
    created_by = models.CharField(max_length=255)
    created_at =  models.DateTimeField(auto_now_add=True)
    updated_at =  models.DateTimeField(auto_now_add=True)
    details = postgres_fields.JSONField(null=True)
    stage = models.CharField(null=True, blank=True, max_length=50)


class AbstractJobNotifier(abc.ABCMeta):
    @abc.abstractmethod
    def notify(self, job):
        ...


class DbSaveNotifier(AbstractJobNotifier):
    """ Simply save the job to db """
    def notify(self, job):
        job.save()


def notify(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        try:
           result = f(self, *args, **kwargs)
           return result
        finally:
           self.notify()
    return wrapper


class AbstractJob(models.Model):

    DEFAULT_TTL_THRESHOLD = (3 * 24 * 60 * 60)

    class Meta:
        abstract = True

    _status = models.IntegerField(null=True)
    _ui_status = models.CharField(choices=UiStatus.choices, max_length=255)
    _data = postgres_fields.JSONField(null=True)
    type = models.IntegerField(null=True)
    stage = models.CharField(null=True, max_length=50)
    created_by = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_at =  models.DateTimeField(auto_now_add=True)
    updated_at =  models.DateTimeField(auto_now_add=True)
    ttl = models.IntegerField(default=DEFAULT_TTL_THRESHOLD) # 3 days

    def __init__(self, *args, notifiers=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not notifiers:
            self._notifiers = (DbSaveNotifier(),)

    @property
    def status(self):
        return self._status

    @property
    def ui_status(self):
        return self._ui_status

    @notify
    def acknowledge(self):
        self.update_status(status=JobStatus.REQUEST_ACK)

    @notify
    def running(self):
        self.update_status(status=JobStatus.RUNNING)

    @notify
    def fail(self, raise_error=True, reason=''):
        self.update_status(status=JobStatus.FAILED)
        if raise_error:
            raise JobFailedError(f'Job failed, reason={reason}')

    @notify
    def success(self, notify):
        self.update_status(status=JobStatus.SUCCESS)

    @notify
    def error(self):
        self.update_status(status=JobStatus.ERRORED)

    @notify
    def success_with_warning(self):
        self.update_status(status=JobStatus.SUCCESS_WITH_WARNING)

    @notify
    def start_stage(self, stage):
        self.stage = stage

    @notify
    def end_stage(self, stage):
        pass

    def update_status(self, status: JobStatus, ui_status: UiStatus=None):
        assert status or ui_stauts
        self._status = status.value
        if ui_status is not None:
            self._ui_status = ui_status.value
        else:
            mapped_status = getattr(UiStatus, status.name, None)
            if mapped_status is not None:
                self.update_ui_status(mapped_status)
        self.touch()

    def update_ui_status(self, status: UiStatus):
        self._ui_status = ui_status
        self.touch()

    def touch(self):
        self.updated_at = now()

    @property
    def notifiers(self):
        return self._notifiers

    def notify(self):
        # notifiers are classes which implemets 'notify' method.
        # and accepts job as first argument
        for notifier in self.notifiers:
            notifier.notify(self)

    def on_success(self):
        pass

    def on_failure(self):
        pass

    def finalize(self):
        pass

    def act(self):
        pass

    def act_resume(self):
        pass

    @property
    def has_expired(self):
        return not (now() <  self.created_at + timedelta(seconds=self.ttl))

    @property
    def is_stale(self):
        return self.has_expired


class JobProgressMixin(models.Model):
    class Meta:
        abstract = True
    _total_units = models.IntegerField(db_column='progress_total_units', default=0)
    _done_units = models.IntegerField(default=0, db_column='progress_done_units', default=0)
    _progress_percent = models.IntegerField(null=True)
    progress_unit = models.CharField(max_length=50, blank=True)
    progress_unit_plural = models.CharField(max_length=50, blank=True)


    def total_units(self):
        return self._total_units

    def done_units(self):
        return self._done_units

    def add_units(self, units):
        _total_units += units

    def report_progress(self, done_units:int=1, notify=True):
        self._done_units += done_units
        if notify:
            self.notify()

    @property
    def remaining_units(self):
        return self.total_units - self.done_units

    @property
    def progress_percent(self):
        if self._progress_percent is not None:
            return _progress_percent
        return ((self.done_units * 100) / self.total_units)
 
    @progress_percent.setter
    def progress_percent(self, value: int):
        assert 0 <= value <= 100
        self._progress_percent = value


class JobRunnerMixin:
    @classmethod
    def run(cls, job: Type[AbstractJob]):
        job.acknowledge()
        try:
            job.running()
            job.act()
        except JobFailedError as e:
            pass
        except Exception as e:
            logger.exception(e)
            job.error()
        else:
            if job.status not in FINAL_STATUSES:
                job.success()
        finally:
            cls.process_post_job_hooks(job)

    @classmethod
    def process_post_job_hooks(cls, job: Type[AbstractJob]):
        try:
            if job.status in SUCCESS_STATUSES:
                job.on_success()
            if job.status in FAILED_STATUSES:
                job.on_failure()
        except Exception as e:
            logger.exception(e)
        finally:
            self.finalize()

