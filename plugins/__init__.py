"""
    Inmanta clearwater plugins

    :copyright: 2017 Inmanta NV
    :contact: code@inmanta.com
"""

from inmanta.plugins import plugin, Context
from inmanta.execute.proxy import UnknownException
from inmanta import config


def get_vnf_instances(ctx: Context, vnf_name):
    env = config.Config.get("config", "environment", None)

    def get_instances():
        return ctx.get_client().list_params(env, {"module": "state"})

    result = ctx.run_sync(get_instances)
    vnfs = []
    params = {}
    if result.code != 200:
        return None
    else:
        for p in result.result["parameters"]:
            if p["name"].startswith("fsm_" + vnf_name):
                vnfs.append(int(p["name"].split("_")[-1]))
                params[p["name"]] = p

    return vnfs, params


def set_state(ctx, fsm_name, value, metadata):
    env = config.Config.get("config", "environment", None)

    def set_state():
        return ctx.get_client().set_param(tid=env, id=fsm_name, value=value, source="plugin", metadata=metadata)

    result = ctx.run_sync(set_state)


NOT_SET_STATES = ["decommission", "remove"]


@plugin
def instances(ctx: Context, vnf: "clearwater::openstack::ClearwaterVNF") -> "number[]":
    """
        Return a list of instances
    """
    fsm_instances, params = get_vnf_instances(ctx, vnf.name)
    x = 0
    try:
        x = vnf.instances
    except UnknownException as e:
        pass

    instances = max(min(x, vnf.max_instances), vnf.min_instances)
    instance_list = []
    for i in range(1, instances + 1):
        if i in fsm_instances:
            fsm_instances.remove(i)
        instance_list.append(i)

    for i in fsm_instances:
        name = "fsm_%s_%d" % (vnf.name, i)
        # transfer its state machine
        if params[name]["value"] not in NOT_SET_STATES:
            set_state(ctx, name, "decommission", params[name]["metadata"])

        instance_list.append(i)

    return instance_list
