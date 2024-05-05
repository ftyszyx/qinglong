import pkgutil as _pkgutil


class TaskBase:
    name = "Base"


__path__ = _pkgutil.extend_path(__path__, __name__)
for _, _modname, _ in _pkgutil.walk_packages(path=__path__, prefix=__name__ + "."):
    if _modname not in ["tasks.main", "tasks.configs"]:
        if _modname.startswith("tasks.utils"):
            continue
        __import__(_modname)
