import sys
import types
import defer

PY3 = False if sys.version_info < (3, 0) else True

def iterator(var):

    if isinstance(var, types.GeneratorType):
        return var

    if isinstance(var, list) or isinstance(var, tuple):
        return iter(var)

    return iter((var,))


def isstring(obj):
    try:
        return isinstance(obj, basestring)
    except NameError:
        return isinstance(obj, str)


class DeferredList(defer.Deferred):

    def __init__(self, deferredList):
        """Initialize a DeferredList"""
        self.result_list = [None] * len(deferredList)
        super(DeferredList, self).__init__()

        self.finished_count = 0

        for index, deferred in enumerate(deferredList):
            if isinstance(deferred, defer.Deferred):
                deferred.add_callbacks(
                    self._cb_deferred,
                    self._cb_deferred,
                    callback_args=(index,),
                    errback_args=(index,)
                )
            else:  # if request allready done
                self.finished_count += 1
                self.result_list[index] = deferred

        # check are deferreds or results was passed to __init__
        try:
            self.check_and_fire()
        except defer.AlreadyCalledDeferred:
            pass

    def _cb_deferred(self, result, index):
        """(internal) Callback for when one of my deferreds fires.
        """
        self.result_list[index] = result

        self.finished_count += 1
        self.check_and_fire()  # check is done and fire
        return result

    def check_and_fire(self):
        if self.finished_count == len(self.result_list):
            self.callback(self.result_list)

class RestrictedDict(dict):
    """
    Stores the properties of an object. It's a dictionary that's
    restricted to a tuple of allowed keys. Any attempt to set an invalid
    key raises an error.

    >>> p = RestrictedDict(('x','y'))
    >>> print p
    RestrictedDict(('x', 'y'), {})
    >>> p['x'] = 1
    >>> p['y'] = 'item'
    >>> print p
    RestrictedDict(('x', 'y'), {'y': 'item', 'x': 1})
    >>> p.update({'x': 2, 'y': 5})
    >>> print p
    RestrictedDict(('x', 'y'), {'y': 5, 'x': 2})
    >>> p['x']
    2
    >>> p['z'] = 0
    Traceback (most recent call last):
    ...
    KeyError: 'z is not allowed as key'
    >>> q = RestrictedDict(('x', 'y'), x=2, y=5)
    >>> p==q
    True
    >>> q = RestrictedDict(('x', 'y', 'z'), x=2, y=5)
    >>> p==q
    False
    >>> len(q)
    2
    >>> q.keys()
    ['y', 'x']
    >>> q._allowed_keys
    ('x', 'y', 'z')
    >>> p._allowed_keys = ('x', 'y', 'z')
    >>> p['z'] = 3
    >>> print p
    RestrictedDict(('x', 'y', 'z'), {'y': 5, 'x': 2, 'z': 3})

    """

    def __init__(self, allowed_keys, seq=(), **kwargs):
        """
        Initializes the class instance. The allowed_keys tuple is
        required, and it cannot be changed later.
        If seq and/or kwargs are provided, the values are added (just
        like a normal dictionary).
        """
        super(RestrictedDict, self).__init__()
        self._allowed_keys = tuple(allowed_keys)
        # normalize arguments to a (key, value) iterable
        if hasattr(seq, 'keys'):
            get = seq.__getitem__
            seq = ((k, get(k)) for k in seq.keys())
        if kwargs:
            from itertools import chain
            seq = chain(seq, kwargs.items())
        # scan the items keeping track of the keys' order
        for k, v in seq:
            self.__setitem__(k, v)

    def __setitem__(self, key, value):
        """Checks if the key is allowed before setting the value"""
        if key in self._allowed_keys:
            super(RestrictedDict, self).__setitem__(key, value)
        else:
            raise KeyError("%s is not allowed as key" % key)

    def update(self, e=None, **kwargs):
        """
        Equivalent to dict.update(), but it was needed to call
        RestrictedDict.__setitem__() instead of dict.__setitem__
        """
        try:
            for k in e:
                self.__setitem__(k, e[k])
        except AttributeError:
            for (k, v) in e:
                self.__setitem__(k, v)
        for k in kwargs:
            self.__setitem__(k, kwargs[k])

    def __eq__(self, other):
        """
        Two RestrictedDicts are equal when their dictionaries and allowed keys
        are all equal.
        """
        if other is None:
            return False
        try:
            allowedcmp = (self._allowed_keys == other._allowed_keys)
            if allowedcmp:
                dictcmp = super(RestrictedDict, self).__eq__(other)
            else:
                return False
        except AttributeError:
            #Other is not a RestrictedDict
            return False
        return bool(dictcmp)

    def __ne__(self, other):
        """x.__ne__(y) <==> not x.__eq__(y)"""
        return not self.__eq__(other)

    def __repr__(self):
        """Representation of the RestrictedDict"""
        return 'RestrictedDict(%s, %s)' % (self._allowed_keys.__repr__(),
                    super(RestrictedDict, self).__repr__())
