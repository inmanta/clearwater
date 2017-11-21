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


@plugin
def get_param(ctx: Context, name: "string") -> "string":
    """
        Get a parameter from the SO
    """
    env = config.Config.get("config", "environment", None)

    def get():
        return ctx.get_client().get_param(tid=env, id=name)

    result = ctx.run_sync(get)

    if result.code == 200:
        return result.result["parameter"]["value"]
    return None


@plugin
def set_param(ctx: Context, name: "string", value: "string", recompile: "bool"=False) -> "string":
    """
        Set a parameter on the SO
    """
    env = config.Config.get("config", "environment", None)

    def setp():
        return ctx.get_client().set_param(tid=env, id=name, value=value, source="plugin", metadata={"module": "clearwater"},
                                          recompile=recompile)

    result = ctx.run_sync(setp)

    if result.code != 200:
        raise Exception(result.result)


@plugin
def select_repo(ctx: Context, service: "clearwater::ClearwaterService", versions: "dict") -> "string":
    """
        Select the current repo to use for this component
    """
    if service.upgrade_version not in versions:
        raise Exception("Version %s for vnf %s-%s does not exist." % (service.upgrade_version, service.instance_name))
    return versions[service.upgrade_version]


def get_service(services, vnf_name, vnf_instance):
    for svc in services:
        if svc.vnf_name == vnf_name and svc.vnf_instance == vnf_instance:
            return svc
    return None


@plugin
def next_upgrade(ctx: Context, service: "clearwater::ClearWater", upgrade_order: "string[]",
                 current: "clearwater::ClearwaterService"=None) -> "clearwater::ClearwaterService":
    upgrade_order = list(upgrade_order) # unwrap
    if current is None:
        return get_service(service.services, upgrade_order[0], 1)

    # check next index first
    svc = get_service(service.services, current.vnf_name, current.vnf_instance + 1)
    if svc is not None:
        return svc

    pos = upgrade_order.index(current.vnf_name)
    if pos + 1 == len(upgrade_order):
        # we reached the end
        return None

    return get_service(service.services, upgrade_order[pos + 1], 1)


@plugin
def select_service_version(ctx: Context, cw: "clearwater::ClearWater") -> "string":
    """
        Select the current version for clearwater
    """
    param_name = cw.name + "_version"
    current_version = get_param(ctx, param_name)
    if current_version is None:
        set_param(ctx, param_name, cw.upgrade_version)
        return cw.upgrade_version

    return current_version


@plugin
def get_current_version(ctx: Context, component: "clearwater::ClearwaterService") -> "string":
    """
        Get the current version of this component from the orchestrator. When the version is not yet defined, use the current
        version of the service.
    """
    param_name = component.name + "_current_version"
    current_version = get_param(ctx, param_name)
    if current_version is None:
        set_param(ctx, param_name, component.clearwater.version)
        return component.clearwater.version

    return current_version


@plugin
def get_upgrade_version(ctx: Context, component: "clearwater::ClearwaterService") -> "string":
    """
        Get the upgrade version of this component from the orchestrator. When the version is not yet defined, use the current
        version of the service.
    """
    param_name = component.name + "_upgrade_version"
    current_version = get_param(ctx, param_name)
    if current_version is None:
        set_param(ctx, param_name, component.clearwater.version)
        return component.clearwater.version

    return current_version


@plugin
def set_upgrade(ctx: Context, component: "any", service: "clearwater::ClearWater"):
    """
        Set the given component to the upgrade version of the service.
    """
    if component is not None:
        param_name = component.name + "_upgrade_version"
        set_param(ctx, param_name, component.clearwater.upgrade_version, True)
    else:
        param_name = service.name + "_version"
        set_param(ctx, param_name, service.upgrade_version)


@plugin
def finish_upgrade(ctx: Context, component: "clearwater::ClearwaterService"):
    """
        Finish the upgrade by setting the current version to the upgrade version.
    """
    param_name = component.name + "_current_version"
    set_param(ctx, param_name, component.upgrade_version)