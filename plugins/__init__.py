"""
    Inmanta clearwater plugins

    :copyright: 2017 Inmanta NV
    :contact: code@inmanta.com
"""

from inmanta.plugins import plugin, Context


@plugin
def instances(vnf: "clearwater::openstack::ClearwaterVNF") -> "number[]":
    """
        Return a list of instances
    """
    instances = max(min(vnf.instances, vnf.max_instances), vnf.min_instances)
    return list(range(1, instances + 1))
