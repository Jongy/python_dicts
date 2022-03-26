import demos.load_global_cache
from demos.load_global_cache import use_globals
from dicts import dict_version
import dis

dis.dis(use_globals)

dict_version(demos.load_global_cache.__dict__)
%timeit use_globals(False)
dict_version(demos.load_global_cache.__dict__)

%timeit use_globals(True)
dict_version(demos.load_global_cache.__dict__)

dict_version(demos.load_global_cache.__dict__)
%timeit use_globals(False)
dict_version(demos.load_global_cache.__dict__)
