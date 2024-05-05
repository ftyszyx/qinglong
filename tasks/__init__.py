import pkgutil as _pkgutil


class CheckIn:
    name = "Base"


__path__ = _pkgutil.extend_path(__path__, __name__)
for _, _modname, _ in _pkgutil.walk_packages(path=__path__, prefix=__name__ + "."):
    if _modname not in ["task.main", "task.configs"]:
        if _modname.startswith("task.utils"):
            continue
        __import__(_modname)
