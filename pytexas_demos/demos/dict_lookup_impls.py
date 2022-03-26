from dicts import print_dict

d = {str(i): 1 for i in range(100)}

print_dict(d)  # lookdict_unicode_nodummy

def dict_loop(d):
    for i in range(10_000):
        d["1"]

%timeit dict_loop(d)

# make a dummy entry
del d["2"]

print_dict(d)  # lookdict_unicode

%timeit dict_loop(d)  # no major difference

# insert a non-str key
d[1] = 1

print_dict(d)  # lookdict

%timeit dict_loop(d)  # 20% slower
