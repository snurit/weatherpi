from abc import ABCMeta, abstractmethod, abstractproperty


class AbstractSensor(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def sensor(self):
        pass

    @abstractproperty
    def values(self):
        pass

    @abstractmethod
    def __init__(self):
        """Create and initialize sensor"""
        raise NotImplementedError

    @abstractmethod
    def initialize(self):
        """Initialize sensor. Called by __init__"""
        raise NotImplementedError

    @abstractmethod
    def get_values(self):
        """Return the values read from sensors as a tuple"""
        raise NotImplementedError

    @abstractmethod
    def get_instance(self):
        raise NotImplementedError

    @abstractmethod
    def __str__(self):
        raise NotImplementedError
