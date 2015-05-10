"""
Item
"""
from pomp.core.utils import RestrictedDict

class Field(object):
    """It just represents a field in a Item to be extracted"""
    creation_counter = 0
    name = None

    def __init__(self):
        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

    def __get__(self, instance, owner):
        if instance is None:
            # Item class being used rather than a item object
            return self

        # Get value from item instance if available
        return instance._data.get(self.name)

    def __set__(self, instance, value):
        instance._data[self.name] = value

class ItemMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        super_new = super(ItemMetaclass, mcs).__new__

        # Discover any item fields
        field_names = {}
        for attr_name, attr_value in attrs.items():
            if not isinstance(attr_value, Field):
                continue
            attr_value.name = attr_name
            field_names[attr_name] = attr_value

        attrs['_fields_ordered'] = tuple(i[1] for i in sorted(
            (v.creation_counter, v.name) for v in field_names.values()))

        # Create the new_class
        new_class = super_new(mcs, name, bases, attrs)

        return new_class

class Item(metaclass=ItemMetaclass):

    __slots__ = ('_data')

    def __init__(self, *args, **kwargs):
        if args:
            # Combine positional arguments with named arguments.
            # We only want named arguments.
            field = iter(self._fields_ordered)
            for value in args:
                name = next(field)
                if name in kwargs:
                    raise TypeError(
                        "Multiple values for keyword argument '" + name + "'")
                kwargs[name] = value
        self._data = RestrictedDict(allowed_keys=self._fields_ordered)

        #self._data = {}

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            if name in self._data:
                self._data[name] = value

        super(Item, self).__setattr__(name, value)


    def __iter__(self):
        return iter(self._fields_ordered)

    def __getitem__(self, name):
        try:
            if name in self._fields_ordered:
                return getattr(self, name)
        except AttributeError:
            pass
        raise KeyError(name)

    def __setitem__(self, name, value):
        if name not in self._fields_ordered:
            raise KeyError(name)
        return setattr(self, name, value)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                ','.join('{}={}'.format(k, v) for k, v in self._data.items()))
