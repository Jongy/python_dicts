import sys
import platform
import textwrap
import ctypes
from ctypes import c_void_p, c_char, c_uint64, POINTER, py_object, Structure

Py_ssize_t = ctypes.c_int64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_int32
Py_hash_t = Py_ssize_t


class PyDictKeyEntry(Structure):
    _fields_ = [
        ("me_hash", Py_hash_t),
        ("me_key", py_object),
        ("me_value", py_object),
    ]


class _dictkeysobject(Structure):
    _fields_ = [
        ("dk_refcnt", Py_ssize_t),
        ("dk_size", Py_ssize_t),
        ("dk_lookup", c_void_p),
        ("dk_usable", Py_ssize_t),
        ("dk_nentries", Py_ssize_t),
        ("dk_indices", c_char * 0),
        # "PyDictKeyEntry dk_entries[dk_nentries + dk_usable]" follows
    ]


# py_object is PyObject*, this is the struct itself
class PyObject(Structure):
    _fields_ = [
        ("ob_refcnt", Py_ssize_t),
        ("ob_type", py_object),
    ]


class PyDictObject(Structure):
    _fields_ = [
        ("ob_base", PyObject),
        ("ma_used", Py_ssize_t),
        ("ma_version_tag", c_uint64),
        ("ma_keys", POINTER(_dictkeysobject)),
        ("ma_values", POINTER(py_object)),
        # dk_indices follows
        # and then dk_entries
    ]


def DK_SIZE(dk):
    assert isinstance(dk, _dictkeysobject)
    return dk.dk_size


if ctypes.sizeof(ctypes.c_void_p) > 4:
    def DK_IXSIZE(dk):
        if DK_SIZE(dk) <= 0xff:
            return 1
        elif DK_SIZE(dk) <= 0xffff:
            return 2
        elif DK_SIZE(dk) <= 0xffffffff:
            return 4
        else:
            return 8
else:
    def DK_IXSIZE(dk):
        if DK_SIZE(dk) <= 0xff:
            return 1
        elif DK_SIZE(dk) <= 0xffff:
            return 2
        else:
            return 4


def DK_ENTRIES(dk):
    return (PyDictKeyEntry * (dk.dk_nentries + dk.dk_usable)).from_address(ctypes.addressof(dk) + _dictkeysobject.dk_indices.offset + DK_SIZE(dk) * DK_IXSIZE(dk))



def find_lookdicts():
    # lookdict_split - get the dk_lookup from a dummy instance.
    class X: pass
    x = X()
    lookdict_split = PyDictObject.from_address(id(x.__dict__)).ma_keys.contents.dk_lookup

    # lookdict_unicode_nodummy - get the dk_lookup from a dict containing strings and no dummy entries
    d = {"a": 1}
    lookdict_unicode_nodummy = PyDictObject.from_address(id(d)).ma_keys.contents.dk_lookup

    # lookdict_unicode - get the dk_lookup from a dict containing strings and dummy entries (deleted, in this case)
    del d["a"]
    lookdict_unicode = PyDictObject.from_address(id(d)).ma_keys.contents.dk_lookup

    # lookdict - get the dk_lookup from a dict containing non-str keys
    d[1] = 1
    lookdict = PyDictObject.from_address(id(d)).ma_keys.contents.dk_lookup

    # if these are not different, then we didn't manage to trick cpython into selecting
    # the different lookdict functions :)
    assert lookdict_split != lookdict_unicode_nodummy != lookdict_unicode != lookdict

    return {
        lookdict_split: "lookdict_split",
        lookdict_unicode: "lookdict_unicode",
        lookdict_unicode_nodummy: "lookdict_unicode_nodummy",
        lookdict: "lookdict",
    }


lookdicts = find_lookdicts()


def _py_object_is_null(obj, attr):
    # funny way to check if a py_object field is NULL. I couldn't find any other way
    # to do it with a quick search, so meh :/
    try:
        getattr(obj, attr)
        return False
    except ValueError as e:
        if e.args[0] == "PyObject is NULL":
            return True
        raise


def _is_split(d: PyDictObject):
    dk = d.ma_keys.contents
    if lookdicts[dk.dk_lookup] == "lookdict_split":
        assert bool(d.ma_values), "ma_values is NULL for split!"
        return True
    else:
        assert not bool(d.ma_values), "ma_values is not NULL for non-split!"
        return False


def get_dict_obj(x: dict):
    assert type(x) is dict

    return PyDictObject.from_address(id(x))


# impl of dictiter_iternextitem
def iter_dict(x: dict, indent: int = 0):
    d = get_dict_obj(x)
    dk = d.ma_keys.contents

    for i in range(d.ma_used):
        if _is_split(d):
            assert i < d.ma_used, f"{i} < {d.ma_used}"
            key = DK_ENTRIES(dk)[i].me_key
            value = d.ma_values[i]
        else:
            n = dk.dk_nentries
            entries = DK_ENTRIES(dk)
            while i < n and _py_object_is_null(entries[i], "me_value"):
                print(textwrap.indent(f"{i:4} : unused / dummy", " " * indent))
                i += 1
            assert i < n, f"{i} < {n}"
            key = entries[i].me_key
            value = entries[i].me_value

        print(textwrap.indent(f"{i:4} : {key!r} : {value!r}", " " * indent))


def print_dict(x: dict):
    d = get_dict_obj(x)
    dk = d.ma_keys.contents
    print("lookdict function:", lookdicts[dk.dk_lookup])
    print("dict size (bytes):", sys.getsizeof(x))
    print()
    print("dict used:", d.ma_used)
    print("dict version_tag:", d.ma_version_tag)
    print("dict values:", hex(ctypes.cast(d.ma_values, ctypes.c_void_p).value or 0))
    print()
    print("keys size:", dk.dk_size)
    print("keys nentries", dk.dk_nentries)
    print("keys usable:", dk.dk_usable)
    print("keys refcount (used by this many dicts):", dk.dk_refcnt)


def print_dict_all(x: dict):
    print_dict(x)
    print()
    print("entries:")
    iter_dict(x, indent=4)


def dict_version(x: dict):
    return get_dict_obj(x).ma_version_tag


# checked on those versions only, others may vary.
assert sys.version_info[:2] in ((3, 8), (3, 9), (3, 10))
# and on Linux
assert sys.platform == "linux"
# x86_64
assert platform.machine() == "x86_64"
