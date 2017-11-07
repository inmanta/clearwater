"""
    Inmanta clearwater plugins

    :copyright: 2017 Inmanta NV
    :contact: code@inmanta.com
"""

from inmanta.plugins import plugin, Context
from inmanta.execute.proxy import UnknownException

@plugin
def instances(vnf: "clearwater::openstack::ClearwaterVNF") -> "number[]":
    """
        Return a list of instances
    """
    x = 0
    try:
        x = vnf.instances
    except UnknownException as e:
        pass

    instances = max(min(x, vnf.max_instances), vnf.min_instances)
    return list(range(1, instances + 1))
